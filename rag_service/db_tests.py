# rag_service/db_tests.py
from typing import List, Optional
import asyncpg
import json
from pydantic import BaseModel

from .config import settings


class TestCaseModel(BaseModel):
    input: List[int]
    output: int


_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.pg_dsn)
    return _pool


async def init_tests_table() -> None:
    """
    Простая инициализация таблицы для хранения тестов.
    В проде лучше делать миграциями.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_tests (
                task_id TEXT PRIMARY KEY,
                tests   JSONB NOT NULL
            )
            """
        )


async def save_task_tests(task_id: str, tests: List[TestCaseModel]) -> None:
    """
    Сохраняем тесты как JSONB: сначала превращаем список моделей в JSON-строку.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        tests_payload = [t.model_dump() for t in tests]
        await conn.execute(
            """
            INSERT INTO task_tests (task_id, tests)
            VALUES ($1, $2::jsonb)
            ON CONFLICT (task_id)
            DO UPDATE SET tests = EXCLUDED.tests
            """,
            task_id,
            json.dumps(tests_payload),  # <-- теперь str, а не list
        )


async def load_task_tests(task_id: str) -> List[TestCaseModel] | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT tests FROM task_tests WHERE task_id = $1",
            task_id,
        )
        if row is None:
            return None

        # row["tests"] может уже быть dict/list (если asyncpg декодит),
        # но после нашего json.dumps/jsonb, PostgreSQL хранит JSONB,
        # asyncpg обычно возвращает его как str → подстрахуемся.
        raw = row["tests"]
        if isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw

        return [TestCaseModel(**t) for t in data]
