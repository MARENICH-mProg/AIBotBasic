# AI Bot Basic

Telegram бот на базе OpenAI API с функциями определения юмора и реакций на сообщения.

## Возможности

- Обработка текстовых сообщений с помощью OpenAI API
- Определение юмористического контента
- Реакции на смешные сообщения
- Сохранение истории сообщений в базе данных
- Асинхронная обработка запросов

## Технологии

- Python 3.9+
- aiogram 3.x
- OpenAI API
- SQLAlchemy
- uvloop (для Unix-систем)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/YOUR_USERNAME/AIBotBasic.git
cd AIBotBasic
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv .venv
source .venv/bin/activate  # для Unix
# или
.venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` и добавьте необходимые переменные окружения:
```
TELEGRAM_TOKEN=your_telegram_token
OPENAI_API_KEY=your_openai_api_key
```

## Запуск

```bash
python bot.py
```

## Структура проекта

```
AIBotBasic/
├── admin/
│   ├── database.py
│   └── models.py
├── bot.py
├── requirements.txt
└── README.md
```

## Лицензия

MIT
