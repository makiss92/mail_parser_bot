import aiohttp
import logging
import os
import asyncio
from aiohttp_socks import ProxyConnector


class TelegramHandler:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._proxy_logged = False

        proxy_url = os.getenv("SOCKS5_PROXY")

        if proxy_url:
            if not self._proxy_logged:
                logging.info("Используется SOCKS5 прокси")
                self._proxy_logged = True
            self.connector = ProxyConnector.from_url(proxy_url)
        else:
            logging.info("Прокси не используется")
            self.connector = None


    async def send_message(self, subject, message):
        try:
            safe_subject = self.escape_html(subject)
            formatted = f"<b>Тема:</b> {safe_subject}\n\n{message}"
            parts = self.split_message(formatted)

            for part in parts:
                success = await self._send_with_retry(part)

                if not success:
                    logging.error("Не удалось отправить сообщение в Telegram")
                    return False

            return True

        except Exception as e:
            logging.error(f"Ошибка Telegram: {e}")
            return False


    async def _send_with_retry(self, text, retries=3):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        for attempt in range(1, retries + 1):
            try:
                connector = ProxyConnector.from_url(os.getenv("SOCKS5_PROXY")) if os.getenv("SOCKS5_PROXY") else None

                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.post(url, json=payload, timeout=10) as resp:
                        data = await resp.json()

                        if data.get("ok"):
                            logging.info("Сообщение отправлено")
                            return True
                        else:
                            logging.error(f"Telegram error: {data}")

            except Exception as e:
                logging.warning(f"Telegram retry {attempt}: {e}")

            await asyncio.sleep(1)

        return False


    def split_message(self, message, max_length=4096):
        return [message[i:i + max_length] for i in range(0, len(message), max_length)]


    def escape_markdown(self, text):
        escape_chars = "_*[]()~>#+-=|{}.!"
        return "".join(f"\\{c}" if c in escape_chars else c for c in text)


    def escape_html(self, text):
        if not text:
            return ""

        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )