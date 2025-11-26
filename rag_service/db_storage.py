# rag_service/db_storage.py
import json
from typing import Optional, Any, List, Dict
import asyncpg
from pydantic import BaseModel
from enum import Enum

from .config import settings


# Типы уровней (дублируем Enum или импортируем из vector_store, чтобы избежать циклических импортов - лучше определить здесь или в отдельном common файле. Пока оставим строки или простой импорт, если vector_store не зависит от этого файла.)
# Для простоты определим здесь Helper
class LevelType(str, Enum):
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"


# --- Модель, совпадающая с JSON задачи ---
class TaskDBModel(BaseModel):
    task_id: str
    title: str
    description: str
    input_description: str
    output_description: str
    constraints: List[str]
    function_name: str
    initial_code_python: str
    initial_code_cpp: str
    test_cases: Any  # Сохраняем как JSONB

    # Поля, которые управляются БД
    chat_history: List[Dict[str, str]] = []
    hints: List[str] = []


_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.pg_dsn)
    return _pool


def get_table_name(level: LevelType) -> str:
    if level == LevelType.JUNIOR: return settings.PG_COLLECTION_JUNIOR
    if level == LevelType.MIDDLE: return settings.PG_COLLECTION_MIDDLE
    if level == LevelType.SENIOR: return settings.PG_COLLECTION_SENIOR
    return "tasks_junior"


async def init_db_tables() -> None:
    """Создает 3 таблицы с полями под JSON задачи + историю."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        for level in LevelType:
            table = get_table_name(level)
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    task_id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    input_description TEXT,
                    output_description TEXT,
                    constraints JSONB,
                    function_name TEXT,
                    initial_code_python TEXT,
                    initial_code_cpp TEXT,
                    test_cases JSONB,
                    chat_history JSONB DEFAULT '[]'::jsonb,
                    hints JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)


# --- Сохранение задачи ---
async def save_generated_task_to_db(level: LevelType, task_data: TaskDBModel) -> None:
    table = get_table_name(level)
    pool = await get_pool()

    constraints_json = json.dumps(task_data.constraints)

    # Сериализация тестов
    if hasattr(task_data.test_cases, 'model_dump'):
        tests_json = json.dumps([t.model_dump() for t in task_data.test_cases])
    elif isinstance(task_data.test_cases, list):
        try:
            tests_json = json.dumps([t.dict() for t in task_data.test_cases])
        except:
            tests_json = json.dumps(task_data.test_cases)
    else:
        tests_json = json.dumps(task_data.test_cases)

    async with pool.acquire() as conn:
        await conn.execute(f"""
            INSERT INTO {table} (
                task_id, title, description, input_description, output_description,
                constraints, function_name, initial_code_python, initial_code_cpp,
                test_cases, chat_history, hints
            ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10::jsonb, '[]'::jsonb, '[]'::jsonb)
            ON CONFLICT (task_id) DO NOTHING
        """,
                           task_data.task_id, task_data.title, task_data.description,
                           task_data.input_description, task_data.output_description,
                           constraints_json, task_data.function_name,
                           task_data.initial_code_python, task_data.initial_code_cpp,
                           tests_json
                           )


# --- Получение полной задачи (для API) ---
async def get_full_task_by_id(task_id: str) -> Optional[Dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        for level in LevelType:
            table = get_table_name(level)
            row = await conn.fetchrow(f"SELECT * FROM {table} WHERE task_id = $1", task_id)
            if row:
                task_data = dict(row)
                # Десериализация
                for field in ['constraints', 'test_cases', 'chat_history', 'hints']:
                    if isinstance(task_data.get(field), str):
                        task_data[field] = json.loads(task_data[field])
                task_data['level'] = level.value
                return task_data
    return None


# --- Получение контекста для подсказки ---
async def get_task_context_for_hint(task_id: str) -> Optional[Dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        for level in LevelType:
            table = get_table_name(level)
            row = await conn.fetchrow(f"SELECT description, chat_history, hints FROM {table} WHERE task_id = $1",
                                      task_id)
            if row:
                return {
                    "level": level,
                    "description": row["description"],
                    "chat_history": json.loads(row["chat_history"]) if isinstance(row["chat_history"], str) else row[
                        "chat_history"],
                    "hints": json.loads(row["hints"]) if isinstance(row["hints"], str) else row["hints"]
                }
    return None


# --- Обновление истории чата ---
async def update_chat_history(level: LevelType, task_id: str, new_history: List[Dict], new_hint: str = None):
    table = get_table_name(level)
    pool = await get_pool()
    history_json = json.dumps(new_history)

    async with pool.acquire() as conn:
        await conn.execute(f"UPDATE {table} SET chat_history = $1::jsonb WHERE task_id = $2", history_json, task_id)
        if new_hint:
            await conn.execute(f"UPDATE {table} SET hints = hints || $1::jsonb WHERE task_id = $2",
                               json.dumps([new_hint]), task_id)


# --- Получение только тестов (для чекера) ---
async def get_task_tests_raw(task_id: str) -> Any:
    pool = await get_pool()
    async with pool.acquire() as conn:
        for level in LevelType:
            table = get_table_name(level)
            row = await conn.fetchrow(f"SELECT test_cases FROM {table} WHERE task_id = $1", task_id)
            if row:
                raw = row["test_cases"]
                return json.loads(raw) if isinstance(raw, str) else raw
    return None