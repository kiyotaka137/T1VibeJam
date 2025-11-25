# rag_service/llm_client.py
from langchain_openai import ChatOpenAI
from .config import settings


llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    temperature=0
)
