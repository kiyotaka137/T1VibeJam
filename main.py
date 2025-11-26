import asyncio
import json
import sys
import os

# Добавляем текущую директорию в путь, чтобы Python видел папку src
sys.path.append(os.getcwd())

from src.services.task_generator import TaskGenerator
from src.services.hint_generator import HintGenerator


def print_header(text):
    print(f"\n\033[96m{'=' * 60}\n{text}\n{'=' * 60}\033[0m")


def print_debug_json(data):
    print("\n\033[95m[DEBUG] ПОЛНЫЙ ОТВЕТ LLM (JSON):\033[0m")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("-" * 60)


async def test_scenario_1_tasks():
    print_header("СЦЕНАРИЙ 1: ГЕНЕРАЦИЯ ЗАДАЧИ (CODER MODEL)")

    # Входные параметры
    grade = "Junior"
    topic = "Массивы (Arrays)"

    print(f"Запрос: Грейд -> {grade}, Тема -> {topic}")
    print("Генерирую задачу (это может занять 10-30 сек)...")

    generator = TaskGenerator()
    result = await generator.generate_tasks(grade, topic)

    # 1. Выводим полный JSON (для дебага)
    print_debug_json(result)

    # 2. Выводим красиво для человека
    if "tasks" in result and result["tasks"]:
        task = result['tasks'][0]  # Берем единственную задачу

        print(f"\n\033[93mЗадача: {task.get('title', 'Без названия')}\033[0m")
        print(f"Функция: \033[1m{task.get('function_name', '???')}\033[0m")
        print(f"Описание: {task.get('description', '')[:100]}...")  # Обрезаем для краткости

        print("-" * 20)
        print("\033[94m🐍 Python Code Template:\033[0m")
        print(f"{task.get('initial_code_python', 'N/A')}")

        print("-" * 20)
        print("\033[96m⚙️ C++ Code Template:\033[0m")
        print(f"{task.get('initial_code_cpp', 'N/A')}")
        print("-" * 20)

        # Тесты
        tests = task.get('test_cases', [])
        if tests:
            t = tests[0]
            inp = t.get('input', 'N/A')
            out = t.get('output', 'N/A')
            print(f"Пример теста (всего {len(tests)}): Input={inp} -> Output={out}")
    else:
        print("Ошибка или пустой результат:", result)


async def test_scenario_2_hints():
    print_header("СЦЕНАРИЙ 2: ДИАЛОГ С МЕНТОРОМ (С УСЛОВИЕМ)")

    # 1. Условие задачи
    task_desc = """
    Задача: Сумма двух чисел (Two Sum).
    Дан массив целых чисел nums и целое число target.
    Верните индексы двух чисел таких, что их сумма равна target.
    Предполагается, что существует ровно одно решение.
    """

    # 2. Код пользователя (с логической ошибкой во вложенном цикле)
    bad_code = """
    def two_sum(nums, target):
        for i in range(len(nums)):
            for j in range(len(nums)): # Ошибка: j должно начинаться с i+1
                if nums[i] + nums[j] == target:
                    return [i, j]
    """

    # 3. История чата
    chat_history = """
    User: Почему мой код не проходит тесты?
    Assistant: Вы используете один и тот же элемент дважды, так как внутренний цикл начинается с 0.
    User: Ну и что? Напиши мне исправленный цикл, я не понимаю.
    """

    print("Входные данные:")
    print(f"Task: {task_desc.strip()[:50]}...")
    print(f"Code Length: {len(bad_code)} chars")
    print("Генерирую подсказку...")

    generator = HintGenerator()

    # Вызов генератора подсказок
    result = await generator.generate_hint(task_desc, bad_code, chat_history)

    # Вывод полного JSON ответа
    print_debug_json(result)


async def main():
    # Запускаем тесты последовательно
    await test_scenario_1_tasks()
    await test_scenario_2_hints()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
    except Exception as e:
        print(f"\n[ОШИБКА]: {e}")