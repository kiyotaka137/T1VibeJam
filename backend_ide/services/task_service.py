from typing import Optional, List, Dict, Any

from sqlalchemy import select

from backend_ide.db.session import async_session_maker
from backend_ide.db.models import Task


async def get_test_cases_for_task(task_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Возвращает список тест-кейсов для задачи.

    Каждый кейс — dict вида:
      { "id": str, "input": ..., "expected": ... }
    """
    async with async_session_maker() as session:
        stmt = select(Task.test_cases).where(Task.id == task_id)
        result = await session.execute(stmt)
        row = result.first()

        if row is None:
            return None

        (cases,) = row

        if not isinstance(cases, list):
            raise ValueError("test_cases в БД должен быть JSON-массивом.")

        return cases
