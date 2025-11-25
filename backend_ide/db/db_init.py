import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine

from backend_ide.db.models import Base  # твой Base + Task


# настройки БД, подставь свои
DB_NAME = "interview_service"
DB_USER = "postgres"       # или твой пользователь
DB_PASSWORD = "mypassword"
DB_HOST = "localhost"
DB_PORT = 5432


def create_database_if_not_exists():
    """
    Подключаемся к системной БД 'postgres' и создаём нашу БД, если её ещё нет.
    """
    conn = psycopg2.connect(
        dbname="postgres",  # системная БД по умолчанию
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # проверяем, есть ли уже такая БД
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cur.fetchone()

    if not exists:
        print(f"Создаю базу данных {DB_NAME}...")
        cur.execute(f'CREATE DATABASE "{DB_NAME}"')
    else:
        print(f"База данных {DB_NAME} уже существует")

    cur.close()
    conn.close()


def create_tables():
    """
    Создаём таблицы по моделям SQLAlchemy в нашей БД.
    """
    db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url, echo=True)
    Base.metadata.create_all(engine)
    print("Таблицы созданы (если их не было).")


if __name__ == "__main__":
    create_database_if_not_exists()
    create_tables()
