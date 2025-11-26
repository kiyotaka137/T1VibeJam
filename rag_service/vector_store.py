# rag_service/vector_store.py
from typing import Optional, Dict, Any, List
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document

from .config import settings
from .embeddings_client import embeddings
from .db_storage import LevelType # Импортируем общий Enum

vectorstore_junior = PGVector(
    connection_string=settings.pg_connection_string,
    embedding_function=embeddings,
    collection_name=settings.PG_COLLECTION_JUNIOR,
)

vectorstore_middle = PGVector(
    connection_string=settings.pg_connection_string,
    embedding_function=embeddings,
    collection_name=settings.PG_COLLECTION_MIDDLE,
)

vectorstore_senior = PGVector(
    connection_string=settings.pg_connection_string,
    embedding_function=embeddings,
    collection_name=settings.PG_COLLECTION_SENIOR,
)

def get_vectorstore_for_level(level: LevelType) -> PGVector:
    if level == LevelType.JUNIOR: return vectorstore_junior
    if level == LevelType.MIDDLE: return vectorstore_middle
    if level == LevelType.SENIOR: return vectorstore_senior
    raise ValueError(f"Unknown level: {level}")

def save_task_to_vectorstore(
    text: str,
    source: str,
    level: LevelType,
    task_id: str,          # Обязательный ID для связки с SQL
    topic: Optional[str] = None,
    extra_meta: Optional[Dict] = None,
) -> str:
    vs = get_vectorstore_for_level(level)

    metadata: Dict[str, Any] = {
        "source": source,
        "level": level.value,
        "topic": topic,
        "task_id": task_id,
    }
    if extra_meta:
        metadata.update(extra_meta)

    # Сохраняем с явным ID
    vs.add_texts(
        texts=[text],
        metadatas=[metadata],
        ids=[task_id],
    )

    return task_id

def similarity_search_for_level(
    level: LevelType, query: str, k: int = 5
) -> List[Document]:
    vs = get_vectorstore_for_level(level)
    return vs.similarity_search(query, k=k)