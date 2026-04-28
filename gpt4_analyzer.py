import logging
import asyncio
import re

from config import GPT4_AVAILABLE


class GPT4Analyzer:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model_name = model_name

        if GPT4_AVAILABLE:
            from g4f.client import Client
            self.client = Client(
                providers=["DeepInfra"]
            )
        else:
            self.client = None

    # ------------------------
    # 🧹 ЧИСТКА ВХОДА
    # ------------------------

    def clean_input(self, text: str) -> str:
        lines = text.splitlines()
        cleaned = []

        for line in lines:
            l = line.lower()

            if "unsubscribe" in l:
                continue
            if "proxy" in l:
                continue
            if "op.wtf" in l:
                continue

            cleaned.append(line)

        return "\n".join(cleaned)

    # ------------------------
    # 🔍 ВАЛИДАЦИЯ
    # ------------------------

    def is_bad(self, text: str) -> bool:
        if not text:
            return True

        t = text.lower().strip()

        if len(t) < 100:
            return True

        if "hello" in t or "click" in t:
            return True

        if "фишинг" in t and ("attack" in t or "server" in t):
            return True

        return False

    # ------------------------
    # 🌍 ЯЗЫК
    # ------------------------

    def is_russian(self, text: str) -> bool:
        cyr = len(re.findall(r"[а-яА-Я]", text))
        lat = len(re.findall(r"[a-zA-Z]", text))
        return cyr > lat

    # ------------------------
    # 🧹 ЧИСТКА ОТВЕТА
    # ------------------------

    import json

    def parse_json(self, text: str):
        import json
        import re

        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if not match:
                return None

            raw = match.group(0)

            return json.loads(raw)

        except Exception:
            return None

    def clean_response(self, text: str) -> str:
        if text.strip().startswith("data: {"):
            try:
                return " ".join(
                    line.split('"content":"')[1].split('"}')[0]
                    for line in text.splitlines()
                    if '"content":"' in line
                )
            except:
                pass

        return text

    # ------------------------
    # 🚨 FALLBACK
    # ------------------------

    def fallback(self, text):
        import re

        text_lower = text.lower()

        # ------------------------
        # 🌐 IP
        # ------------------------

        ip_match = re.search(r'\d+\.\d+\.\d+\.\d+', text)
        ip = ip_match.group(0) if ip_match else "не определён"
        ip_html = f"<code>{ip}</code>"

        # ------------------------
        # 🔍 КЛАССИФИКАЦИЯ
        # ------------------------

        if any(x in text_lower for x in ["ddos", "attack", "flood"]):
            cls = "DDoS / атака"
            priority = "🚨"
        elif any(x in text_lower for x in ["scan", "crawler", "scraping"]):
            cls = "Сканирование / сбор данных"
            priority = "⚠️"
        elif any(x in text_lower for x in ["brute", "login attempt"]):
            cls = "Брутфорс"
            priority = "⚠️"
        else:
            cls = "Abuse report"
            priority = "ℹ️"

        # ------------------------
        # 📖 ОПИСАНИЕ
        # ------------------------

        desc = (
            f"Зафиксирована подозрительная активность с IP {ip_html}. "
            f"Источник не был обработан LLM, выполнен базовый анализ."
        )

        # ------------------------
        # 🛠 РЕКОМЕНДАЦИИ
        # ------------------------

        actions = [
            f"Проверить устройство с IP {ip_html} на компрометацию",
            "Проанализировать сетевые логи и активные соединения",
            "Ограничить или заблокировать подозрительный исходящий трафик",
            "Проверить открытые порты и доступы (SSH, RDP, Web)",
            "Обновить ПО и сменить пароли на всех сервисах",
        ]

        actions_html = "\n".join(f"• {a}" for a in actions)

        # ------------------------
        # 🎨 HTML ВЫВОД
        # ------------------------

        return (
            f"<b>{priority} СЕТЕВОЙ ИНЦИДЕНТ (fallback)</b>\n\n"
            f"<b>🔍 Классификация</b>\n{cls}\n\n"
            f"<b>📖 Описание</b>\n{desc}\n\n"
            f"<b>🛠 Действия</b>\n{actions_html}"
        )

    # ------------------------
    # 🧠 ОСНОВНОЙ МЕТОД
    # ------------------------

    async def analyze_text(self, text, prompt):
        text = self.clean_input(text)

        if not GPT4_AVAILABLE or not self.client:
            return self.fallback(text)

        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": text}
                        ]
                    ),
                    timeout=20
                )

                result = response.choices[0].message.content
                result = self.normalize_llm_output(result)

                # ------------------------
                # 🔥 2. fallback на текст
                # ------------------------
                if not self.is_bad(result):
                    formatted = self.format_output(result)
                    if formatted:
                        return formatted

            except Exception as e:
                logging.warning(f"GPT attempt {attempt}: {e}")

            await asyncio.sleep(1)

        # ------------------------
        # 🚨 полный fallback
        # ------------------------
        return self.fallback(text)


    def normalize_llm_output(self, text: str) -> str:
        import re

        if not text:
            return ""

        # ❌ убираем markdown/звёздочки
        text = text.replace("*", "")

        # ❌ убираем лишние блоки
        text = re.sub(r'запрещено:.*', '', text, flags=re.IGNORECASE | re.DOTALL)

        # ❌ убираем рекламу
        text = re.sub(r'need proxies.*', '', text, flags=re.IGNORECASE)

        return text.strip()


    # ------------------------
    # 🎨 ФОРМАТИРОВАНИЕ ВЫВОДА
    # ------------------------

    def escape_html(self, text: str) -> str:
        if not text:
            return ""

        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )


    def format_output(self, text: str) -> str:
        import re   

        if not text:
            return None

        # ------------------------
        # 🧹 ЧИСТКА МУСОРА
        # ------------------------

        lines = text.splitlines()
        cleaned = []

        for line in lines:
            l = line.lower()

            if any(x in l for x in ["proxy", "op.wtf", "cheaper than"]):
                continue

            cleaned.append(line.strip())

        text = "\n".join(cleaned)
        text = text.replace("*", "")
        text = text.replace("---", "")
        text = text.replace("```", "")
        text = re.sub(r'</?(?!code|b)[^>]+>', '', text)

        # ------------------------
        # 📦 ПАРСИМ БЛОКИ
        # ------------------------

        cls = desc = ""
        rec = []

        current = None

        for line in cleaned:
            l = line.lower()

            if "классификац" in l:
                current = "cls"
                continue
            elif "описан" in l:
                current = "desc"
                continue
            elif "рекомендац" in l or "действ" in l:
                current = "rec"
                continue

            if current == "cls":
                cls += " " + line
            elif current == "desc":
                desc += " " + line
            elif current == "rec":
                rec.append(line)

        # fallback
        if not cls:
            cls = "Abuse / подозрительная активность"

        if not desc:
            desc = "Обнаружена подозрительная активность"

        # ------------------------
        # 🎯 IP В <code>
        # ------------------------

        def highlight_ip(x):
            return re.sub(r'(\d+\.\d+\.\d+\.\d+)', r'<code>\1</code>', x)

        cls = self.escape_html(cls)
        desc = self.escape_html(desc)
        rec = [self.escape_html(r) for r in rec]

        # потом уже IP
        cls = highlight_ip(cls)
        desc = highlight_ip(desc)
        rec = [highlight_ip(r) for r in rec]

        # ------------------------
        # 🧠 ЧИСТИМ СПИСОК
        # ------------------------

        fixed = []
        for r in rec:
            r = r.lstrip("-• ").strip()
            if r:
                fixed.append(r)

        if not fixed:
            fixed = ["Проверить сервер", "Проанализировать логи"]

        rec_html = "\n".join(f"• {r}" for r in fixed)

        # ------------------------
        # 🚨 ПРИОРИТЕТ
        # ------------------------

        priority = "⚠️"
        if "ddos" in text.lower():
            priority = "🚨"

        # ------------------------
        # 🎨 ВЫВОД (HTML)
        # ------------------------

        return (
    f"<b>{priority} СЕТЕВОЙ ИНЦИДЕНТ</b>\n\n"
    f"<b>🔍 Классификация</b>\n{cls.strip()}\n\n"
    f"<b>📖 Описание</b>\n{desc.strip()}\n\n"
    f"<b>🛠 Действия</b>\n{rec_html}"
)