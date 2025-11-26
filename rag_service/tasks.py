# rag_service/tasks.py
import re
import uuid
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .config import settings
from .db_storage import LevelType, save_generated_task_to_db, TaskDBModel, get_full_task_by_id
from .vector_store import save_task_to_vectorstore
# Импортируем все промпты, включая новый ADAPTIVE
from .prompts_const import (
    TASK_GEN_SYSTEM_PROMPT, TASK_GEN_USER_TEMPLATE,
    TASK_REFINE_SYSTEM_PROMPT, TASK_REFINE_USER_TEMPLATE,
    TASK_ADAPTIVE_SYSTEM_PROMPT, TASK_ADAPTIVE_USER_TEMPLATE
)


# --- Модели генератора (Pydantic) ---
class GenTestCase(BaseModel):
    input: str
    output: str


class TaskStructure(BaseModel):
    title: str = Field(description="Заголовок")
    description: str = Field(description="Условие")
    input_description: str = Field(description="Вход")
    output_description: str = Field(description="Выход")
    constraints: List[str] = Field(description="Ограничения")
    function_name: str = Field(description="Snake case name")
    initial_code_python: str = Field(description="Python template")
    initial_code_cpp: str = Field(description="C++ template")
    test_cases: List[GenTestCase] = Field(description="Tests")


# --- Класс Генератора ---
class TaskGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.BASE_URL,
            api_key=settings.API_KEY,
            model=settings.CODER_MODEL,
            temperature=0.6,
            max_tokens=2000,
        )
        self.parser = JsonOutputParser(pydantic_object=TaskStructure)

    def _clean(self, text: str) -> str:
        """Очистка ответа от тегов <think> и markdown блоков"""
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        match = re.search(r'```json\s*(.*?)\s*```', text, flags=re.DOTALL)
        if match: return match.group(1)
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1: return text[start: end + 1]
        return text

    async def _run_llm(self, formatted_prompt) -> Optional[TaskStructure]:
        try:
            print(f"   >>> LLM Request ({settings.CODER_MODEL})...")
            resp = await self.llm.ainvoke(formatted_prompt)
            data = self.parser.parse(self._clean(resp.content))
            return TaskStructure(**data)
        except Exception as e:
            print(f"LLM Error: {e}")
            return None

    # 1. Генерация по теме (Standard)
    async def generate(self, grade: str, topic: str) -> Optional[TaskStructure]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", TASK_GEN_SYSTEM_PROMPT),
            ("user", TASK_GEN_USER_TEMPLATE),
        ])
        formatted = await prompt.ainvoke({
            "grade": grade, "topic": topic,
            "format_instructions": self.parser.get_format_instructions()
        })
        return await self._run_llm(formatted)

    # 2. Улучшение текста HR (Refine)
    async def refine(self, grade: str, raw_text: str) -> Optional[TaskStructure]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", TASK_REFINE_SYSTEM_PROMPT),
            ("user", TASK_REFINE_USER_TEMPLATE),
        ])
        formatted = await prompt.ainvoke({
            "grade": grade, "raw_text": raw_text,
            "format_instructions": self.parser.get_format_instructions()
        })
        return await self._run_llm(formatted)

    # 3. Адаптивная генерация (Adaptive)
    async def generate_adaptive(
            self,
            prev_task: dict,
            user_code: str,
            time_minutes: float,
            new_level: str
    ) -> Optional[TaskStructure]:

        prompt = ChatPromptTemplate.from_messages([
            ("system", TASK_ADAPTIVE_SYSTEM_PROMPT),
            ("user", TASK_ADAPTIVE_USER_TEMPLATE),
        ])

        formatted = await prompt.ainvoke({
            "prev_title": prev_task.get("title", "Unknown"),
            "prev_level": prev_task.get("level", "unknown"),
            "time_spent": f"{time_minutes:.1f}",
            "user_code": user_code,
            "new_level": new_level,
            "format_instructions": self.parser.get_format_instructions()
        })

        return await self._run_llm(formatted)


generator = TaskGenerator()


# --- Вспомогательная логика ---

def calculate_next_level(current_level: LevelType, minutes: float) -> LevelType:
    """Определяет следующий уровень сложности на основе времени решения"""
    levels = [LevelType.JUNIOR, LevelType.MIDDLE, LevelType.SENIOR]

    try:
        idx = levels.index(current_level)
    except ValueError:
        return LevelType.JUNIOR  # Fallback

    if minutes < 15:
        # Быстро -> Повышаем (если возможно)
        new_idx = min(idx + 1, len(levels) - 1)
    elif minutes > 35:
        # Долго -> Понижаем (если возможно)
        new_idx = max(idx - 1, 0)
    else:
        # Нормально -> Оставляем тот же
        new_idx = idx

    return levels[new_idx]


# --- Workflows (Бизнес-логика) ---

async def generate_task_workflow(level: LevelType, topic: str) -> tuple[Optional[str], Optional[TaskStructure]]:
    """Генерация обычной задачи"""
    task_data = await generator.generate(level.value, topic)
    if not task_data: return None, None

    task_id = str(uuid.uuid4())
    await _save_task_full(task_id, task_data, level, source="generated", topic=topic)

    return task_id, task_data


async def create_custom_task_workflow(level: LevelType, raw_text: str) -> tuple[Optional[str], Optional[TaskStructure]]:
    """Создание задачи из текста HR"""
    task_data = await generator.refine(level.value, raw_text)
    if not task_data: return None, None

    task_id = str(uuid.uuid4())
    await _save_task_full(task_id, task_data, level, source="custom_hr", topic="Custom")

    return task_id, task_data


async def generate_next_task_workflow(
        prev_task_id: str,
        time_spent_sec: int,
        user_code: str
) -> tuple[Optional[str], Optional[TaskStructure], Optional[str]]:
    """
    Адаптивная генерация следующей задачи.
    Возвращает: (new_task_id, task_data, new_level_str)
    """
    # 1. Получаем данные о прошлой задаче
    prev_task_data = await get_full_task_by_id(prev_task_id)
    if not prev_task_data:
        print(f"⚠️ Previous task {prev_task_id} not found in DB")
        return None, None, None

    # Парсим уровень прошлой задачи
    try:
        current_level = LevelType(prev_task_data.get("level", "junior"))
    except:
        current_level = LevelType.JUNIOR

    # 2. Вычисляем новый уровень
    minutes = time_spent_sec / 60.0
    new_level = calculate_next_level(current_level, minutes)
    print(f"   >>> Adaptive Logic: {minutes:.1f} min. Level: {current_level.value} -> {new_level.value}")

    # 3. Генерируем новую задачу
    task_data = await generator.generate_adaptive(
        prev_task=prev_task_data,
        user_code=user_code,
        time_minutes=minutes,
        new_level=new_level.value
    )

    if not task_data: return None, None, None

    # 4. Сохраняем
    task_id = str(uuid.uuid4())
    # Тему берем от родителя, чтобы контекст сохранялся в метаданных вектора
    topic = prev_task_data.get("title", "Adaptive")

    await _save_task_full(task_id, task_data, new_level, source="ai_adaptive", topic=topic)

    return task_id, task_data, new_level.value


async def _save_task_full(
        task_id: str,
        task_data: TaskStructure,
        level: LevelType,
        source: str,
        topic: str
):
    """Вспомогательная функция сохранения в SQL и Vector"""
    # 1. SQL
    db_model = TaskDBModel(
        task_id=task_id,
        title=task_data.title,
        description=task_data.description,
        input_description=task_data.input_description,
        output_description=task_data.output_description,
        constraints=task_data.constraints,
        function_name=task_data.function_name,
        initial_code_python=task_data.initial_code_python,
        initial_code_cpp=task_data.initial_code_cpp,
        test_cases=task_data.test_cases
    )
    await save_generated_task_to_db(level, db_model)

    # 2. Vector Store
    try:
        search_text = f"{task_data.title}\n{task_data.description}"
        save_task_to_vectorstore(
            text=search_text,
            source=source,
            level=level,
            topic=topic,
            task_id=task_id,
            extra_meta={"title": task_data.title}
        )
    except Exception as e:
        print(f"Vector save warning: {e}")