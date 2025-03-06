# Чтобы развернуть проект, Вам необходимо:

1. Убедитесь, что **Docker** и **Docker Compose** установлены.  
   Вы можете найти инструкции по установке Docker [здесь](https://docs.docker.com/engine/install/).

2. Скопируйте папку проекта (или клонируйте репозиторий с помощью Git).

3. Создайте файл `.env` и заполните его конфиденциальными данными:
    ```IMAP_SERVER=
    EMAIL_USERNAME=
    EMAIL_PASSWORD=
    TELEGRAM_BOT_TOKEN=
    TELEGRAM_CHAT_ID=

5. Запустите контейнер:
   ```bash
   docker-compose up --build
