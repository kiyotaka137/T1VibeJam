# Dockerfile

FROM python:3.12-slim

WORKDIR /app

# зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# код сервиса
COPY rag_service ./rag_service


EXPOSE 8000

CMD ["uvicorn", "rag_service.api:app", "--host", "0.0.0.0", "--port", "8000"]
