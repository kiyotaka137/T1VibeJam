# rag_service/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Общий ключ и базовый URL
    API_KEY: str
    BASE_URL: str

    # Модели
    LLM_MODEL: str  # Общая модель (для чата и т.д.)
    EMBED_MODEL: str

    # Специфичные модели
    CODER_MODEL: str = "qwen3-coder-30b-a3b-instruct-fp8"  # Для генерации задач
    HINT_MODEL: str = "qwen3-32b-awq"  # Для подсказок

    # ---- Postgres + pgvector ----
    PG_HOST: str = "localhost"
    PG_PORT: int = 5434
    PG_DB: str = "rag_db"
    PG_USER: str = "rag_user"
    PG_PASSWORD: str = "rag_password"

    # Имена коллекций/таблиц
    PG_COLLECTION_JUNIOR: str = "tasks_junior"
    PG_COLLECTION_MIDDLE: str = "tasks_middle"
    PG_COLLECTION_SENIOR: str = "tasks_senior"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def pg_connection_string(self) -> str:
        return (
            f"postgresql+psycopg://{self.PG_USER}:{self.PG_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"
        )

    @property
    def pg_dsn(self) -> str:
        return (
            f"postgresql://{self.PG_USER}:{self.PG_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"
        )


settings = Settings()