# rag_service/tasks.py
from typing import Optional
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate

from .llm_client import llm
from .vector_store import save_task_to_vectorstore, LevelType


class GeneratedTask(BaseModel):
    task_text: str
    topic: Optional[str] = None
    level: LevelType
    should_save: bool


generate_task_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Ты генератор учебных задач.

По запросу пользователя сгенерируй ОДНУ задачу и верни строго JSON:
{
  "task_text": "текст задачи",
  "topic": "кратко тема задачи (например 'деревья', 'системы уравнений')",
  "level": "junior" | "middle" | "senior",
  "should_save": true | false
}

Если задача получилась адекватной учебной и не совсем тривиальной, ставь should_save = true.
Если запрос странный или задача получилась мусорной, ставь should_save = false.""",
        ),
        ("user", "{request}"),
    ]
)

generate_task_chain = generate_task_prompt | llm.with_structured_output(GeneratedTask)


def generate_task(request_text: str) -> GeneratedTask:
    return generate_task_chain.invoke({"request": request_text})


def save_user_task(raw_message: str, level: LevelType) -> None:
    """
    Сохранение задачи, которую прислал пользователь.
    raw_message — уже без префикса SUBMIT_XXX.
    """
    save_task_to_vectorstore(
        text=raw_message,
        source="user",
        level=level,
        topic=None,
    )


def maybe_save_generated_task(task: GeneratedTask) -> None:
    if not task.should_save:
        return
    save_task_to_vectorstore(
        text=task.task_text,
        source="generated",
        level=task.level,
        topic=task.topic,
    )
