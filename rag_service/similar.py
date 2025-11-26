# rag_service/similar.py
from typing import Tuple, List

import anyio
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from .llm_client import llm
from .vector_store import (
    LevelType,
    similarity_search_for_level,
)
from .utils import clean_query


similar_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """/no_think Ты помогаешь подготовить поисковый запрос для поиска задач в базе.

По описанию темы и уровню (junior/middle/senior) составь короткий, чёткий запрос,
по которому легко найти нужные задачи.

Верни только сам текст запроса, без пояснений.""",
        ),
        ("user", "Уровень: {level}\nОписание: {description}"),
    ]
)

similar_chain = similar_prompt | llm | StrOutputParser()


async def build_search_query(level: LevelType, description: str) -> str:
    return await similar_chain.ainvoke(
        {"level": level.value, "description": description}
    )


async def find_similar_tasks(
    level: LevelType, description: str, k: int = 5
) -> Tuple[str, List[Document]]:
    """
    Возвращает (поисковый_запрос, список документов).
    """
    search_query = clean_query(await build_search_query(level, description))
    docs = await anyio.to_thread.run_sync(
        similarity_search_for_level,
        level,
        search_query,
        k,
    )
    return search_query, docs
