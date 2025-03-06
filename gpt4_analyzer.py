import logging
import asyncio
from g4f.client import Client

class GPT4Analyzer:
    def __init__(self):
        self.client = Client()

    async def analyze_text(self, text, prompt):
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
            #logging.info(f"GPT-4 analysis successful: {result}")
            return result
        except Exception as e:
            logging.error(f"Ошибка при анализе текста с помощью GPT-4: {str(e)}")
            return "Не удалось получить анализ от GPT-4."