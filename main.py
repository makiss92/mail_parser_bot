import time
import imaplib
import email
import json
import os
import logging
import requests
from g4f.client import Client

# Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Конфигурационный файл для хранения обработанных писем
CONFIG_FILE = "processed_emails.json"

def load_processed_emails():
    try:
        with open(CONFIG_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_processed_email(email_id):
    processed = load_processed_emails()
    processed.add(email_id)
    with open(CONFIG_FILE, "w") as f:
        json.dump(list(processed), f)

def fetch_unread_emails(username, password, imap_server, bot_token, chat_id):
    processed_emails = load_processed_emails()
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(username, password)
    mail.select("inbox")

    # Ищем только непрочитанные письма
    status, messages = mail.search(None, 'UNSEEN')
    if status == 'OK' and messages[0]:  # Проверяем, что есть непрочитанные письма
        email_ids = messages[0].split()
        logging.info(f"Found {len(email_ids)} unread emails.")
    else:
        email_ids = []  # Если писем нет, возвращаем пустой список
        logging.info("No unread emails found.")

    emails = []
    for e_id in email_ids:
        e_id_decoded = e_id.decode()
        if e_id_decoded in processed_emails:
            #logging.info(f"Email {e_id_decoded} already processed. Skipping.")
            continue

        try:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg["Subject"]
                    logging.info(f"Processing email with ID: {e_id_decoded}, Subject: {subject}")

                    # Извлекаем текст письма
                    text = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                text += part.get_payload(decode=True).decode()
                    else:
                        text = msg.get_payload(decode=True).decode()

                    # Анализируем текст через GPT-4
                    analysis_result = analyze_with_gpt4(text, "Проанализируй текст письма и предложи рекомендации.")
                    logging.info(f"Analysis result: {analysis_result}")

                    # Отправляем рекомендацию в Telegram
                    send_to_telegram(bot_token, chat_id, subject, analysis_result)
                    logging.info(f"Email {e_id_decoded} processed and sent to Telegram.")

                    # Сохраняем ID письма как обработанное
                    save_processed_email(e_id_decoded)
                    logging.info(f"Email {e_id_decoded} marked as processed.")

        except Exception as e:
            logging.error(f"Error processing email {e_id_decoded}: {str(e)}")

    return emails

def analyze_with_gpt4(text, prompt):
    try:
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
        )
        result = response.choices[0].message.content
        logging.info(f"GPT-4 analysis successful: {result}")
        return result
    except Exception as e:
        logging.error(f"Error analyzing text with GPT-4: {str(e)}")
        return None

def send_to_telegram(bot_token, chat_id, subject, message):
    """
    Отправляет сообщение в Telegram с Markdown-форматированием.

    :param bot_token: Токен вашего Telegram-бота.
    :param chat_id: ID чата.
    :param subject: Тема письма.
    :param message: Сообщение для отправки.
    """
    try:
        # Экранируем специальные символы в теме и сообщении
        subject = escape_markdown(subject)
        message = escape_markdown(message)

        # Форматируем сообщение
        formatted_message = f"**Тема:** {subject}\n\n> {message}"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": formatted_message,
            "parse_mode": "MarkdownV2"  # Включаем Markdown-форматирование
        }
        response = requests.post(url, json=payload)
        logging.info(f"Message sent to Telegram: {response.json()}")
        return response.json()
    except Exception as e:
        logging.error(f"Error sending message to Telegram: {str(e)}")
        return None

def escape_markdown(text):
    """
    Экранирует специальные символы для MarkdownV2.

    :param text: Исходный текст.
    :return: Экранированный текст.
    """
    escape_chars = "_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)


def load_config():
    """
    Загружает конфиденциальные данные из переменных окружения.
    """
    config = {
        "imap_server": os.getenv("IMAP_SERVER"),
        "email_username": os.getenv("EMAIL_USERNAME"),
        "email_password": os.getenv("EMAIL_PASSWORD"),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID"),
    }
    if None in config.values():
        raise ValueError("Не все переменные окружения заданы.")
    return config

# Основная функция
def main():
    logging.info("Starting the script...")

    # Загружаем конфиденциальные данные
    config = load_config()

    # Конфигурация
    IMAP_SERVER = config["imap_server"]
    EMAIL_USERNAME = config["email_username"]
    EMAIL_PASSWORD = config["email_password"]
    TELEGRAM_BOT_TOKEN = config["telegram_bot_token"]
    TELEGRAM_CHAT_ID = config["telegram_chat_id"]

    # Промпт для нейросети
    prompt = "Проанализируй текст письма и предложи рекомендации! Только пожалуйста кратно, прям тезисно!"

    while True:
        try:
            emails = fetch_unread_emails(EMAIL_USERNAME, EMAIL_PASSWORD, IMAP_SERVER, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

            for e_id, email_msg in emails:
                try:
                    # Извлекаем тему письма
                    subject = email_msg["Subject"]
                    if not subject:
                        subject = "Без темы"

                    # Извлекаем текст письма
                    text = ""
                    if email_msg.is_multipart():
                        for part in email_msg.walk():
                            if part.get_content_type() == "text/plain":
                                text += part.get_payload(decode=True).decode()
                    else:
                        text = email_msg.get_payload(decode=True).decode()

                    # Анализируем текст через GPT-4
                    analysis_result = analyze_with_gpt4(text, prompt)
                    recommendation = analysis_result if analysis_result else "Не удалось получить рекомендацию."

                    # Отправляем рекомендацию в Telegram с темой письма
                    send_to_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, subject, recommendation)
                    save_processed_email(e_id.decode())

                except Exception as e:
                    logging.error(f"Error processing email {e_id}: {str(e)}")

            time.sleep(30)

        except Exception as e:
            logging.error(f"Critical error: {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    main()