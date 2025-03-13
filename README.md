# Mail Parser Bot

**Mail Parser Bot** — это автоматизированный бот, который анализирует электронные письма, извлекает ключевую информацию и отправляет рекомендации в Telegram. Бот использует GPT-4 для анализа текста писем и предоставляет удобные рекомендации в формате, понятном пользователю.

## Основные функции:

- **Парсинг писем**: Автоматически извлекает текст из непрочитанных писем с почтового сервера.
- **Анализ текста**: Использует GPT-4 для анализа текста и генерации рекомендаций.
- **Отправка в Telegram**: Отправляет рекомендации в Telegram.
- **Поддержка Docker:** Для простого развертывания проекта.
- **Фильтрация писем:** По ключевым словам (например, "спам", "реклама").

## Требования:

- **Python 3.9** или выше.
- **Docker** (опционально, для контейнеризации).
- **Учетная запись Telegram** для создания бота и получения `chat_id`.

## Установка:

1. Убедиться, что **Docker** и **Docker Compose** установлены ([Инструкция](https://docs.docker.com/engine/install/)).  

2. Скопировать папку проекта (или клонируйте репозиторий с помощью [Git](https://github.com/makiss92/mail_parser_bot.git)).

3. Создать файл `.env` и заполните его конфиденциальными данными:
```ini
IMAP_SERVER=imap.example.com
EMAIL_USERNAME=your_email@example.com
EMAIL_PASSWORD=your_password
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
PROMPT_TEXT=request_text_for_gpt
```

4. Запустить контейнер:
```bash
docker-compose up --build
```
> Для запуска контейнера в фоновом режиме используйте флаг `-d`.

# Итог
Теперь ваш проект упакован в Docker и готов к развёртыванию `"одной командой"`. 
Вы можете легко переносить его на другие компьютеры и запускать без необходимости установки зависимостей вручную.
