import os
import logging
from dotenv import load_dotenv

# Проверка доступности библиотеки g4f
try:
    from g4f.client import Client
    GPT4_AVAILABLE = True
except ImportError:
    logging.warning("Библиотека g4f не установлена. Анализ GPT-4 будет отключен.")
    GPT4_AVAILABLE = False

# Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_config():
    """
    Загружает переменные окружения и возвращает их в виде словаря.
    """
    load_dotenv()
    config = {
        "IMAP_SERVER": os.getenv("IMAP_SERVER"),
        "EMAIL_USERNAME": os.getenv("EMAIL_USERNAME"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
    }

    # Собираем информацию о загруженных переменных
    loaded_vars = []
    missing_vars = []
    for key, value in config.items():
        if value is not None:
            loaded_vars.append(key)
        else:
            missing_vars.append(key)

    # Формируем одно сообщение для логов
    if missing_vars:
        logging.error(f"Переменные окружения не найдены: {', '.join(missing_vars)}")
        raise ValueError("Не все переменные окружения заданы.")
    else:
        logging.info(f"Загружены переменные окружения: {', '.join(loaded_vars)}")

    return config