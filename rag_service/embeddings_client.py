# rag_service/embeddings_client.py
from typing import List
from langchain_core.embeddings import Embeddings
from openai import OpenAI
from .config import settings


class ExternalAPIEmbeddings(Embeddings):
    """
    OpenAI-compatible embeddings wrapper.
    Uses:
        from openai import OpenAI
        client.embeddings.create(...)
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.API_KEY,
            base_url=settings.BASE_URL.rstrip("/"),
        )
        self.model = settings.EMBED_MODEL

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Returns list of embedding vectors for documents.
        """
        resp = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in resp.data]

    def embed_query(self, text: str) -> List[float]:
        """
        Returns single vector for a query.
        """
        resp = self.client.embeddings.create(
            model=self.model,
            input=[text],
        )
        return resp.data[0].embedding


embeddings = ExternalAPIEmbeddings()
