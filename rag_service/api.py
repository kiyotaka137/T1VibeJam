# rag_service/api.py
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .tasks import (
    generate_task,
    create_user_task_with_tests,
    create_generated_task_with_tests,
)
from .similar import find_similar_tasks
from .vector_store import LevelType
from .db_tests import init_tests_table, load_task_tests, TestCaseModel


app = FastAPI(title="RAG Task Service")


# ----- startup -----

@app.on_event("startup")
async def on_startup():
    # инициализируем таблицу для тестов
    await init_tests_table()


# ----- Модели -----

class ChatRequest(BaseModel):
    user_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    reply: str
    mode: str            # "SUBMIT" или "GENERATE"
    task_id: str | None  # id задачи, если она была сохранена


class SimilarRequest(BaseModel):
    level: str           # "junior" | "middle" | "senior"
    description: str
    k: int = 5


class SimilarTask(BaseModel):
    task_id: str | None = None
    text: str
    topic: str | None = None
    level: str | None = None
    source: str | None = None


class SimilarResponse(BaseModel):
    query: str
    tasks: List[SimilarTask]


class TestsResponse(BaseModel):
    task_id: str
    tests: List[TestCaseModel]


# ----- Префиксы для SUBMIT -----

SUBMIT_PREFIXES = {
    LevelType.JUNIOR: "SUBMIT_JUNIOR ",
    LevelType.MIDDLE: "SUBMIT_MIDDLE ",
    LevelType.SENIOR: "SUBMIT_SENIOR ",
}


def parse_level(level_str: str) -> LevelType:
    normalized = level_str.strip().lower()
    if normalized == "junior":
        return LevelType.JUNIOR
    if normalized == "middle":
        return LevelType.MIDDLE
    if normalized == "senior":
        return LevelType.SENIOR
    raise ValueError(f"Unknown level: {level_str}")


# ----- /chat -----

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Логика теперь простая:
    1) Если сообщение начинается с SUBMIT_JUNIOR/MIDDLE/SENIOR — считаем, что это готовая задача.
       Сохраняем её в нужную коллекцию, генерируем тесты.
    2) Всё остальное — считаем запросом на генерацию задачи.
       Генерируем задачу, и если should_save=true, сохраняем + генерируем тесты.
    """
    raw_message = req.message.strip()

    # 1) SUBMIT_JUNIOR / SUBMIT_MIDDLE / SUBMIT_SENIOR
    for level, prefix in SUBMIT_PREFIXES.items():
        if raw_message.startswith(prefix):
            task_text = raw_message[len(prefix):].strip()
            if not task_text:
                return ChatResponse(
                    reply="После префикса нужно написать текст задачи.",
                    mode="SUBMIT",
                    task_id=None,
                )

            task_id = await create_user_task_with_tests(task_text, level)

            return ChatResponse(
                reply=(
                    f"Задачу уровня {level.value} сохранил в базу "
                    f"и сгенерировал для неё тесты (task_id: {task_id})."
                ),
                mode="SUBMIT",
                task_id=task_id,
            )

    # 2) Всё остальное — генерация задачи
    gen_task = await generate_task(raw_message)
    task_id = await create_generated_task_with_tests(gen_task)

    # task_id может быть None, если should_save = false
    return ChatResponse(
        reply=gen_task.task_text,
        mode="GENERATE",
        task_id=task_id,
    )


# ----- /similar -----

@app.post("/similar", response_model=SimilarResponse)
async def similar_endpoint(req: SimilarRequest):
    try:
        level = parse_level(req.level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="level должен быть одним из: junior, middle, senior",
        )

    query, docs = await find_similar_tasks(
        level=level,
        description=req.description,
        k=req.k,
    )

    tasks: List[SimilarTask] = []
    for d in docs:
        meta = d.metadata or {}
        tasks.append(
            SimilarTask(
                task_id=meta.get("task_id"),
                text=d.page_content,
                topic=meta.get("topic"),
                level=meta.get("level"),
                source=meta.get("source"),
            )
        )

    return SimilarResponse(query=query, tasks=tasks)


# ----- /tests/{task_id} -----
# Эту ручку будет дергать другой микросервис

@app.get("/tests/{task_id}", response_model=TestsResponse)
async def get_tests(task_id: str):
    tests = await load_task_tests(task_id)
    if tests is None:
        raise HTTPException(
            status_code=404,
            detail="Tests not found for this task_id",
        )
    return TestsResponse(task_id=task_id, tests=tests)
