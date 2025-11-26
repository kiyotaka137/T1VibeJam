# runner/Dockerfile
FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /backend_ide

# Если понадобятся зависимости — ставь здесь:
# RUN pip install --no-cache-dir ...

# Кладём скрипт раннера внутрь образа
COPY run_tests_py.py /backend_ide/runners/run_tests_py.py

# По умолчанию контейнер выполняет этот скрипт
ENTRYPOINT ["python", "/backend_ide/runners/run_tests_py.py"]
