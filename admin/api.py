from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List
from .database import async_session
from .models import User, Message
from pydantic import BaseModel

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зависимость для получения сессии базы данных
async def get_db():
    async with async_session() as session:
        yield session

# Pydantic модели
class UserStats(BaseModel):
    total_users: int
    active_users_today: int
    total_messages: int
    funny_messages: int

class MessageResponse(BaseModel):
    id: int
    content: str
    response: str | None
    is_funny: bool
    created_at: datetime
    user_full_name: str

@app.get("/api/stats", response_model=UserStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Получение общей статистики"""
    today = datetime.utcnow().date()
    
    # Общее количество пользователей
    total_users = await db.scalar(select(func.count(User.id)))
    
    # Активные пользователи за сегодня
    active_users = await db.scalar(
        select(func.count(User.id))
        .select_from(Message)
        .join(User)
        .where(func.date(Message.created_at) == today)
    )
    
    # Общее количество сообщений
    total_messages = await db.scalar(select(func.count(Message.id)))
    
    # Количество смешных сообщений
    funny_messages = await db.scalar(
        select(func.count(Message.id))
        .where(Message.is_funny == True)
    )
    
    return UserStats(
        total_users=total_users,
        active_users_today=active_users,
        total_messages=total_messages,
        funny_messages=funny_messages
    )

@app.get("/api/messages", response_model=List[MessageResponse])
async def get_messages(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Получение списка сообщений с пагинацией"""
    query = (
        select(Message, User.full_name)
        .join(User)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(query)
    messages = []
    
    for msg, user_full_name in result:
        messages.append(
            MessageResponse(
                id=msg.id,
                content=msg.content,
                response=msg.response,
                is_funny=msg.is_funny,
                created_at=msg.created_at,
                user_full_name=user_full_name
            )
        )
    
    return messages 