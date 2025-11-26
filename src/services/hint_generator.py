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
            # Используем IP, чтобы не было DNS ошибок (как в инструкции)
            base_url="http://45.145.191.148:4000/v1",
            api_key="sk-x8YPQ4vYbpEJHQlc5faICA",
            model="qwen3-32b-awq",  # Обычный универсальный Квен
            temperature=0.5,
            max_tokens=1500,
            request_timeout=60,
        )
        self.parser = JsonOutputParser(pydantic_object=HintResponse)

    def _clean_response_content(self, raw_content: str) -> str:
        """Очистка ответа от reasoning (на случай, если модель все же решит подумать) и markdown."""
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL)

        json_match = re.search(r'```json\s*(.*?)\s*```', clean_content, flags=re.DOTALL)
        if json_match:
            return json_match.group(1)

        json_start = clean_content.find('{')
        json_end = clean_content.rfind('}')
        if json_start != -1 and json_end != -1:
            return clean_content[json_start: json_end + 1]

        return clean_content

    async def generate_hint(self, task_description: str, user_code: str, chat_history: str):
        """
        Теперь принимаем еще и task_description
        """

        # 1. Сборка промпта
        prompt = ChatPromptTemplate.from_messages([
            ("system", HINT_SYSTEM_PROMPT),
            ("user", HINT_USER_TEMPLATE),
        ])

        formatted_prompt = await prompt.ainvoke({
            "task_description": task_description,  # <-- Передаем условие
            "user_code": user_code,
            "chat_history": chat_history,
            "format_instructions": self.parser.get_format_instructions()
        })

        # 2. Вызов модели (System Prompt содержит /no_think)
        response = await self.llm.ainvoke(formatted_prompt)
        raw_text = response.content

        # 3. Очистка и парсинг
        cleaned_json_str = self._clean_response_content(raw_text)

        try:
            parsed_data = self.parser.parse(cleaned_json_str)
            return parsed_data
        except Exception as e:
            print(f"Error parsing hint JSON: {e}")
            return {
                "hint": "Произошла ошибка при генерации подсказки. Попробуйте еще раз."
            }