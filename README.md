# 🧠 RAG Task Service

Микросервис для генерации алгоритмических задач, умного поиска, адаптивного обучения и контекстных подсказок.
Использует **FastAPI**, **LangChain**, **PostgreSQL (pgvector)** и **LLM** (совместимые с OpenAI API).

---

## ✨ Возможности

1.  **Генерация задач (AI Generation):** Создание полноценной задачи (условие, код, тесты) по указанной теме и уровню сложности.
2.  **Оформление задач HR (Refinement):** Преобразование "сырого" текста условия от HR в структурированный JSON с авто-генерацией тестов и шаблонов кода.
3.  **Адаптивное обучение (Next Task):** Генерация следующей задачи на основе успехов пользователя (время решения). Если решил быстро — уровень повышается, если долго — понижается.
4.  **Гибридное хранение:**
    * **SQL (PostgreSQL):** Хранит полную структуру задачи, скрытые тесты и историю чата.
    * **Vector (PGVector):** Хранит семантические эмбеддинги для умного поиска.
5.  **Умный поиск:** Поиск задач по смыслу (например, запрос "сортировка" найдет "Merge Sort").
6.  **Контекстные подсказки (Hints):** Чат-бот (Ментор), который помнит историю переписки по конкретной задаче и дает наводящие подсказки.

---

## 🛠 Технологический стек

* **Язык:** Python 3.10+
* **API:** FastAPI
* **LLM Orchestration:** LangChain
* **Database:** PostgreSQL 15+
* **Vector Extension:** pgvector
* **Drivers:** `asyncpg` (асинхронный), `psycopg` (синхронный для LangChain), `sqlalchemy`.

---

## 🚀 Быстрый старт

### 1. Конфигурация (.env)
Создайте файл `.env` в корне проекта:

```ini
# --- LLM API Settings ---
API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxx
BASE_URL=[https://llm.t1v.scibox.tech/v1](https://llm.t1v.scibox.tech/v1)

# --- Models ---
EMBED_MODEL=bge-m3
LLM_MODEL=qwen3-32b-awq
CODER_MODEL=qwen3-coder-30b-a3b-instruct-fp8
HINT_MODEL=qwen3-32b-awq

# --- Database ---
PG_HOST=localhost
PG_PORT=5434
PG_DB=rag_db
PG_USER=rag_user
PG_PASSWORD=rag_password

# Названия таблиц (коллекций)
PG_COLLECTION_JUNIOR=tasks_junior
PG_COLLECTION_MIDDLE=tasks_middle
PG_COLLECTION_SENIOR=tasks_senior
````

### 2\. Запуск через Docker (Рекомендуется)

Запускает и базу данных, и API сервис в контейнерах.

```bash
# Сборка и запуск
docker-compose up --build
```

API будет доступно по адресу: `http://localhost:8000`

### 3\. Локальный запуск (для разработки)

Запускаем базу в Docker, а код — локально.

```bash
# 1. Запустить только БД
docker-compose up -d db

# 2. Установить зависимости
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Запустить сервер
uvicorn rag_service.api:app --reload --port 8000
```

-----

## 🔌 API Documentation (Integration Guide)

### 1\. Генерация задач

#### 🤖 Автоматическая генерация (`POST /generate_task`)

Генерирует задачу "с нуля" по теме.

**Request:**

```json
{
  "level": "junior",
  "topic": "Binary Search"
}
```

#### 📝 Создание из текста HR (`POST /create_custom_task`)

Превращает сырой текст в структурированную задачу.

**Request:**

```json
{
  "level": "middle",
  "raw_text": "Дана строка, нужно найти самый длинный палиндром..."
}
```

#### 📈 Адаптивная генерация (`POST /generate_next_task`)

Генерирует следующую задачу на основе результатов предыдущей.

  * \< 15 мин: Уровень повышается.
  * \> 35 мин: Уровень понижается.
  * Иначе: Тот же уровень, похожая тема.

**Request:**

```json
{
  "prev_task_id": "uuid-string...",
  "time_spent_sec": 300,        // Время решения в секундах
  "user_solution": "def solve()..." // Код пользователя
}
```

**Response (для всех методов генерации):**

```json
{
  "task_id": "f73a95f9...",
  "task_data": {
    "title": "...",
    "description": "...",
    "initial_code_python": "...",
    "test_cases": [...],
    "constraints": [...]
  },
  "new_level": "middle", // Только для adaptive
  "message": "Success"
}
```

-----

### 2\. Работа с задачей

#### 🔍 Поиск (`POST /search_tasks`)

**Request:**

```json
{
  "query": "сортировка массивов",
  "level": "junior",
  "limit": 5
}
```

#### 📖 Получение полной задачи (`GET /task/{task_id}`)

Возвращает **всё**, что есть в базе (включая историю чата).

#### 🧪 Получение тестов (`GET /tests/{task_id}`)

Используется **Checker-сервисом**. Возвращает чистый список тестов.

-----

### 3\. Подсказки (Ментор)

#### 💡 Генерация подсказки (`POST /hint`)

Сервис сам сохраняет историю переписки в БД.

**Request:**

```json
{
  "task_id": "uuid-string...",
  "user_code": "def solution(): return 0",
  "user_message": "Я застрял, что делать?"
}
```

**Response:**

```json
{
  "hint": "Попробуйте использовать два указателя..."
}
```

-----

## 🗄 Структура Базы Данных

Сервис использует **PostgreSQL** (3 таблицы: `tasks_junior`, `tasks_middle`, `tasks_senior`).

| Название колонки | Тип | Описание |
| :--- | :--- | :--- |
| **`task_id`** | `TEXT` (PK) | UUID задачи. |
| **`title`** | `TEXT` | Заголовок. |
| **`description`** | `TEXT` | Условие задачи. |
| **`test_cases`** | `JSONB` | Скрытые тесты `[{input: "...", output: "..."}]`. |
| **`constraints`** | `JSONB` | Ограничения `["1 <= n <= 100"]`. |
| **`chat_history`** | `JSONB` | История диалога `[{role: "user", content: "..."}]`. |

-----

## 🧪 Тестирование

Для проверки всех сценариев (Generative AI, RAG Search, Hints, History) используйте скрипт:

```bash
python test_flow_v2.py
```

````

---