# rag_service/rag.py
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .llm_client import llm
from .vector_store import (
    similarity_search_all_levels,
    format_docs_for_context,
)


qa_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Ты ассистент по решению задач.

Тебе дан контекст — несколько задач из базы (могут быть не идеально релевантными).
1. Если контекст помогает — используй его.
2. Если нет — не подгоняй решение под контекст.

Контекст:
{context}""",
        ),
        ("user", "{question}"),
    ]
)

qa_chain = qa_prompt | llm | StrOutputParser()


def get_rag_context(message: str) -> str:
    docs = similarity_search_all_levels(message, k_per_level=2)
    return format_docs_for_context(docs)


def answer_with_rag(message: str) -> str:
    context = get_rag_context(message)
    return qa_chain.invoke({"context": context, "question": message})
