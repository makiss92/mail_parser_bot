import logging
import asyncio
import re
import time
import json

from config import GPT4_AVAILABLE


class GPT4Analyzer:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model_name = model_name

        # circuit breaker
        self.fail_count = 0
        self.fail_threshold = 5
        self.cooldown_until = 0

        if GPT4_AVAILABLE:
            from g4f.client import Client
            self.client = Client(providers=["DeepInfra"])
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

        return False

    # ------------------------
    # 🌍 ЯЗЫК
    # ------------------------

    def is_russian(self, text: str) -> bool:
        cyr = len(re.findall(r"[а-яА-Я]", text))
        lat = len(re.findall(r"[a-zA-Z]", text))
        return cyr > lat

    # ------------------------
    # 📦 JSON
    # ------------------------

    def parse_json(self, text: str):
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if not match:
                return None
            return json.loads(match.group(0))
        except Exception:
            return None

    # ------------------------
    # 🧹 STREAM CLEAN
    # ------------------------

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

    def fallback(self, text: str) -> str:
        text_lower = text.lower()

        ips = re.findall(r'\d+\.\d+\.\d+\.\d+', text)
        ip_list = list(set(ips))[:3]

        ip_html = ", ".join(f"<code>{ip}</code>" for ip in ip_list) if ip_list else "не определён"

        # ------------------------
        # КЛАССИФИКАЦИЯ
        # ------------------------

        if any(x in text_lower for x in ["ddos", "attack", "flood"]):
            cls = "DDoS / атака"
            priority = "🚨"

            memo = [
                "Проверь исходящий трафик",
                "Ограничь трафик на firewall",
                "Проверь активные процессы"
            ]

            commands = [
                "iftop -i eth0",
                "ss -antp | grep ESTAB",
                "top -o %CPU",
                "iptables -L -n --line-numbers"
            ]

        elif any(x in text_lower for x in ["brute", "login", "ssh"]):
            cls = "Брутфорс / подбор паролей"
            priority = "⚠️"

            memo = [
                "Проверь попытки авторизации",
                "Ограничь доступ по IP",
                "Включи fail2ban"
            ]

            commands = [
                "grep 'Failed password' /var/log/auth.log | tail -n 20",
                "last -a | head",
                "fail2ban-client status",
                "ss -antp | grep :22"
            ]

        elif any(x in text_lower for x in ["scan", "crawler", "nmap"]):
            cls = "Сканирование"
            priority = "⚠️"

            memo = [
                "Обычно не критично",
                "Проверь открытые порты",
                "Можно включить rate-limit"
            ]

            commands = [
                "ss -tulnp",
                "netstat -tulnp",
                "iptables -L -n",
                "conntrack -L | head"
            ]

        else:
            cls = "Abuse / подозрительная активность"
            priority = "ℹ️"

            memo = [
                "Проверь систему",
                "Проверь сетевые соединения",
                "Проверь последние изменения"
            ]

            commands = [
                "ss -antp",
                "ps aux --sort=-%cpu | head",
                "last -a"
            ]

        # ------------------------
        # ОПИСАНИЕ
        # ------------------------

        desc = f"Обнаружена активность с IP {ip_html}. Выполнен базовый анализ."

        # ------------------------
        # ДЕЙСТВИЯ
        # ------------------------

        actions = [
            f"Проверить устройство с IP {ip_html}",
            "Проанализировать сетевые логи",
            "Ограничить подозрительный трафик"
        ]

        actions_html = "\n".join(f"• {a}" for a in actions)
        memo_html = "\n".join(f"• {m}" for m in memo)
        commands_html = "\n".join(f"<code>{c}</code>" for c in commands)

        commands_block = ""
        if commands:
            commands_block = f"\n\n<b>💻 Команды</b>\n{commands_html}"

        return (
            f"<b>{priority} СЕТЕВОЙ ИНЦИДЕНТ (fallback)</b>\n\n"
            f"<b>🔍 Классификация</b>\n{cls}\n\n"
            f"<b>📖 Описание</b>\n{desc}\n\n"
            f"<b>🛠 Действия</b>\n{actions_html}\n\n"
            f"<b>📌 Памятка</b>\n{memo_html}"
            f"{commands_block}"
        )

    # ------------------------
    # 🧠 ОСНОВНОЙ МЕТОД
    # ------------------------

    async def analyze_text(self, text, prompt):
        text = self.clean_input(text)

        if not GPT4_AVAILABLE or not self.client:
            return self.fallback(text)

        if time.time() < self.cooldown_until:
            return self.fallback(text)

        for attempt in range(1, 4):
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
                result = self.clean_response(result)
                result = self.normalize_llm_output(result)

                if not self.is_bad(result):
                    formatted = self.format_output(result)
                    if formatted:
                        self.fail_count = 0
                        return formatted

            except Exception as e:
                logging.warning(f"[LLM] attempt {attempt}: {e}")

                self.fail_count += 1

                if self.fail_count >= self.fail_threshold:
                    self.cooldown_until = time.time() + 60
                    break

            await asyncio.sleep(2 ** attempt)

        return self.fallback(text)

    # ------------------------
    # 🧹 CLEAN
    # ------------------------

    def normalize_llm_output(self, text: str) -> str:
        if not text:
            return ""

        text = text.replace("*", "")
        text = re.sub(r'need proxies.*', '', text, flags=re.I)

        return text.strip()

    # ------------------------
    # 🎨 FORMAT
    # ------------------------

    def escape_html(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def format_output(self, text: str) -> str:
        if not text:
            return None

        # ------------------------
        # CLEAN
        # ------------------------

        text = re.sub(r'https?://\S+', '', text)
        text = text.replace("*", "").replace("```", "").replace("---", "")

        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # ------------------------
        # PARSE
        # ------------------------

        cls = desc = ""
        rec = []
        memo = []

        current = None

        for line in lines:
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
            elif "памятка" in l:
                current = "memo"
                continue

            if current == "cls":
                cls += " " + line
            elif current == "desc":
                desc += " " + line
            elif current == "rec":
                rec.append(line)
            elif current == "memo":
                memo.append(line)

        if not cls.strip():
            cls = "Abuse активность"

        if not desc.strip():
            desc = "Обнаружена подозрительная активность"

        # ------------------------
        # ENTITY HIGHLIGHT
        # ------------------------

        def highlight_entities(x):
            x = re.sub(r'(\d+\.\d+\.\d+\.\d+)', r'<code>\1</code>', x)
            x = re.sub(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'<code>\1</code>', x)
            return x

        cls = highlight_entities(self.escape_html(cls))
        desc = highlight_entities(self.escape_html(desc))

        rec = [highlight_entities(self.escape_html(r)) for r in rec]
        memo = [highlight_entities(self.escape_html(m)) for m in memo]

        # ------------------------
        # CLEAN ACTIONS
        # ------------------------

        cleaned_rec = []

        for r in rec:
            r = re.sub(r'^[-•.\s]+', '', r).strip()

            if not r:
                continue

            if any(x in r.lower() for x in ["proxy", "http", "www"]):
                continue

            cleaned_rec.append(r)

        if not cleaned_rec:
            cleaned_rec = [
                "Проверить сервер",
                "Проанализировать логи",
                "Ограничить трафик"
            ]

        rec_html = "\n".join(f"• {r}" for r in cleaned_rec)

        # ------------------------
        # MEMO
        # ------------------------

        cleaned_memo = []

        for m in memo:
            m = re.sub(r'^[-•.\s]+', '', m).strip()
            if m:
                cleaned_memo.append(m)

        if not cleaned_memo:
            cleaned_memo = [
                "Проверить систему",
                "Проверить сетевые соединения",
                "Проверить процессы"
            ]

        memo_html = "\n".join(f"• {m}" for m in cleaned_memo)

        # ------------------------
        # PRIORITY
        # ------------------------

        text_lower = text.lower()

        if any(x in text_lower for x in ["ddos", "botnet"]):
            priority = "🚨"
        elif any(x in text_lower for x in ["brute", "scan"]):
            priority = "⚠️"
        else:
            priority = "ℹ️"

        # ------------------------
        # COMMANDS
        # ------------------------

        commands = []

        if "ddos" in text_lower:
            commands = [
                "iftop -i eth0",
                "ss -antp | grep ESTAB",
                "top -o %CPU",
                "iptables -L -n"
            ]

        elif "brute" in text_lower:
            commands = [
                "grep 'Failed password' /var/log/auth.log | tail",
                "last -a",
                "fail2ban-client status",
                "ss -antp | grep :22"
            ]

        elif "scan" in text_lower:
            commands = [
                "ss -tulnp",
                "netstat -tulnp",
                "iptables -L -n",
                "conntrack -L | head"
            ]

        commands_html = "\n".join(f"<code>{c}</code>" for c in commands)

        commands_block = ""
        if commands:
            commands_block = f"\n\n<b>💻 Команды (пример)</b>\n{commands_html}"

        # ------------------------
        # OUTPUT
        # ------------------------

        return (
            f"<b>{priority} СЕТЕВОЙ ИНЦИДЕНТ</b>\n\n"
            f"<b>🔍 Классификация</b>\n{cls.strip()}\n\n"
            f"<b>📖 Описание</b>\n{desc.strip()}\n\n"
            f"<b>🛠 Действия</b>\n{rec_html}\n\n"
            f"<b>📌 Памятка</b>\n{memo_html}"
            f"{commands_block}"
        )