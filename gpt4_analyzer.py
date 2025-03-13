import logging
import asyncio
from config import GPT4_AVAILABLE  # Импортируем переменную

class GPT4Analyzer:
    def __init__(self):
        if GPT4_AVAILABLE:
            from g4f.client import Client
            self.client = Client()
        else:
            self.client = None

    async def analyze_text(self, text, prompt):
        """
        Анализирует текст с использованием GPT-4.
        Если ответ приходит в формате JSON, извлекает текст из него.
        """
        if not GPT4_AVAILABLE:
            return "Анализ GPT-4 отключен. Установите библиотеку g4f."

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ]
            )
            result = response.choices[0].message.content

            # Проверяем, если ответ пришел в формате JSON
            if result.strip().startswith("data: {"):
                # Извлекаем текст из JSON
                result = " ".join(
                    line.split('"content":"')[1].split('"}')[0]
                    for line in result.strip().splitlines()
                    if '"content":"' in line
                )

            #logging.info(f"Анализ GPT-4 выполнен успешно: {result}")
            return result
        except Exception as e:
            logging.error(f"Ошибка при анализе текста с GPT-4: {str(e)}")
            return "Не удалось получить анализ от GPT-4."