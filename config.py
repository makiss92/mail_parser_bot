# config.py
import os
import logging
from dotenv import load_dotenv

# Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_config():
    load_dotenv()
    config = {
        "IMAP_SERVER": os.getenv("IMAP_SERVER"),
        "EMAIL_USERNAME": os.getenv("EMAIL_USERNAME"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
    }

    for key, value in config.items():
        if value is None:
            logging.error(f"Переменная окружения {key} не найдена!")
        else:
            logging.info(f"Переменная окружения {key} загружена.")

    if None in config.values():
        raise ValueError("Не все переменные окружения заданы.")

    return config