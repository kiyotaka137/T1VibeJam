import re


def clean_query(text: str) -> str:
    """
    Удаляет блоки <think>...</think> и любые их вариации.
    Также чистит пустые строки.
    """
    # Удаляем <think>...</think>
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # Убираем пробелы и пустые строки
    return text.strip()
