# rag_service/similar.py
from typing import Tuple, List, Any
import anyio
from langchain_core.documents import Document
from .db_storage import LevelType
from .vector_store import similarity_search_for_level


async def find_similar_tasks(
        level: LevelType, description: str, k: int = 5
) -> Tuple[str, List[Document]]:
    """
    Простой поиск по PGVector.
    Возвращает (текст_запроса, список_документов).
    """
    # Здесь можно добавить LLM-обработку запроса, если нужно
    search_query = description.strip()

    docs = await anyio.to_thread.run_sync(
        similarity_search_for_level, level, search_query, k
    )
    return search_query, docs