import asyncio
import json
import sys
import os

# Добавляем текущую директорию в путь поиска модулей,
# чтобы Python видел папку src
sys.path.append(os.getcwd())

from src.services.task_generator import TaskGenerator
from src.services.hint_generator import HintGenerator


# Простая функция для цветного вывода в терминал
def print_header(text):
    print(f"\n\033[96m{'=' * 60}\n{text}\n{'=' * 60}\033[0m")


def print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


async def test_scenario_1_tasks():
    print_header("СЦЕНАРИЙ 1: ГЕНЕРАЦИЯ ЗАДАЧ")

    # Входные данные
    grade = "Middle"
    topic = "Бинарный поиск (Binary Search)"

    print(f"Запрос: Грейд -> {grade}, Тема -> {topic}")
    print("Генерирую задачи (подождите 5-10 сек)...")

    generator = TaskGenerator()
    result = await generator.generate_tasks(grade, topic)

    print("\n\033[92m[УСПЕХ] Ответ от LLM:\033[0m")
    print_json(result)


async def test_scenario_2_hints():
    print_header("СЦЕНАРИЙ 2: ДИАЛОГ С ПОДСКАЗКАМИ")

    # 1. Плохой код пользователя (бесконечный цикл в бинпоиске)
    bad_code = """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = left # ОШИБКА: Забыл +1, будет бесконечный цикл
        else:
            right = mid - 1
    return -1
    """

    # 2. История чата (имитация диалога)
    # Пользователь пытается выпросить код решения
    chat_history = """
User: У меня код зависает и не выдает ответ. В чем дело?
Assistant: Похоже, у вас проблема с условием выхода из цикла или обновлением границ.
User: Я не понимаю. Просто напиши мне правильный код функции, я скопирую.
    """

    print("Входные данные:")
    print(f"--- Code ---\n{bad_code.strip()}\n")
    print(f"--- Chat History ---\n{chat_history.strip()}\n")
    print("Анализирую код и генерирую ответ (Thinking mode)...")

    generator = HintGenerator()
    result = await generator.generate_hint(bad_code, chat_history)

    print("\n\033[92m[УСПЕХ] Ответ от LLM (JSON):\033[0m")
    print_json(result)

    print(
        "\n\033[93mПримечание: Если модель сработала верно, она должна отказать в выдаче кода\nи дать наводку на строку 'left = left'.\033[0m")


async def main():
    # Запускаем тесты последовательно
    await test_scenario_1_tasks()
    await test_scenario_2_hints()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nТест прерван пользователем.")
    except Exception as e:
        print(f"\n\033[91m[ОШИБКА] Произошло исключение:\033[0m {e}")