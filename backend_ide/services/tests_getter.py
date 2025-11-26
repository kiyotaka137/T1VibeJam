import os
import httpx
from fastapi import HTTPException, status

RAG_API_URL = os.getenv("RAG_API_URL", "http://rag_api:8000")

async def fetch_tests_from_rag(task_id: str):
    url = f"{RAG_API_URL}/tests/{task_id}"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Не удалось достучаться до RAG-сервиса: {repr(e)}",
        ) from e

    if resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Тесты для задачи {task_id} не найдены в RAG",
        )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка от RAG-сервиса: {resp.status_code} {resp.text}",
        )

    data = resp.json()
    tests = data.get("tests")
    if tests is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Некорректный ответ от RAG (нет поля 'tests')",
        )
    return tests
