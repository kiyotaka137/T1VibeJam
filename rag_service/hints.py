# rag_service/hints.py
import re
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from .config import settings
from .prompts_const import HINT_SYSTEM_PROMPT, HINT_USER_TEMPLATE
from .db_storage import get_task_context_for_hint, update_chat_history


class HintResponseData(BaseModel):
    hint: str = Field(description="Текст ответа")


class HintGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.BASE_URL,
            api_key=settings.API_KEY,
            model=settings.HINT_MODEL,
            temperature=0.5,
        )
        self.parser = JsonOutputParser(pydantic_object=HintResponseData)

    def _clean(self, text: str) -> str:
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        match = re.search(r'```json\s*(.*?)\s*```', text, flags=re.DOTALL)
        if match: return match.group(1)
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1: return text[start: end + 1]
        return text

    async def process_hint(self, task_id: str, user_code: str, user_message: str) -> str:
        # 1. Достаем контекст из БД
        ctx = await get_task_context_for_hint(task_id)
        if not ctx: return "Ошибка: Задача не найдена."

        description = ctx["description"]
        history = ctx["chat_history"]
        level = ctx["level"]

        # 2. Добавляем сообщение юзера
        history.append({"role": "user", "content": user_message})

        # 3. Генерируем
        prompt = ChatPromptTemplate.from_messages([("system", HINT_SYSTEM_PROMPT), ("user", HINT_USER_TEMPLATE)])
        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history])

        try:
            formatted = await prompt.ainvoke({
                "task_description": description, "user_code": user_code,
                "chat_history": history_str, "format_instructions": self.parser.get_format_instructions()
            })
            resp = await self.llm.ainvoke(formatted)
            parsed = self.parser.parse(self._clean(resp.content))
            hint_text = parsed.get("hint", "Ошибка.")
        except Exception:
            hint_text = "Не удалось сгенерировать подсказку."

        # 4. Сохраняем ответ и историю
        history.append({"role": "assistant", "content": hint_text})
        await update_chat_history(level, task_id, history, hint_text)

        return hint_text


hint_service = HintGenerator()