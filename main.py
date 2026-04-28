import asyncio
import logging

from email_handler import EmailHandler
from telegram_handler import TelegramHandler
from gpt4_analyzer import GPT4Analyzer
from config import load_config
from utils.file_storage import AsyncJSONStorage
from queue_manager import MailQueue
from rate_limiter import RateLimiter

llm_limiter = RateLimiter(5, 60)
tg_limiter = RateLimiter(20, 60)

storage = AsyncJSONStorage("processed_emails.json")

stats = {
    "processed": 0,
    "fallback": 0,
    "errors": 0
}


async def load_processed_emails():
    try:
        data = await storage.read()
        return set(data)
    except:
        return set()


async def save_processed_email(email_id):
    await storage.append_unique(email_id)


def should_exclude_email(subject, text):
    excluded_keywords = [
        "Vobile", "McGrawHill", "Compliance"
    ]
    return any(k.lower() in subject.lower() or k.lower() in text.lower() for k in excluded_keywords)


async def producer(email_handler, mail_queue, poll_interval):
    while True:
        try:
            emails = email_handler.fetch_unread_emails()

            for mail in emails:
                if mail_queue.size() > 150:
                    logging.warning("Переполнение очереди")
                    break

                await mail_queue.put(mail)

        except Exception as e:
            logging.error(f"[PRODUCER] {e}")

        await asyncio.sleep(poll_interval)


async def worker(mail_queue, telegram_handler, analyzer, prompt_text, processed_emails):
    processed_emails = await load_processed_emails()

    while True:
        e_id, subject, text, date = await mail_queue.get()

        try:
            if e_id in processed_emails:
                mail_queue.task_done()
                continue

            if should_exclude_email(subject, text):
                mail_queue.task_done()
                
                continue
            await llm_limiter.acquire()
            result = await analyzer.analyze_text(text, prompt_text)

            if "fallback" in result.lower():
                stats["fallback"] += 1

            message = f"<b>Дата:</b> {date}\n\n{result}"

            await tg_limiter.acquire()
            sent = await telegram_handler.send_message(subject, message)

            if sent:
                stats["processed"] += 1
                await save_processed_email(e_id)
                processed_emails.add(e_id)
            else:
                stats["errors"] += 1

        except Exception as e:
            stats["errors"] += 1
            logging.error(f"[WORKER] {e}")

        finally:
            mail_queue.task_done()


async def stats_logger(mail_queue):
    while True:
        await asyncio.sleep(60)
        logging.info(f"[Сводка] {stats} очередь={mail_queue.size()}")


async def main():
    logging.info("Запуск...")

    config = load_config()

    poll_interval = int(config["EMAIL_POLL_INTERVAL"])

    email_handler = EmailHandler(
        config["IMAP_SERVER"],
        config["EMAIL_USERNAME"],
        config["EMAIL_PASSWORD"]
    )

    telegram_handler = TelegramHandler(
        config["TELEGRAM_BOT_TOKEN"],
        config["TELEGRAM_CHAT_ID"]
    )

    analyzer = GPT4Analyzer(config["GPT_MODEL"])

    mail_queue = MailQueue(maxsize=400)

    processed_emails = await load_processed_emails()

    workers = [
        asyncio.create_task(
            worker(mail_queue, telegram_handler, analyzer, config["PROMPT_TEXT"], processed_emails)
        )
        for _ in range(3)
    ]

    await asyncio.gather(
        producer(email_handler, mail_queue, poll_interval),
        stats_logger(mail_queue),
        *workers
    )

if __name__ == "__main__":
    asyncio.run(main())