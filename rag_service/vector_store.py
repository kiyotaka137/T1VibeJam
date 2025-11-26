# rag_service/vector_store.py
import uuid
from enum import Enum
from typing import Optional, Dict, Any, List

from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document

from .config import settings
from .embeddings_client import embeddings


class LevelType(str, Enum):
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"


# Три отдельные коллекции в pgvector
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
    if level == LevelType.JUNIOR:
        return vectorstore_junior
    if level == LevelType.MIDDLE:
        return vectorstore_middle
    if level == LevelType.SENIOR:
        return vectorstore_senior
    raise ValueError(f"Unknown level: {level}")


def save_task_to_vectorstore(
    text: str,
    source: str,
    level: LevelType,
    topic: Optional[str] = None,
    extra_meta: Optional[Dict[str, Any]] = None,
    task_id: Optional[str] = None,
) -> str:
    """
    Сохраняет задачу в нужную векторку.
    Генерирует task_id (uuid), если не передан.
    Этот task_id будет:
      - primary key в таблице pgvector
      - лежать в metadata как "task_id"
    """
    if task_id is None:
        task_id = str(uuid.uuid4())

    vs = get_vectorstore_for_level(level)

    metadata: Dict[str, Any] = {
        "source": source,       # "user" или "generated"
        "level": level.value,
        "topic": topic,
        "task_id": task_id,
    }
    if extra_meta:
        metadata.update(extra_meta)

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


def similarity_search_all_levels(
    query: str,
    k_per_level: int = 2,
) -> List[Document]:
    docs: List[Document] = []
    for level in LevelType:
        vs = get_vectorstore_for_level(level)
        docs.extend(vs.similarity_search(query, k=k_per_level))
    return docs


def format_docs_for_context(docs: List[Document]) -> str:
    parts = []
    for i, d in enumerate(docs, start=1):
        meta = d.metadata or {}
        topic = meta.get("topic")
        level = meta.get("level")
        source = meta.get("source")
        task_id = meta.get("task_id")

        header = f"[Задача {i}"
        if task_id:
            header += f", id: {task_id}"
        if level:
            header += f", level: {level}"
        if topic:
            header += f", topic: {topic}"
        if source:
            header += f", source: {source}"
        header += "]"

        parts.append(f"{header}\n{d.page_content}")
    return "\n\n".join(parts)
