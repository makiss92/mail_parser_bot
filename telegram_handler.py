import aiohttp
import logging

class TelegramHandler:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id

    async def send_message(self, subject, message):
        try:
            logging.info(f"Попытка отправить сообщение на адрес chat_id: {self.chat_id}")
            subject = self.escape_markdown(subject)
            message = self.escape_markdown(message)
            formatted_message = f"**Тема:** {subject}\n\n{message}"

            message_parts = self.split_message(formatted_message)

            async with aiohttp.ClientSession() as session:
                for part in message_parts:
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    payload = {
                        "chat_id": self.chat_id,
                        "text": part,
                        "parse_mode": "MarkdownV2"
                    }
                    async with session.post(url, json=payload) as response:
                        response_data = await response.json()
                        if response_data.get("ok"):
                            logging.info(f"Часть сообщения успешно отправлена.")
                        else:
                            logging.error(f"Не удалось отправить часть сообщения.")
                            logging.error(f"Ответ от API: {response_data}")

            return True
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения в Telegram: {str(e)}")
            return False

    def split_message(self, message, max_length=4096):
        if len(message) <= max_length:
            return [message]
        parts = []
        while len(message) > 0:
            part = message[:max_length]
            parts.append(part)
            message = message[max_length:]
        logging.info(f"Сообщение разделено на {len(parts)} части.")
        return parts

    def escape_markdown(self, text):
        escape_chars = "_*[]()~>#+-=|{}.!"
        escaped_text = "".join(f"\\{char}" if char in escape_chars else char for char in text)

        if escaped_text.count("**") % 2 != 0:
            escaped_text = escaped_text.replace("**", "*")
        if escaped_text.count("__") % 2 != 0:
            escaped_text = escaped_text.replace("__", "_")
        if escaped_text.count("```") % 2 != 0:
            escaped_text = escaped_text.replace("```", "`")

        #logging.info(f"Экранированный текст: {escaped_text}")
        return escaped_text