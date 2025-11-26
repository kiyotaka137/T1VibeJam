import requests
import json
import time
import sys

# URL локально запущенного сервиса
BASE_URL = "http://localhost:8000"


def print_header(title):
    print(f"\n{'=' * 60}")
    print(f"🛠  SCENARIO: {title}")
    print(f"{'=' * 60}")


def debug_print(label: str, data: dict):
    """Красиво печатает JSON ответ от LLM/API"""
    print(f"\n🔍 [DEBUG] Полный ответ {label}:")
    print("-" * 40)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("-" * 40)


def test_full_flow():
    # ==================================================================================
    # 1. ГЕНЕРАЦИЯ ЗАДАЧИ
    # ==================================================================================
    print_header("1. Генерация задачи (HR)")

    topic = "Binary Search in rotated array"
    level = "middle"

    print(f"⏳ Отправляем запрос на генерацию... (Тема: {topic}, Уровень: {level})")
    start_time = time.time()

    try:
        gen_resp = requests.post(
            f"{BASE_URL}/generate_task",
            json={"level": level, "topic": topic}
        )
        gen_resp.raise_for_status()
        gen_data = gen_resp.json()
    except Exception as e:
        print(f"❌ Ошибка генерации: {e}")
        sys.exit(1)

    duration = time.time() - start_time
    task_id = gen_data.get("task_id")

    if not task_id:
        print("❌ Task ID не вернулся!")
        sys.exit(1)

    print(f"✅ Задача сгенерирована за {duration:.2f} сек.")

    # --- DEBUG ВЫВОД ---
    # Показываем структуру задачи, которую сгенерировала Coder Model
    debug_print("LLM Task Generation", gen_data['task_data'])

    # ==================================================================================
    # 2. ПОИСК ЗАДАЧИ
    # ==================================================================================
    print_header("2. Поиск задачи по вектору (Search)")

    search_query = "поиск в массиве"
    print(f"🔎 Ищем по запросу: '{search_query}'...")

    try:
        search_resp = requests.post(
            f"{BASE_URL}/search_tasks",
            json={"query": search_query, "level": level, "limit": 5}
        )
        search_resp.raise_for_status()
        search_results = search_resp.json()
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        sys.exit(1)

    found = False
    print(f"📥 Найдено задач: {len(search_results)}")

    # Выводим краткий список
    for item in search_results:
        print(f"   - [{item['task_id']}] {item['title']} (score: {item.get('score')})")
        if item['task_id'] == task_id:
            found = True

    if found:
        print("✅ Наша сгенерированная задача найдена в векторном поиске!")
    else:
        print("⚠️ Задача не найдена в топе поиска.")

    # ==================================================================================
    # 3. ПОЛУЧЕНИЕ ПОЛНОЙ ИНФОРМАЦИИ
    # ==================================================================================
    print_header("3. Загрузка полной задачи из SQL")

    try:
        get_resp = requests.get(f"{BASE_URL}/task/{task_id}")
        get_resp.raise_for_status()
        full_task = get_resp.json()
    except Exception as e:
        print(f"❌ Ошибка получения задачи: {e}")
        sys.exit(1)

    print("✅ Данные получены успешно.")
    # --- DEBUG ВЫВОД ---
    # Показываем, что реально лежит в базе (включая constraints, hidden tests и т.д.)
    debug_print("SQL Stored Task", full_task)

    # ==================================================================================
    # 4. ПОЛУЧЕНИЕ ТЕСТОВ
    # ==================================================================================
    print_header("4. Получение тестов (endpoint /tests/)")

    try:
        tests_resp = requests.get(f"{BASE_URL}/tests/{task_id}")
        tests_resp.raise_for_status()
        tests_data = tests_resp.json()
    except Exception as e:
        print(f"❌ Ошибка получения тестов: {e}")
        sys.exit(1)

    print(f"✅ Тесты получены. Количество: {len(tests_data['tests'])}")
    # Просто выведем первый тест для примера
    print(f"   Пример теста 1: {tests_data['tests'][0]}")

    # ==================================================================================
    # 5. ГЕНЕРАЦИЯ ПОДСКАЗКИ
    # ==================================================================================
    print_header("5. Генерация подсказки (Hint)")

    user_code = """
    class Solution:
        def search(self, nums, target):
            return -1 # пока не знаю как решать
    """
    user_msg = "Я понял, что массив отсортирован, но он сдвинут. Как найти точку сдвига?"

    print(f"🗣 Сообщение юзера: {user_msg}")
    print("⏳ Думаем над подсказкой...")

    try:
        hint_resp = requests.post(
            f"{BASE_URL}/hint",
            json={
                "task_id": task_id,
                "user_code": user_code,
                "user_message": user_msg,
                "chat_history": ""
            }
        )
        hint_resp.raise_for_status()
        hint_data = hint_resp.json()
    except Exception as e:
        print(f"❌ Ошибка подсказки: {e}")
        sys.exit(1)

    # --- DEBUG ВЫВОД ---
    # Показываем полный JSON ответа хинта
    debug_print("Hint LLM Response", hint_data)

    # ==================================================================================
    # 6. ПРОВЕРКА ИСТОРИИ
    # ==================================================================================
    print_header("6. Проверка сохранения истории в БД")

    get_resp_2 = requests.get(f"{BASE_URL}/task/{task_id}")
    full_task_2 = get_resp_2.json()
    history = full_task_2.get('chat_history', [])

    print(f"📚 Сообщений в истории: {len(history)}")

    # --- DEBUG ВЫВОД ---
    debug_print("Chat History from DB", history)

    if len(history) >= 2:
        print("✅ История обновлена корректно!")
    else:
        print("⚠️ История пуста или не обновилась.")


if __name__ == "__main__":
    test_full_flow()