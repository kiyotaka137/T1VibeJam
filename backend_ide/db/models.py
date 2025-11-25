from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    level: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Массив кейсов: [{"id": ..., "input": ..., "expected": ...}, ...]
    test_cases: Mapped[list] = mapped_column(JSONB, nullable=False)
