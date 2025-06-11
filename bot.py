import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = openai.OpenAI(api_key=OPENAI_API_KEY)
WELCOME_TEXT = "Привет! Я бот на базе OpenAI."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_TEXT)
    context.chat_data['messages'] = [{"role": "system", "content": WELCOME_TEXT}]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    messages = context.chat_data.setdefault('messages', [{"role": "system", "content": WELCOME_TEXT}])
    messages.append({"role": "user", "content": text})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    reply_text = response.choices[0].message.content.strip()
    messages.append({"role": "assistant", "content": reply_text})

    await update.message.reply_text(reply_text)


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
