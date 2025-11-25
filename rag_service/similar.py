# rag_service/similar.py
import re
from typing import Tuple, List
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from .llm_client import llm
from .vector_store import (
    LevelType,
    similarity_search_for_level,
)


similar_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """/no_think Ты помогаешь подготовить поисковый запрос для поиска задач в базе.

По описанию темы и уровню (junior/middle/senior) составь короткий, чёткий текстовый запрос,
который хорошо отражает, какие задачи нужно найти.

Верни только сам запрос, без пояснений.""",
        ),
        ("user", "Уровень: {level}\nОписание: {description}"),
    ]
)

similar_chain = similar_prompt | llm | StrOutputParser()


def clean_query(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()

def build_search_query(level: LevelType, description: str) -> str:
    return similar_chain.invoke(
        {"level": level.value, "description": description}
    )


def find_similar_tasks(
    level: LevelType, description: str, k: int = 5
) -> Tuple[str, List[Document]]:
    """
    Возвращает (готовый_поисковый_запрос, список документов).
    """
    search_query = build_search_query(level, description)
    docs = similarity_search_for_level(level, search_query, k=k)
    return search_query, docs
