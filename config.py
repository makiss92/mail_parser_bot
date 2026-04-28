import os
import logging
from dotenv import load_dotenv

# ------------------------
# 🔍 Проверка g4f
# ------------------------

try:
    from g4f.client import Client
    GPT4_AVAILABLE = True
except ImportError:
    logging.warning("Библиотека g4f не установлена. Анализ GPT отключен.")
    GPT4_AVAILABLE = False

# ------------------------
# 🪵 Логи
# ------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ------------------------
# 📄 Загрузка prompt
# ------------------------

def load_prompt():
    prompt_value = os.getenv("PROMPT_TEXT", "")

    if prompt_value.endswith(".txt"):
        if os.path.exists(prompt_value):
            try:
                with open(prompt_value, "r", encoding="utf-8") as f:
                    content = f.read().strip()

                    logging.info(f"Промпт загружен ({len(content)} символов)")

                    return content
            except Exception as e:
                logging.error(f"Ошибка чтения промпт файла: {e}")
                return ""
        else:
            logging.error(f"Файл промпта не найден: {prompt_value}")
            return ""

    logging.info("Промпт загружен из ENV переменной")
    return prompt_value.strip()

# ------------------------
# ⚙️ Основной конфиг
# ------------------------

def load_config():
    load_dotenv()

    prompt_text = load_prompt()

    config = {
        "IMAP_SERVER": os.getenv("IMAP_SERVER"),
        "EMAIL_USERNAME": os.getenv("EMAIL_USERNAME"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
        "EMAIL_POLL_INTERVAL": os.getenv("EMAIL_POLL_INTERVAL"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
        "PROMPT_TEXT": prompt_text,
        "GPT_MODEL": os.getenv("GPT_MODEL", "gpt-4o-mini"),
        "DEBUG": os.getenv("DEBUG", "false").lower() == "true",
    }

    if config["DEBUG"]:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info(f"DEBUG режим: {'ON' if config['DEBUG'] else 'OFF'}")

    required = [
        "IMAP_SERVER",
        "EMAIL_USERNAME",
        "EMAIL_PASSWORD",
        "EMAIL_POLL_INTERVAL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID"
    ]

    missing = [k for k in required if not config.get(k)]

    if missing:
        logging.error(f"Не найдены переменные: {', '.join(missing)}")
        raise ValueError("Не все переменные окружения заданы.")

    if not prompt_text:
        logging.warning("Промпт пустой, будет использоваться fallback логика")

    logging.info("Конфиг успешно загружен")

    return config