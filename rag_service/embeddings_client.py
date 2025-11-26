# rag_service/embeddings_client.py
from typing import List
from langchain_core.embeddings import Embeddings
from openai import OpenAI
from .config import settings

class ExternalAPIEmbeddings(Embeddings):
    """
    Обертка для эмбеддингов, совместимая с OpenAI API.
    Используется внутри PGVector.
    """

    def __init__(self):
        # Инициализируем клиента с настройками из config.py
        self.client = OpenAI(
            api_key=settings.API_KEY,
            base_url=settings.BASE_URL.rstrip("/"), # Убираем слеш на всякий случай
        )
        self.model = settings.EMBED_MODEL

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Генерация векторов для списка документов (при сохранении в БД)."""
        # Заменяем переносы строк на пробелы, это рекомендация для многих моделей
        texts = [t.replace("\n", " ") for t in texts]
        resp = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in resp.data]

    def embed_query(self, text: str) -> List[float]:
        """Генерация вектора для поискового запроса."""
        text = text.replace("\n", " ")
        resp = self.client.embeddings.create(
            model=self.model,
            input=[text],
        )
        return resp.data[0].embedding

# Создаем глобальный экземпляр, который будем импортировать
embeddings = ExternalAPIEmbeddings()