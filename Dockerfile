FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Установим docker-cli, чтобы из контейнера вызывать docker run
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# зависимости
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# код
COPY . .

EXPOSE 8000

# если у тебя приложение называется по-другому —
# поменяй backend_ide.main:app на свой модуль
CMD ["uvicorn", "backend_ide.main:app", "--host", "0.0.0.0", "--port", "8000"]
