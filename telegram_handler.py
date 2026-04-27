import aiohttp
import logging
import os
import re

from aiohttp_socks import ProxyConnector


class TelegramHandler:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.proxy_url = os.getenv("SOCKS5_PROXY")

        if self.proxy_url:
            logging.info("Используется SOCKS5 прокси")
            self.connector = ProxyConnector.from_url(self.proxy_url)
        else:
            logging.info("Прокси не используется")
            self.connector = None

        self.timeout = aiohttp.ClientTimeout(total=15)

    # ------------------------
    # 🚀 ОСНОВНОЙ МЕТОД
    # ------------------------

    async def send_message(self, subject, message):
        try:
            message = self.normalize_text(message)
            message = self.format_message(message)

            subject = self.escape_html(subject)

            formatted_message = (
                f"🔐 <b>Тема:</b> {subject}\n"
                f"{'─' * 35}\n\n"
                f"{message}"
            )

            parts = self.split_message(formatted_message)

            for part in parts:
                try:
                    async with aiohttp.ClientSession(
                        connector=self.connector,
                        timeout=self.timeout
                    ) as session:

                        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                        payload = {
                            "chat_id": self.chat_id,
                            "text": part,
                            "parse_mode": "HTML"
                        }

                        async with session.post(url, json=payload) as response:
                            data = await response.json()

                            if data.get("ok"):
                                logging.info("Сообщение отправлено в Telegram.")
                            else:
                                logging.error(f"Ошибка Telegram: {data}")

                except Exception as e:
                    logging.error(f"Ошибка отправки части: {str(e)}")

            return True

        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения: {str(e)}")
            return False

    # ------------------------
    # 🧠 ФОРМАТИРОВАНИЕ
    # ------------------------

    def normalize_text(self, text: str) -> str:
        """Чистим мусор от LLM"""
        if not text:
            return text

        lines = text.splitlines()
        cleaned = []

        for line in lines:
            l = line.strip().lower()

            if any(x in l for x in [
                "it seems",
                "it appears",
                "you have received",
                "based on the information"
            ]):
                continue

            cleaned.append(line)

        return "\n".join(cleaned).strip()

    def format_message(self, text: str) -> str:
        """Красивый формат под Telegram"""

        text = self.escape_html(text)

        # 🔥 Заголовки
        text = re.sub(r"(?i)тип[:\-]", "<b>Тип:</b>", text)
        text = re.sub(r"(?i)классификация[:\-]", "<b>Классификация:</b>", text)
        text = re.sub(r"(?i)описание[:\-]", "<b>Описание:</b>", text)
        text = re.sub(r"(?i)объяснение[:\-]", "<b>Объяснение:</b>", text)
        text = re.sub(r"(?i)рекомендации[:\-]", "<b>Рекомендации:</b>", text)
        text = re.sub(r"(?i)действия[:\-]", "<b>Действия:</b>", text)

        # 🔥 IP адреса
        text = re.sub(
            r"\b(\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?)\b",
            r"<code>\1</code>",
            text
        )

        # 🔥 списки
        text = re.sub(r"^[\-\*]\s", "• ", text, flags=re.MULTILINE)

        # 🔥 переносы
        text = text.replace("\n\n", "\n")

        return text

    # ------------------------
    # 🧰 УТИЛИТЫ
    # ------------------------

    def split_message(self, message, max_length=4096):
        if len(message) <= max_length:
            return [message]

        parts = []
        while len(message) > 0:
            part = message[:max_length]
            parts.append(part)
            message = message[max_length:]

        return parts

    def escape_html(self, text):
        if not text:
            return text

        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )