import asyncio
import json
import logging
from email_handler import EmailHandler
from telegram_handler import TelegramHandler
from gpt4_analyzer import GPT4Analyzer
from config import load_config, GPT4_AVAILABLE

CONFIG_FILE = "processed_emails.json"

async def load_processed_emails():
    try:
        with open(CONFIG_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

async def save_processed_email(email_id):
    processed = await load_processed_emails()
    processed.add(email_id)
    with open(CONFIG_FILE, "w") as f:
        json.dump(list(processed), f)

def should_exclude_email(subject, text):
    """
    Проверяет, нужно ли исключить письмо из обработки.
    """
    excluded_keywords = [
        "Vobile Compliance",
        "Notice of Claimed Infringement",
        "Vobile, Inc."
    ]

    # Проверяем тему и текст письма
    for keyword in excluded_keywords:
        if keyword.lower() in subject.lower() or keyword.lower() in text.lower():
            return True
    return False

async def fetch_unread_emails(username, password, imap_server, bot_token, chat_id, prompt_text):
    email_handler = EmailHandler(imap_server, username, password)
    telegram_handler = TelegramHandler(bot_token, chat_id)
    processed_emails = await load_processed_emails()

    emails = email_handler.fetch_unread_emails()
    for e_id, subject, text in emails:
        if e_id in processed_emails:
            logging.info(f"Письмо {e_id} уже обработано. Пропускаем.")
            continue

        # Проверяем, нужно ли исключить письмо
        if should_exclude_email(subject, text):
            logging.info(f"Письмо {e_id} исключено из обработки. Тема: {subject}")
            continue

        # Анализируем текст письма с использованием заданного запроса
        analysis_result = await GPT4Analyzer().analyze_text(text, prompt_text)

        # Отправляем результат в Telegram
        await telegram_handler.send_message(subject, analysis_result)
        await save_processed_email(e_id)
        logging.info(f"Письмо {e_id} обработано и отправлено в Telegram.")

async def main():
    logging.info("Запуск скрипта...")
    config = load_config()

    IMAP_SERVER = config["IMAP_SERVER"]
    EMAIL_USERNAME = config["EMAIL_USERNAME"]
    EMAIL_PASSWORD = config["EMAIL_PASSWORD"]
    TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
    TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]
    PROMPT_TEXT = config["PROMPT_TEXT"]

    while True:
        try:
            await fetch_unread_emails(EMAIL_USERNAME, EMAIL_PASSWORD, IMAP_SERVER, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PROMPT_TEXT)
            await asyncio.sleep(300)  # Интервал проверки: 5 минут (300 секунд)
        except Exception as e:
            logging.error(f"Критическая ошибка: {str(e)}")
            await asyncio.sleep(300)  # Интервал проверки: 5 минут (300 секунд)

if __name__ == "__main__":
    asyncio.run(main())