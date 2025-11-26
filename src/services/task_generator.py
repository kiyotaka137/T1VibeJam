# src/services/task_generator.py
import re
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from src.prompts.task_prompts import TASK_GEN_SYSTEM_PROMPT, TASK_GEN_USER_TEMPLATE


# --- Модели данных ---
class TestCase(BaseModel):
    input: str = Field(description="JSON строка со списком аргументов.")
    output: str = Field(description="JSON строка с результатом.")


class TaskStructure(BaseModel):
    title: str = Field(description="Заголовок задачи")
    description: str = Field(description="Условие задачи")
    input_description: str = Field(description="Описание входа")
    output_description: str = Field(description="Описание выхода")
    constraints: List[str] = Field(description="Ограничения")
    function_name: str = Field(description="Имя функции (snake_case)")
    initial_code_python: str = Field(description="Шаблон Python")
    initial_code_cpp: str = Field(description="Шаблон C++")
    test_cases: List[TestCase] = Field(description="Тестовые данные")


# --- Генератор ---
class TaskGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url="http://45.145.191.148:4000/v1",  # IP-адрес
            api_key="sk-x8YPQ4vYbpEJHQlc5faICA",
            # МЕНЯЕМ МОДЕЛЬ НА КОДЕРСКУЮ (она быстрее для кода)
            model="qwen3-coder-30b-a3b-instruct-fp8",
            temperature=0.6,
            max_tokens=2000,
            request_timeout=120,
        )
        self.parser = JsonOutputParser(pydantic_object=TaskStructure)

    def _clean_response(self, text: str) -> str:
        # Даже если think отключен, на всякий случай оставим очистку
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        match = re.search(r'```json\s*(.*?)\s*```', text, flags=re.DOTALL)
        if match:
            return match.group(1)
        json_start = text.find('{')
        json_end = text.rfind('}')
        if json_start != -1 and json_end != -1:
            return text[json_start: json_end + 1]
        return text

    async def generate_tasks(self, grade: str, topic: str):
        prompt = ChatPromptTemplate.from_messages([
            ("system", TASK_GEN_SYSTEM_PROMPT),
            ("user", TASK_GEN_USER_TEMPLATE),
        ])

        formatted_prompt = await prompt.ainvoke({
            "grade": grade,
            "topic": topic,
            "format_instructions": self.parser.get_format_instructions()
        })

        try:
            print("   >>> Отправка запроса к LLM (CODER модель)...")
            response = await self.llm.ainvoke(formatted_prompt)
            cleaned_json = self._clean_response(response.content)

            task_data = self.parser.parse(cleaned_json)
            return {"tasks": [task_data]}

        except Exception as e:
            print(f"⚠️ Ошибка генерации: {e}")
            return {"error": str(e), "tasks": []}