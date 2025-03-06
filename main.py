import asyncio
import json
import logging
from config import load_config
from email_handler import EmailHandler
from telegram_handler import TelegramHandler
from gpt4_analyzer import GPT4Analyzer

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

async def main():
    logging.info("Запускаем скрипт...")
    config = load_config()

    email_handler = EmailHandler(config["IMAP_SERVER"], config["EMAIL_USERNAME"], config["EMAIL_PASSWORD"])
    telegram_handler = TelegramHandler(config["TELEGRAM_BOT_TOKEN"], config["TELEGRAM_CHAT_ID"])
    gpt4_analyzer = GPT4Analyzer()

    prompt = "Проанализируй текст письма, напиши рекомендации на Русском языке!"

    while True:
        try:
            emails = email_handler.fetch_unread_emails()
            processed_emails = await load_processed_emails()

            for e_id, subject, text in emails:
                if e_id in processed_emails:
                    logging.info(f"Это письмо под №:{e_id} уже обработано. Пропускаем.")
                    continue

                analysis_result = await gpt4_analyzer.analyze_text(text, prompt)
                await telegram_handler.send_message(subject, analysis_result)
                await save_processed_email(e_id)
                logging.info(f"Номер письма №:{e_id} обработан и отправлен в Telegram.")

            await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"Критическая ошибка: {str(e)}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())