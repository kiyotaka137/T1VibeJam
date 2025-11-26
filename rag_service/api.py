# rag_service/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, List, Dict, Optional

# Импортируем новую функцию workflow
from .tasks import generate_task_workflow, create_custom_task_workflow, TaskStructure
from .hints import hint_service
from .db_storage import init_db_tables, get_task_tests_raw, get_full_task_by_id, LevelType
from .similar import find_similar_tasks

app = FastAPI(title="RAG Task Service")


@app.on_event("startup")
async def on_startup():
    await init_db_tables()


# ----- Models -----

class GenerateTaskRequest(BaseModel):
    level: str
    topic: str

class CreateCustomTaskRequest(BaseModel):
    level: str
    raw_text: str # Текст от HR


class GenerateTaskResponse(BaseModel):
    # ИСПРАВЛЕНО: используем Optional вместо |
    task_id: Optional[str]
    task_data: Optional[TaskStructure]
    message: str


class HintRequest(BaseModel):
    task_id: str
    user_code: str
    user_message: str


class HintResponse(BaseModel):
    hint: str


class SearchRequest(BaseModel):
    query: str
    level: str
    limit: int = 5


class SearchResultItem(BaseModel):
    task_id: str
    # ИСПРАВЛЕНО: используем Optional вместо |
    title: Optional[str]
    preview: str


class TestsResponse(BaseModel):
    task_id: str
    tests: Any


def parse_level(s: str) -> LevelType:
    s = s.strip().lower()
    if s == "junior": return LevelType.JUNIOR
    if s == "middle": return LevelType.MIDDLE
    if s == "senior": return LevelType.SENIOR
    raise ValueError("Invalid level")


# ----- Endpoints -----

@app.post("/generate_task", response_model=GenerateTaskResponse)
async def generate_task_endpoint(req: GenerateTaskRequest):
    try:
        lvl = parse_level(req.level)
    except ValueError:
        raise HTTPException(400, "Invalid level")

    task_id, task_data = await generate_task_workflow(lvl, req.topic)

    if not task_id:
        return GenerateTaskResponse(task_id=None, task_data=None, message="Fail")

    return GenerateTaskResponse(task_id=task_id, task_data=task_data, message="Success")


# 2. Создание из сырого текста HR (НОВЫЙ)
@app.post("/create_custom_task", response_model=GenerateTaskResponse)
async def create_custom_task_endpoint(req: CreateCustomTaskRequest):
    """
    Принимает сырой текст задачи от HR, облагораживает его через LLM,
    генерирует тесты/код и сохраняет как полноценную задачу.
    """
    try:
        lvl = parse_level(req.level)
    except ValueError:
        raise HTTPException(400, "Invalid level")

    task_id, task_data = await create_custom_task_workflow(lvl, req.raw_text)

    if not task_id:
        return GenerateTaskResponse(task_id=None, task_data=None, message="Ошибка обработки задачи.")

    return GenerateTaskResponse(
        task_id=task_id,
        task_data=task_data,
        message="Задача успешно создана из описания HR."
    )


@app.post("/hint", response_model=HintResponse)
async def hint_endpoint(req: HintRequest):
    hint = await hint_service.process_hint(req.task_id, req.user_code, req.user_message)
    return HintResponse(hint=hint)


@app.post("/search_tasks", response_model=List[SearchResultItem])
async def search_tasks_endpoint(req: SearchRequest):
    try:
        lvl = parse_level(req.level)
    except ValueError:
        raise HTTPException(400, "Invalid level")

    _, docs = await find_similar_tasks(level=lvl, description=req.query, k=req.limit)

    results = []
    for doc in docs:
        meta = doc.metadata
        t_id = meta.get("task_id")
        if not t_id: continue

        results.append(SearchResultItem(
            task_id=t_id,
            title=meta.get("title", "No Title"),
            preview=doc.page_content[:200]
        ))
    return results


@app.get("/task/{task_id}", response_model=Dict[str, Any])
async def get_task_detail_endpoint(task_id: str):
    task_data = await get_full_task_by_id(task_id)
    if not task_data:
        raise HTTPException(404, "Task not found")
    return task_data


@app.get("/tests/{task_id}", response_model=TestsResponse)
async def get_tests(task_id: str):
    tests = await get_task_tests_raw(task_id)
    if not tests: raise HTTPException(404, "Not found")
    return TestsResponse(task_id=task_id, tests=tests)