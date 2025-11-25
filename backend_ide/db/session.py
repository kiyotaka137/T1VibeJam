from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from backend_ide.core.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # можно включить True для дебага SQL
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
