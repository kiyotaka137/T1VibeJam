# rag_service/intent.py
from enum import Enum
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate

from .llm_client import llm


class IntentType(str, Enum):
    GENERATE_TASK = "GENERATE_TASK"
    CHAT = "CHAT"


class Intent(BaseModel):
    intent: IntentType


intent_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Ты классифицируешь сообщения в чате о задачах.

Префиксы SUBMIT_JUNIOR / SUBMIT_MIDDLE / SUBMIT_SENIOR уже обработаны бэкендом, 
до тебя доходит обычный текст.

Выбери ОДИН intent:
- GENERATE_TASK — пользователь просит придумать/сгенерировать новую задачу.
- CHAT — обычный диалог: решение, объяснение, обсуждение.

Отвечай строго JSON: {"intent": "GENERATE_TASK" | "CHAT"}""",
        ),
        ("user", "{message}"),
    ]
)

intent_chain = intent_prompt | llm.with_structured_output(Intent)


def detect_intent(message: str) -> IntentType:
    result = intent_chain.invoke({"message": message})
    return result.intent
