import os
import asyncio
import logging
import json
from collections import defaultdict
from datetime import datetime

from aiogram import Bot, Dispatcher, html, F
from aiogram.types import Message, FSInputFile, Sticker
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from openai import OpenAI

from sqlalchemy.ext.asyncio import AsyncSession
from admin.database import async_session
from admin.models import User, Message as DBMessage

# --- Настройка логирования ---
logging.basicConfig(
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger('TelegramBot')

# --- Конфигурация ---
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("Не задан TELEGRAM_TOKEN или OPENAI_API_KEY")

# Инициализация OpenAI-клиента
client = OpenAI(api_key=OPENAI_API_KEY)

# Словарь для отслеживания состояния пользователей
user_states = defaultdict(lambda: {"is_processing": False, "last_response_id": None})

WELCOME_TEXT = "Привет! Я бот на базе OpenAI. Готов помочь вам!"
# Замените на корректный file_id вашего стикера из BotFather
STICKER_ID = "CAACAgIAAxkBAAEOhxZoLF8eiaEVv5-DojVYr34ibp-jngACKzIAAgFp2UmUd0xG0FOntjYE"

# Инициализация диспетчера
dp = Dispatcher()

async def get_or_create_user(session: AsyncSession, telegram_user) -> User:
    from sqlalchemy import select
    
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            full_name=telegram_user.full_name
        )
        session.add(user)
        await session.commit()
    
    return user

@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    user = message.from_user
    try:
        async with async_session() as session:
            await get_or_create_user(session, user)
        await message.answer(WELCOME_TEXT)
        logger.info(f"Пользователь {user.id} ({user.full_name}) запустил бота")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота для пользователя {user.id}: {str(e)}")

@dp.message()
async def message_handler(message: Message, bot: Bot) -> None:
    """Обработчик всех текстовых сообщений"""
    chat_id = message.chat.id
    user = message.from_user
    user_text = message.text

    # Проверяем, не обрабатывается ли уже сообщение от этого пользователя
    if user_states[chat_id]["is_processing"]:
        logger.info(f"Отклонено сообщение от пользователя {user.id} - предыдущий запрос в обработке")
        temp_msg = await message.answer("Пожалуйста, подождите. Я все еще генерирую ответ на предыдущий запрос.")
        await asyncio.sleep(1)
        await temp_msg.delete()
        await message.delete()
        return

    try:
        logger.info(f"Обработка сообщения от пользователя {user.id} ({user.full_name})")
        user_states[chat_id]["is_processing"] = True

        async with async_session() as session:
            db_user = await get_or_create_user(session, user)
            
            # Создаем запись о сообщении
            db_message = DBMessage(
                user_id=db_user.id,
                content=user_text
            )
            session.add(db_message)
            await session.commit()

            # 1) Отправляем стикер и включаем typing
            sticker_msg = await message.answer_sticker(STICKER_ID)
            await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
            
            # 2) Готовим параметры вызова API с функцией для проверки юмора
            kwargs = {
                "model": "gpt-4.1-nano",
                "tools": [
                    {
                        "type": "function",
                        "name": "check_humor",
                        "description": "Проверяет, является ли сообщение смешным",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "is_funny": {
                                    "type": "boolean",
                                    "description": "True если сообщение смешное, False если нет"
                                }
                            },
                            "required": ["is_funny"]
                        }
                    }
                ],
                "tool_choice": "auto"
            }

            # Формируем входные данные
            input_data = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_text
                        }
                    ]
                }
            ]

            prev_id = user_states[chat_id].get('last_response_id')
            if prev_id:
                kwargs["previous_response_id"] = prev_id

            kwargs["input"] = input_data

            # 3) Асинхронный вызов OpenAI API
            response = client.responses.create(**kwargs)

            # Проверяем наличие вызова функции
            is_funny = False
            tool_call = None
            
            if response.output and len(response.output) > 0 and response.output[0].type == "function_call":
                tool_call = response.output[0]
                try:
                    args = json.loads(tool_call.arguments)
                    is_funny = args.get("is_funny", False)
                    if is_funny:
                        await bot.set_message_reaction(chat_id=message.chat.id, message_id=message.message_id, reaction=[{"type": "emoji", "emoji": "😁"}])
                        
                    # Отправляем результат выполнения функции только если функция была вызвана
                    input_data.extend([
                        {
                            "type": "function_call",
                            "call_id": tool_call.call_id,
                            "name": tool_call.name,
                            "arguments": tool_call.arguments
                        },
                        {
                            "type": "function_call_output",
                            "call_id": tool_call.call_id,
                            "output": json.dumps({"is_funny": is_funny})
                        }
                    ])
                except Exception as e:
                    logger.error(f"Ошибка при обработке tool_call: {e}")
            
            kwargs["input"] = input_data
            # Получаем финальный ответ
            response = client.responses.create(**kwargs)
            user_states[chat_id]['last_response_id'] = response.id

            # 4) Извлекаем текст из ответа
            if response.output and len(response.output) > 0:
                for output in response.output:
                    if hasattr(output, 'content') and output.content:
                        reply_text = output.content[0].text.strip()
                        break
                else:
                    reply_text = "Извините, я не смог сформировать ответ."
            else:
                reply_text = "Извините, я не смог сформировать ответ."

            # Обновляем запись в базе данных
            db_message.response = reply_text
            db_message.is_funny = is_funny
            await session.commit()

            # 5) Удаляем стикер и отправляем ответ
            await sticker_msg.delete()
            await message.answer(reply_text)

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от пользователя {user.id}: {str(e)}")
        await message.answer("Произошла ошибка при обработке вашего сообщения. Пожалуйста, попробуйте позже.")
    
    finally:
        user_states[chat_id]["is_processing"] = False
        logger.info(f"Завершена обработка сообщения от пользователя {user.id}")

async def main() -> None:
    """Запускает бота."""
    logger.info("Запуск бота...")
    
    # Инициализация бота с настройками по умолчанию
    bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    # Используем uvloop для улучшения производительности на Unix-системах
    if os.name != "nt":  # Проверяем, что не Windows
        import uvloop
        uvloop.install()
        logger.info("uvloop успешно установлен")

    logger.info("Бот успешно настроен и готов к работе")
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {str(e)}")
