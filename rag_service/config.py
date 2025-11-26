# rag_service/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # общий ключ и базовый урл для обоих (LLM + эмбеддер)
    API_KEY: str
    BASE_URL: str

    # разные модели
    LLM_MODEL: str
    EMBED_MODEL: str

    # ---- Postgres + pgvector ----
    PG_HOST: str = "localhost"
    PG_PORT: int = 5434
    PG_DB: str = "rag_db"
    PG_USER: str = "rag_user"
    PG_PASSWORD: str = "rag_password"

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
        # для asyncpg
        return (
            f"postgresql://{self.PG_USER}:{self.PG_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"
        )


settings = Settings()
