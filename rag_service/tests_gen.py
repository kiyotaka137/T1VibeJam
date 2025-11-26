# rag_service/tests_gen.py
from typing import List
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate

from .llm_client import llm
from .vector_store import LevelType
from .db_tests import TestCaseModel, save_task_tests


class TestCase(BaseModel):
    input: List[int]
    output: int


class GeneratedTests(BaseModel):
    tests: List[TestCase]


tests_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Ты генерируешь тесты для задач по программированию и алгоритмам.

По тексту задачи и уровню (junior / middle / senior) сгенерируй несколько корректных тестов.

Формат данных:
- tests: список объектов, у каждого два поля:
    - input: список целых чисел
    - output: одно целое число

Количество тестов: примерно от 5 до 10.
Отвечай строго в соответствии с этой схемой, без пояснений и комментариев.""",
        ),
        ("user", "Уровень: {level}\nТекст задачи:\n{task_text}"),
    ]
)

tests_chain = tests_prompt | llm.with_structured_output(GeneratedTests)


async def generate_tests_for_task(
    task_text: str, level: LevelType
) -> List[TestCase]:
    result: GeneratedTests = await tests_chain.ainvoke(
        {"level": level.value, "task_text": task_text}
    )
    return result.tests


async def generate_and_store_tests(
    task_id: str,
    task_text: str,
    level: LevelType,
) -> None:
    """
    Генерируем тесты и сохраняем их в таблицу task_tests.
    """
    tests = await generate_tests_for_task(task_text, level)
    await save_task_tests(
        task_id,
        [TestCaseModel(**t.model_dump()) for t in tests],
    )
