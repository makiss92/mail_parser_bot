import asyncio
import json
import logging
from email_handler import EmailHandler
from telegram_handler import TelegramHandler
from gpt4_analyzer import GPT4Analyzer
from config import load_config, GPT4_AVAILABLE  # Импортируем переменную

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

async def fetch_unread_emails(username, password, imap_server, bot_token, chat_id):
    email_handler = EmailHandler(imap_server, username, password)
    telegram_handler = TelegramHandler(bot_token, chat_id)
    processed_emails = await load_processed_emails()

    emails = email_handler.fetch_unread_emails()
    for e_id, subject, text in emails:
        if e_id in processed_emails:
            logging.info(f"Email {e_id} already processed. Skipping.")
            continue

        # Анализируем текст письма
        prompt = "Проанализируй текст письма, напиши рекомендации!"
        analysis_result = await GPT4Analyzer().analyze_text(text, prompt)

        # Отправляем результат в Telegram
        await telegram_handler.send_message(subject, analysis_result)
        await save_processed_email(e_id)
        logging.info(f"Email {e_id} processed and sent to Telegram.")

async def main():
    logging.info("Starting the script...")
    config = load_config()

    IMAP_SERVER = config["IMAP_SERVER"]
    EMAIL_USERNAME = config["EMAIL_USERNAME"]
    EMAIL_PASSWORD = config["EMAIL_PASSWORD"]
    TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
    TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]

    while True:
        try:
            await fetch_unread_emails(EMAIL_USERNAME, EMAIL_PASSWORD, IMAP_SERVER, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"Critical error: {str(e)}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())