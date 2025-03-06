import os
import logging
from dotenv import load_dotenv

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

    # Считаем количество загруженных переменных
    loaded_count = sum(1 for value in config.values() if value is not None)
    total_count = len(config)

    if loaded_count == total_count:
        logging.info(f"Загружены все {loaded_count} переменных окружения.")
    else:
        missing_vars = [key for key, value in config.items() if value is None]
        logging.error(f"Переменные окружения не найдены: {', '.join(missing_vars)}")
        raise ValueError("Не все переменные окружения заданы.")

    return config