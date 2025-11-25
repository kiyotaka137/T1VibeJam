# src/services/task_generator.py
import re
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from src.prompts.task_prompts import TASK_GEN_SYSTEM_PROMPT, TASK_GEN_USER_TEMPLATE


# Описываем схему выхода
class TasksResponse(BaseModel):
    task1: str = Field(description="Полный текст условия первой задачи (на русском)")
    task2: str = Field(description="Полный текст условия второй задачи (на русском)")
    task3: str = Field(description="Полный текст условия третьей задачи (на русском)")


class TaskGenerator:
    def __init__(self):
        # Инициализация клиента
        # reasoning включен по умолчанию, если не добавить /no_think
        self.llm = ChatOpenAI(
            base_url="YOUR_URL",  # [cite: 3]
            api_key="YOUR_KEY",
            model="qwen3-32b-awq",  # [cite: 6]
            temperature=0.6,  # Чуть ниже для стабильности JSON, но достаточно для креатива
            max_tokens=3000,  # Запас для рассуждений + JSON
        )

        self.parser = JsonOutputParser(pydantic_object=TasksResponse)

    def _clean_response_content(self, raw_content: str) -> str:
        """
        Очищает ответ от reasoning-блоков и markdown-оберток,
        чтобы достать чистый JSON.
        """
        # 1. Удаляем теги <think>...</think> если они есть (DeepSeek/Qwen style)
        # re.DOTALL позволяет точке . матчить переносы строк
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL)

        # 2. Иногда модель пишет мысли просто текстом, а JSON кладет в ```json ... ```
        # Попробуем найти контент внутри ```json ... ```
        json_match = re.search(r'```json\s*(.*?)\s*```', clean_content, flags=re.DOTALL)
        if json_match:
            return json_match.group(1)

        # 3. Если блоков кода нет, ищем первую { и последнюю }
        json_start = clean_content.find('{')
        json_end = clean_content.rfind('}')

        if json_start != -1 and json_end != -1:
            return clean_content[json_start: json_end + 1]

        return clean_content

    async def generate_tasks(self, grade: str, topic: str):
        # Собираем промпт из наших файлов
        prompt = ChatPromptTemplate.from_messages([
            ("system", TASK_GEN_SYSTEM_PROMPT),
            ("user", TASK_GEN_USER_TEMPLATE),
        ])

        # Формируем цепочку вручную, чтобы вклиниться с очисткой
        # chain = prompt | self.llm
        # Мы не подключаем parser сразу в pipe, потому что нам надо почистить "мысли"

        formatted_prompt = await prompt.ainvoke({
            "grade": grade,
            "topic": topic,
            "format_instructions": self.parser.get_format_instructions()
        })

        # Вызов модели
        response = await self.llm.ainvoke(formatted_prompt)
        raw_text = response.content

        # Логируем рассуждения (если нужно для отладки), но пользователю отдаем JSON
        # print(f"Raw response with reasoning: {raw_text[:200]}...")

        # Очистка и парсинг
        cleaned_json_str = self._clean_response_content(raw_text)

        try:
            parsed_data = self.parser.parse(cleaned_json_str)
            return parsed_data
        except Exception as e:
            # Fallback: возвращаем сырой текст ошибки или пробуем восстановить
            print(f"JSON Parsing Error: {e}")
            print(f"Cleaned string was: {cleaned_json_str}")
            return {"error": "Failed to parse tasks", "raw_output": cleaned_json_str}