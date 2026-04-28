import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import logging


class EmailHandler:
    def __init__(self, imap_server, username, password):
        self.imap_server = imap_server
        self.username = username
        self.password = password

    # ------------------------
    # 📬 ПОЛУЧЕНИЕ ПИСЕМ
    # ------------------------

    def fetch_unread_emails(self):
        result = []
        mail = None

        logging.info("Проверка почты...")

        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, timeout=15)
            mail.login(self.username, self.password)

            # ❗ ВАЖНО: без readonly
            mail.select("inbox")

            status, messages = mail.search(None, "UNSEEN")

            if status != "OK":
                logging.warning("Не удалось получить список писем")
                return result

            email_ids = messages[0].split()

            if not email_ids:
                logging.info("Новых писем нет")
                return result

            logging.info(f"Найдено непрочитанных писем: {len(email_ids)}")

            for num in email_ids:
                e_id = num.decode()

                try:
                    status, msg_data = mail.fetch(num, "(RFC822)")

                    if status != "OK" or not msg_data or not msg_data[0]:
                        logging.warning(f"[{e_id}] Не удалось получить письмо")
                        continue

                    msg = email.message_from_bytes(msg_data[0][1])

                    subject = self._decode(msg.get("Subject"))
                    body = self._extract_text(msg)

                    date_raw = msg.get("Date", "")
                    date_parsed = self._parse_date(date_raw)

                    logging.info(f"[{e_id}] Письмо: {subject[:60]}")

                    result.append((e_id, subject, body, date_parsed))

                except Exception as e:
                    logging.error(f"[{e_id}] Ошибка обработки письма: {e}")

        except Exception as e:
            logging.error(f"Ошибка подключения к IMAP: {e}")

        finally:
            if mail:
                try:
                    mail.logout()
                except Exception:
                    pass

            logging.info("Проверка завершена")

        return result

    # ------------------------
    # ✅ ПОМЕТКА ПРОЧИТАННЫМ
    # ------------------------

    def mark_as_seen(self, email_id):
        mail = None

        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, timeout=10)
            mail.login(self.username, self.password)
            mail.select("inbox")

            mail.store(email_id, "+FLAGS", "\\Seen")

            logging.info(f"[{email_id}] Помечено как прочитанное")

        except Exception as e:
            logging.warning(f"[{email_id}] Ошибка mark_as_seen: {e}")

        finally:
            if mail:
                try:
                    mail.logout()
                except Exception:
                    pass

    # ------------------------
    # 🔤 ДЕКОД ТЕМЫ
    # ------------------------

    def _decode(self, value):
        if not value:
            return ""

        parts = decode_header(value)
        result = ""

        for decoded, charset in parts:
            if isinstance(decoded, bytes):
                result += decoded.decode(charset or "utf-8", errors="ignore")
            else:
                result += decoded

        result = result.replace("\r", "").replace("\n", " ").strip()

        result = " ".join(result.split())

        return result

    # ------------------------
    # 📅 ДАТА
    # ------------------------

    def _parse_date(self, date_str):
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            return "неизвестно"

    # ------------------------
    # 📄 ТЕЛО ПИСЬМА
    # ------------------------

    def _extract_text(self, msg):
        try:
            text = ""

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    payload = part.get_payload(decode=True)

                    if not payload:
                        continue

                    if content_type == "text/plain":
                        return payload.decode(errors="ignore")

                    if content_type == "text/html" and not text:
                        text = payload.decode(errors="ignore")

            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="ignore")

            return text

        except Exception:
            return ""