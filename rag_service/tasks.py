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
from .db_storage import LevelType, save_generated_task_to_db, TaskDBModel
from .vector_store import save_task_to_vectorstore
# Импортируем новые промпты
from .prompts_const import (
    TASK_GEN_SYSTEM_PROMPT, TASK_GEN_USER_TEMPLATE,
    TASK_REFINE_SYSTEM_PROMPT, TASK_REFINE_USER_TEMPLATE
)

# --- Модели генератора ---
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
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        match = re.search(r'```json\s*(.*?)\s*```', text, flags=re.DOTALL)
        if match: return match.group(1)
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1: return text[start: end + 1]
        return text

    async def generate(self, grade: str, topic: str) -> Optional[TaskStructure]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", TASK_GEN_SYSTEM_PROMPT),
            ("user", TASK_GEN_USER_TEMPLATE),
        ])
        formatted = await prompt.ainvoke({
            "grade": grade, "topic": topic,
            "format_instructions": self.parser.get_format_instructions()
        })
        try:
            print(f"   >>> Generating task ({settings.CODER_MODEL})...")
            resp = await self.llm.ainvoke(formatted)
            data = self.parser.parse(self._clean(resp.content))
            return TaskStructure(**data)
        except Exception as e:
            print(f"Gen Error: {e}")
            return None

class TaskGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.BASE_URL,
            api_key=settings.API_KEY,
            model=settings.CODER_MODEL,
            temperature=0.6, # Чуть меньше креатива, больше точности
            max_tokens=2000,
        )
        self.parser = JsonOutputParser(pydantic_object=TaskStructure)

    def _clean(self, text: str) -> str:
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        match = re.search(r'```json\s*(.*?)\s*```', text, flags=re.DOTALL)
        if match: return match.group(1)
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1: return text[start: end + 1]
        return text

    # Старый метод (генерация с нуля)
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

    # НОВЫЙ МЕТОД (доработка сырого текста)
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

    async def _run_llm(self, formatted_prompt) -> Optional[TaskStructure]:
        try:
            print(f"   >>> LLM Request ({settings.CODER_MODEL})...")
            resp = await self.llm.ainvoke(formatted_prompt)
            data = self.parser.parse(self._clean(resp.content))
            return TaskStructure(**data)
        except Exception as e:
            print(f"LLM Error: {e}")
            return None

generator = TaskGenerator()

async def generate_task_workflow(level: LevelType, topic: str) -> tuple[Optional[str], Optional[TaskStructure]]:
    # 1. Генерация
    task_data = await generator.generate(level.value, topic)
    if not task_data: return None, None

    # 2. Создаем ID
    task_id = str(uuid.uuid4())

    # 3. Сохраняем в SQL (Полная инфа)
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

    # 4. Сохраняем в Vector Store (Индекс для поиска)
    try:
        search_text = f"{task_data.title}\n{task_data.description}"
        save_task_to_vectorstore(
            text=search_text,
            source="generated",
            level=level,
            topic=topic,
            task_id=task_id, # Тот же ID
            extra_meta={"title": task_data.title}
        )
    except Exception as e:
        print(f"Vector save warning: {e}")

    return task_id, task_data

# НОВАЯ ФУНКЦИЯ WORKFLOW
async def create_custom_task_workflow(level: LevelType, raw_text: str) -> tuple[Optional[str], Optional[TaskStructure]]:
    """
    1. Улучшает сырой текст через LLM.
    2. Сохраняет в SQL и Vector.
    """
    # 1. Refine (улучшение)
    task_data = await generator.refine(level.value, raw_text)
    if not task_data: return None, None

    # 2. ID
    task_id = str(uuid.uuid4())

    # 3. SQL
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

    # 4. Vector
    try:
        search_text = f"{task_data.title}\n{task_data.description}"
        save_task_to_vectorstore(
            text=search_text,
            source="custom_hr", # Пометим, что это от HR
            level=level,
            topic="Custom",     # Тему можно вытащить из LLM, но пока заглушка
            task_id=task_id,
            extra_meta={"title": task_data.title}
        )
    except Exception as e:
        print(f"Vector save warning: {e}")

    return task_id, task_data