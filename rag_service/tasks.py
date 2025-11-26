# rag_service/tasks.py
from typing import Optional
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate

from .llm_client import llm
from .vector_store import save_task_to_vectorstore, LevelType
from .tests_gen import generate_and_store_tests
from .utils import clean_query


class GeneratedTask(BaseModel):
    task_text: str
    topic: Optional[str] = None
    level: LevelType
    should_save: bool


# Промпт без JSON-примеров, только словесное описание
generate_task_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Ты генератор учебных задач.

По запросу пользователя сгенерируй ОДНУ задачу.

Структура ответа:
- task_text: текст задачи (строка)
- topic: кратко тема задачи (строка, можно пусто)
- level: уровень задачи: "junior", "middle" или "senior"
- should_save: булево значение (true/false), стоит ли сохранять задачу в базу.

Отвечай строго в соответствии с этой схемой, без пояснений и комментариев.""",
        ),
        ("user", "{request}"),
    ]
)

generate_task_chain = generate_task_prompt | llm.with_structured_output(GeneratedTask)


async def generate_task(request_text: str) -> GeneratedTask:
    """
    Генерирует задачу по тексту запроса пользователя.
    """
    result: GeneratedTask = await generate_task_chain.ainvoke(
        {"request": request_text}
    )
    return result


async def create_user_task_with_tests(
    task_text: str,
    level: LevelType,
) -> str:
    """
    1) Сохраняем пользовательскую задачу в векторное хранилище (получаем task_id)
    2) Генерируем тесты и сохраняем их в таблицу task_tests
    3) Возвращаем task_id
    """
    task_id = save_task_to_vectorstore(
        text=clean_query(task_text),
        source="user",
        level=level,
        topic=None,
        extra_meta=None,
        task_id=None,
    )

    await generate_and_store_tests(task_id, task_text, level)
    return task_id


async def create_generated_task_with_tests(
    gen_task: GeneratedTask,
) -> Optional[str]:
    """
    То же самое, но для сгенерированной задачи.
    Если should_save = false — ничего не сохраняем и тесты не генерируем.
    """
    if not gen_task.should_save:
        return None

    task_id = save_task_to_vectorstore(
        text=gen_task.task_text,
        source="generated",
        level=gen_task.level,
        topic=gen_task.topic,
        extra_meta=None,
        task_id=None,
    )

    await generate_and_store_tests(task_id, gen_task.task_text, gen_task.level)
    return task_id
