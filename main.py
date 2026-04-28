import asyncio
import logging

from email_handler import EmailHandler
from telegram_handler import TelegramHandler
from gpt4_analyzer import GPT4Analyzer
from config import load_config
from utils.file_storage import AsyncJSONStorage


storage = AsyncJSONStorage("processed_emails.json")

stats = {
    "processed": 0,
    "fallback": 0,
    "errors": 0
}


# ------------------------
# 📦 STORAGE
# ------------------------

async def load_processed_emails():
    try:
        data = await storage.read()
        return set(data)
    except Exception:
        return set()


async def save_processed_email(email_id):
    await storage.append_unique(email_id)


# ------------------------
# 🚫 ФИЛЬТР ПИСЕМ
# ------------------------

def should_exclude_email(subject, text):
    excluded_keywords = [
        "Vobile Compliance",
        "Notice of Claimed Infringement",
        "Vobile, Inc.",
        "McGrawHill",
        "Global Services"
    ]

    for keyword in excluded_keywords:
        if keyword.lower() in subject.lower() or keyword.lower() in text.lower():
            return True

    return False


# ------------------------
# 📬 ОБРАБОТКА ПИСЕМ
# ------------------------

async def fetch_unread_emails(
    email_handler,
    telegram_handler,
    analyzer,
    prompt_text
):
    processed_emails = await load_processed_emails()

    emails = email_handler.fetch_unread_emails()

    for e_id, subject, text, date in emails:

        if e_id in processed_emails:
            continue

        if should_exclude_email(subject, text):
            logging.info(f"[{e_id}] Исключено: {subject[:80]}")
            continue

        logging.info(f"[{e_id}] Обработка: {subject[:80]}")

        try:
            # AI анализ
            analysis_result = await analyzer.analyze_text(text, prompt_text)

            # fallback метрика
            if "fallback" in analysis_result.lower():
                stats["fallback"] += 1

            # добавляем дату
            full_message = f"<b>Дата:</b> {date}\n\n{analysis_result}"

            # отправка
            sent = await telegram_handler.send_message(subject, full_message)

            if sent:
                stats["processed"] += 1
                logging.info(f"[{e_id}] Готово")
            else:
                stats["errors"] += 1
                logging.error(f"[{e_id}] Ошибка отправки Telegram")

            await save_processed_email(e_id)
            processed_emails.add(e_id)

        except Exception as e:
            stats["errors"] += 1
            logging.error(f"[{e_id}] Ошибка обработки: {e}")


# ------------------------
# 🚀 MAIN LOOP
# ------------------------

async def main():
    logging.info("Запуск скрипта...")

    config = load_config()

    IMAP_SERVER = config["IMAP_SERVER"]
    EMAIL_USERNAME = config["EMAIL_USERNAME"]
    EMAIL_PASSWORD = config["EMAIL_PASSWORD"]
    TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
    TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]
    PROMPT_TEXT = config["PROMPT_TEXT"]
    GPT_MODEL = config["GPT_MODEL"]

    logging.info(f"Используется модель: {GPT_MODEL}")

    # создаём ОДИН раз
    email_handler = EmailHandler(IMAP_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD)
    telegram_handler = TelegramHandler(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    analyzer = GPT4Analyzer(GPT_MODEL)

    loop_count = 0

    while True:
        try:
            await fetch_unread_emails(
                email_handler,
                telegram_handler,
                analyzer,
                PROMPT_TEXT
            )

            loop_count += 1

            # статистика раз в 10 циклов (~5 минут)
            if loop_count % 10 == 0:
                logging.info(
                    f"processed={stats['processed']} | "
                    f"fallback={stats['fallback']} | errors={stats['errors']}"
                )

            await asyncio.sleep(10)

        except Exception as e:
            stats["errors"] += 1
            logging.error(f"Критическая ошибка: {e}")
            await asyncio.sleep(10)


# ------------------------
# ▶️ ENTRYPOINT
# ------------------------

if __name__ == "__main__":
    asyncio.run(main())