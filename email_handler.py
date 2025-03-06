import imaplib
import email
from email.header import decode_header
import logging

class EmailHandler:
    def __init__(self, imap_server, username, password):
        self.imap_server = imap_server
        self.username = username
        self.password = password
        self.mail = imaplib.IMAP4_SSL(imap_server)
        self.mail.login(username, password)
        self.mail.select("inbox")

    def decode_mime_header(self, header):
        decoded_parts = decode_header(header)
        decoded_str = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_str += part.decode(encoding or "utf-8", errors="replace")
            else:
                decoded_str += part
        return decoded_str

    def extract_text(self, msg):
        text = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    text += part.get_payload(decode=True).decode("utf-8", errors="replace")
        else:
            text = msg.get_payload(decode=True).decode("utf-8", errors="replace")
        return text

    def fetch_unread_emails(self):
        status, messages = self.mail.search(None, 'UNSEEN')
        if status == 'OK' and messages[0]:
            email_ids = messages[0].split()
            logging.info(f"Найдено {len(email_ids)} новое письмо.")
        else:
            email_ids = []
            logging.info("Новых писем не найдено.")

        emails = []
        for e_id in email_ids:
            e_id_decoded = e_id.decode()
            try:
                _, msg_data = self.mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = msg["Subject"]
                        if subject:
                            subject = self.decode_mime_header(subject)
                        else:
                            subject = "Без темы"
                        #logging.info(f"Processing email with ID: {e_id_decoded}, Subject: {subject}")

                        text = self.extract_text(msg)
                        emails.append((e_id_decoded, subject, text))
            except Exception as e:
                logging.error(f"Ошибка при обработке почты {e_id_decoded}: {str(e)}")

        return emails