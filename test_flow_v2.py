import requests
import json
import time
import sys
import uuid

# URL локально запущенного сервиса
BASE_URL = "http://localhost:8000"


# --- Цвета для консоли ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_section(title):
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}🛠  SCENARIO: {title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}")


# --- Debug Клиент (Выводит всё, что входит и выходит) ---
class DebugClient:
    def _log(self, method, url, payload=None, response=None, duration=0):
        print(f"\n{Colors.CYAN}--- HTTP REQUEST ---{Colors.ENDC}")
        print(f"{Colors.BOLD}{method} {url}{Colors.ENDC}")

        if payload:
            print(f"{Colors.BLUE}Payload (Input):{Colors.ENDC}")
            print(json.dumps(payload, indent=2, ensure_ascii=False))

        print(f"\n{Colors.CYAN}--- HTTP RESPONSE ({response.status_code}) [{duration:.2f}s] ---{Colors.ENDC}")
        try:
            resp_json = response.json()
            # Ограничим вывод слишком длинных полей для читаемости
            preview_json = json.loads(json.dumps(resp_json))
            if 'task_data' in preview_json and preview_json['task_data']:
                td = preview_json['task_data']
                if 'description' in td and len(td['description']) > 200:
                    td['description'] = td['description'][:200] + "... [TRUNCATED]"

            print(f"{Colors.GREEN}Body (Output):{Colors.ENDC}")
            print(json.dumps(preview_json, indent=2, ensure_ascii=False))
            return resp_json
        except:
            print(f"{Colors.WARNING}Body (Raw):{Colors.ENDC} {response.text}")
            return response.text

    def post(self, endpoint, data, expected_status=200):
        url = f"{BASE_URL}{endpoint}"
        start = time.time()
        resp = requests.post(url, json=data)
        duration = time.time() - start

        json_data = self._log("POST", url, data, resp, duration)

        if resp.status_code != expected_status:
            print(f"{Colors.FAIL}❌ ОЖИДАЛСЯ СТАТУС {expected_status}, ПОЛУЧЕН {resp.status_code}{Colors.ENDC}")
        return resp.status_code, json_data

    def get(self, endpoint, expected_status=200):
        url = f"{BASE_URL}{endpoint}"
        start = time.time()
        resp = requests.get(url)
        duration = time.time() - start

        json_data = self._log("GET", url, None, resp, duration)

        if resp.status_code != expected_status:
            print(f"{Colors.FAIL}❌ ОЖИДАЛСЯ СТАТУС {expected_status}, ПОЛУЧЕН {resp.status_code}{Colors.ENDC}")
        return resp.status_code, json_data


client = DebugClient()


def run_tests():
    # Хранилище ID для дальнейших тестов
    created_tasks = {}

    # ==================================================================================
    # СЦЕНАРИЙ 1: Генерация задачи через AI (Старый метод)
    # ==================================================================================
    print_section("1. AI Генерация задачи (по теме)")

    topic = "Merge Sort implementation"
    level = "junior"

    status, gen_data = client.post("/generate_task", {"level": level, "topic": topic})

    if status == 200 and gen_data.get("task_id"):
        task_id = gen_data["task_id"]
        created_tasks['ai_task'] = task_id
        print(f"{Colors.BOLD}✅ AI Task ID получен: {task_id}{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}CRITICAL: Не удалось сгенерировать задачу AI.{Colors.ENDC}")

    # ==================================================================================
    # СЦЕНАРИЙ 2: Создание задачи из текста HR (НОВЫЙ МЕТОД)
    # ==================================================================================
    print_section("2. Создание задачи из сырого текста HR (Refinement)")

    raw_hr_input = """
    Задача про анаграммы. Даны две строки s и t. 
    Нужно вернуть true, если t является анаграммой s, и false иначе.
    Пример: s = "anagram", t = "nagaram" -> true.
    Ограничения: строки состоят только из маленьких английских букв.
    """

    status, custom_data = client.post("/create_custom_task", {
        "level": "junior",
        "raw_text": raw_hr_input
    })

    if status == 200 and custom_data.get("task_id"):
        hr_task_id = custom_data["task_id"]
        created_tasks['hr_task'] = hr_task_id

        task_data = custom_data.get('task_data', {})
        print(f"{Colors.BOLD}✅ HR Task ID получен: {hr_task_id}{Colors.ENDC}")
        print(f"Заголовок: {task_data.get('title')}")
        print(f"Функция: {task_data.get('function_name')}")
        print(f"Тестов сгенерировано: {len(task_data.get('test_cases', []))}")
    else:
        print(f"{Colors.FAIL}CRITICAL: Не удалось создать задачу HR.{Colors.ENDC}")

    # ==================================================================================
    # СЦЕНАРИЙ 3: Диалог и История (Проверяем на AI задаче)
    # ==================================================================================
    if 'ai_task' in created_tasks:
        t_id = created_tasks['ai_task']
        print_section("3. Диалог и История (Context Window)")

        # Шаг 1: Юзер задает вопрос
        print(f"{Colors.BOLD}>>> Шаг 1: Первый вопрос юзера{Colors.ENDC}")
        client.post("/hint", {
            "task_id": t_id,
            "user_code": "def solve(): pass",
            "user_message": "С чего начать сортировку слиянием?"
        })

        # Шаг 2: Юзер задает второй вопрос
        print(f"{Colors.BOLD}>>> Шаг 2: Второй вопрос юзера (контекстный){Colors.ENDC}")
        client.post("/hint", {
            "task_id": t_id,
            "user_code": "def solve(): pass",
            "user_message": "А как делить массив?"
        })

        # Шаг 3: Проверяем историю
        print(f"{Colors.BOLD}>>> Шаг 3: Проверка накопления истории в БД{Colors.ENDC}")
        _, check_res = client.get(f"/task/{t_id}")
        history = check_res.get("chat_history", [])

        print(f"Сообщений в истории: {len(history)}")
        for i, msg in enumerate(history):
            print(f"   [{i}] {msg['role']}: {msg['content'][:50]}...")

        if len(history) >= 4:
            print(f"{Colors.BOLD}✅ История работает!{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ Ошибка истории.{Colors.ENDC}")

    # ==================================================================================
    # СЦЕНАРИЙ 4: Поиск (Проверяем, ищутся ли ОБЕ задачи)
    # ==================================================================================
    print_section("4. Проверка поиска (PGVector)")

    # Ищем сортировку (AI задача)
    print(f"{Colors.BOLD}>>> Поиск AI задачи (сортировка){Colors.ENDC}")
    _, search_sort = client.post("/search_tasks", {"query": "sorting algorithm", "level": "junior"})

    # Ищем анаграммы (HR задача)
    print(f"{Colors.BOLD}>>> Поиск HR задачи (анаграммы){Colors.ENDC}")
    _, search_anagram = client.post("/search_tasks", {
        "query": "проверка анаграмм",  # <-- Ищем анаграммы
        "level": "junior",
        "limit": 2
    })
    # Проверка ID
    found_ai = False
    if 'ai_task' in created_tasks:
        found_ai = any(item['task_id'] == created_tasks['ai_task'] for item in search_sort)

    found_hr = False
    if 'hr_task' in created_tasks:
        found_hr = any(item['task_id'] == created_tasks['hr_task'] for item in search_anagram)

    if found_ai:
        print(f"{Colors.BOLD}✅ AI задача найдена в поиске.{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠️ AI задача не в топе поиска.{Colors.ENDC}")

    if found_hr:
        print(f"{Colors.BOLD}✅ HR задача найдена в поиске.{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠️ HR задача не в топе поиска.{Colors.ENDC}")

    # ==================================================================================
    # СЦЕНАРИЙ 5: Тестирование ошибок
    # ==================================================================================
    print_section("5. Тестирование ошибок (Negative Cases)")

    # 1. Несуществующий ID
    fake_id = str(uuid.uuid4())
    print(f"{Colors.BOLD}>>> Тест: Запрос несуществующей задачи (ожидаем 404){Colors.ENDC}")
    client.get(f"/task/{fake_id}", expected_status=404)

    # 2. Невалидный уровень
    print(f"{Colors.BOLD}>>> Тест: Генерация с плохим уровнем (ожидаем 400){Colors.ENDC}")
    client.post("/create_custom_task", {"level": "god_mode", "raw_text": "Task"}, expected_status=400)


if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\nТест прерван пользователем.")
    except Exception as e:
        print(f"\n{Colors.FAIL}CRITICAL ERROR: {e}{Colors.ENDC}")