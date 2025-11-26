import asyncio
import json
import sys
import os

sys.path.append(os.getcwd())

from src.services.hint_generator import HintGenerator


def print_header(text):
    print(f"\n\033[96m{'=' * 60}\n{text}\n{'=' * 60}\033[0m")


async def test_scenario_2_hints():
    print_header("СЦЕНАРИЙ 2: ДИАЛОГ С МЕНТОРОМ (С УСЛОВИЕМ, БЕЗ THINKING)")

    # 1. Условие задачи (которое теперь обязательно)
    task_desc = """
    Задача: Сумма двух чисел (Two Sum).
    Дан массив целых чисел nums и целое число target.
    Верните индексы двух чисел таких, что их сумма равна target.
    Предполагается, что существует ровно одно решение.
    """

    # 2. Код пользователя (с ошибкой в логике)
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
    # Теперь передаем 3 аргумента
    result = await generator.generate_hint(task_desc, bad_code, chat_history)

    print("\n\033[95m[DEBUG] ПОЛНЫЙ ОТВЕТ LLM (JSON):\033[0m")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("-" * 60)


async def main():
    await test_scenario_2_hints()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрервано.")