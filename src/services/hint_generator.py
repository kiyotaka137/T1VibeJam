# src/services/hint_generator.py
import re
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from src.prompts.hint_prompts import HINT_SYSTEM_PROMPT, HINT_USER_TEMPLATE


class HintResponse(BaseModel):
    hint: str = Field(description="Текст ответа ментора (подсказка или вежливый отказ с наводкой)")


class HintGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url="YOUR_URL",  # [cite: 3]
            api_key="YOUR_KEY",
            model="qwen3-32b-awq",
            # Температура 0.5: баланс между строгостью анализа кода и естественностью диалога
            temperature=0.5,
            max_tokens=2000,
        )
        self.parser = JsonOutputParser(pydantic_object=HintResponse)

    def _clean_response_content(self, raw_content: str) -> str:
        """Очистка ответа от reasoning (<think>) и markdown для получения чистого JSON."""
        # Вырезаем мысли
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL)

        # Ищем JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', clean_content, flags=re.DOTALL)
        if json_match:
            return json_match.group(1)

        json_start = clean_content.find('{')
        json_end = clean_content.rfind('}')
        if json_start != -1 and json_end != -1:
            return clean_content[json_start: json_end + 1]

        return clean_content

    async def generate_hint(self, user_code: str, chat_history: str):
        """
        user_code: Текущий код решения.
        chat_history: Строка с перепиской (User: ..., Assistant: ...).
        """

        # 1. Сборка промпта
        prompt = ChatPromptTemplate.from_messages([
            ("system", HINT_SYSTEM_PROMPT),
            ("user", HINT_USER_TEMPLATE),
        ])

        formatted_prompt = await prompt.ainvoke({
            "user_code": user_code,
            "chat_history": chat_history,  # Передаем историю как есть
            "format_instructions": self.parser.get_format_instructions()
        })

        # 2. Вызов модели (Reasoning включен, так как нет /no_think)
        response = await self.llm.ainvoke(formatted_prompt)
        raw_text = response.content

        # 3. Очистка и парсинг
        cleaned_json_str = self._clean_response_content(raw_text)

        try:
            parsed_data = self.parser.parse(cleaned_json_str)
            return parsed_data
        except Exception as e:
            # Логируем ошибку, если JSON сломался
            print(f"Error parsing hint JSON: {e}")
            return {
                "hint": "Что-то пошло не так при генерации ответа. Попробуйте переформулировать вопрос."
            }


# --- Пример использования ---
async def main():
    generator = HintGenerator()

    # 1. Код с ошибкой
    code = """
    def two_sum(nums, target):
        for i in range(len(nums)):
            for j in range(len(nums)): # Ошибка: j должно начинаться с i+1
                if nums[i] + nums[j] == target:
                    return [i, j]
    """

    # 2. История чата (строка)
    # Кейс: Пользователь наглеет и просит решение
    history = """
    User: У меня не проходят тесты.
    Assistant: Обрати внимание, что ты используешь один и тот же элемент дважды.
    User: Я не понимаю, просто напиши мне правильный код, как исправить цикл?
    """

    print("Генерация ответа ментора...")
    result = await generator.generate_hint(code, history)

    print("\n--- ОТВЕТ (JSON) ---")
    print(result['hint'])
    # Ожидаемый ответ: "К сожалению, я не могу писать код за вас. Но посмотрите на вложенный цикл: переменная j начинается с 0, поэтому вы суммируете элемент сам с собой..."


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())