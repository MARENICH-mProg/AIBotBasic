# AIBotBasic

This repository provides a minimal Telegram bot that uses OpenAI to generate replies.  

## Setup

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set the following environment variables (you can copy `.env.example` to `.env`):

- `TELEGRAM_BOT_TOKEN` – your Telegram bot token
- `OPENAI_API_KEY` – OpenAI API key

3. Run the bot:

```bash
python bot.py
```

When a user sends `/start`, the bot greets them. Subsequent messages are sent to OpenAI and the generated response is returned.
