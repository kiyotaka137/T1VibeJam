# rag_service/api.py
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .intent import IntentType, detect_intent
from .tasks import generate_task, maybe_save_generated_task, save_user_task
from .rag import answer_with_rag
from .similar import find_similar_tasks
from .vector_store import LevelType


app = FastAPI(title="RAG Task Service")


# ----- Модели запросов/ответов -----

class ChatRequest(BaseModel):
    user_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    reply: str
    mode: str  # "SUBMIT", "GENERATE", "CHAT"


class SimilarRequest(BaseModel):
    level: str  # "junior" | "middle" | "senior"
    description: str
    k: int = 5


class SimilarTask(BaseModel):
    text: str
    topic: str | None = None
    level: str | None = None
    source: str | None = None


class SimilarResponse(BaseModel):
    query: str
    tasks: List[SimilarTask]


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
def chat_endpoint(req: ChatRequest):
    raw_message = req.message.strip()

    # 1) SUBMIT_JUNIOR / SUBMIT_MIDDLE / SUBMIT_SENIOR
    for level, prefix in SUBMIT_PREFIXES.items():
        if raw_message.startswith(prefix):
            task_text = raw_message[len(prefix):].strip()
            if not task_text:
                return ChatResponse(
                    reply="После префикса нужно написать текст задачи.",
                    mode="SUBMIT",
                )

            save_user_task(task_text, level)
            return ChatResponse(
                reply=f"Задачу уровня {level.value} сохранил в базу. "
                      f"Могу сгенерировать похожую или помочь с решением.",
                mode="SUBMIT",
            )

    # 2) Всё остальное — либо GENERATE_TASK, либо CHAT
    intent = detect_intent(raw_message)

    if intent == IntentType.GENERATE_TASK:
        gen_task = generate_task(raw_message)
        maybe_save_generated_task(gen_task)
        reply = gen_task.task_text
        return ChatResponse(reply=reply, mode="GENERATE")

    # 3) CHAT
    answer = answer_with_rag(raw_message)
    return ChatResponse(reply=answer, mode="CHAT")


# ----- /similar -----

@app.post("/similar", response_model=SimilarResponse)
def similar_endpoint(req: SimilarRequest):
    try:
        level = parse_level(req.level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="level должен быть одним из: junior, middle, senior",
        )

    query, docs = find_similar_tasks(
        level=level,
        description=req.description,
        k=req.k,
    )

    tasks: List[SimilarTask] = []
    for d in docs:
        meta = d.metadata or {}
        tasks.append(
            SimilarTask(
                text=d.page_content,
                topic=meta.get("topic"),
                level=meta.get("level"),
                source=meta.get("source"),
            )
        )

    return SimilarResponse(query=query, tasks=tasks)
