# Чтобы развернуть проект, Вам необходимо:

1. Убедиться, что **Docker** и **Docker Compose** установлены.  
   Вы можете найти инструкции по установке Docker [здесь](https://docs.docker.com/engine/install/).

2. Скопировать папку проекта (или клонируйте репозиторий с помощью Git).

3. Создать файл `.env` и заполните его конфиденциальными данными:
```ini
IMAP_SERVER=
EMAIL_USERNAME=
EMAIL_PASSWORD=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

4. Запустить контейнер:
```bash
docker-compose up --build
```
5. Дополнительные улучшения(не обязательно):

Если вы хотите сохранять логи в файл, добавьте монтирование `volume` для логов:

```yaml
volumes:
   - .:/app
   - ./logs:/app/logs  # Монтируем папку для логов
```

6. Обновите код для записи логов в файл:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/mail-bot.log"),  # Логи в файл
        logging.StreamHandler()  # Логи в консоль
    ]
)
```

# Итог
Теперь ваш проект упакован в Docker и готов к развёртыванию `"одной командой"`. 
Вы можете легко переносить его на другие компьютеры и запускать без необходимости установки зависимостей вручную.
