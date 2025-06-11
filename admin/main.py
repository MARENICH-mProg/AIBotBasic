from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from typing import List
from . import models, security
from .database import get_db, engine
import json

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создание таблиц при запуске
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

# Аутентификация
@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.Admin).where(models.Admin.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Получение статистики
@app.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: models.Admin = Depends(security.get_current_user)
):
    # Получаем общее количество пользователей
    result = await db.execute(select(models.User))
    total_users = len(result.scalars().all())
    
    # Получаем общее количество сообщений
    result = await db.execute(select(models.Message))
    total_messages = len(result.scalars().all())
    
    # Получаем количество смешных сообщений
    result = await db.execute(select(models.Message).where(models.Message.is_funny == True))
    funny_messages = len(result.scalars().all())
    
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "funny_messages": funny_messages
    }

# Получение последних сообщений
@app.get("/messages")
async def get_messages(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: models.Admin = Depends(security.get_current_user)
):
    result = await db.execute(
        select(models.Message)
        .join(models.User)
        .order_by(models.Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return [
        {
            "id": msg.id,
            "content": msg.content,
            "response": msg.response,
            "is_funny": msg.is_funny,
            "created_at": msg.created_at,
            "user": {
                "id": msg.user.id,
                "telegram_id": msg.user.telegram_id,
                "username": msg.user.username,
                "full_name": msg.user.full_name
            }
        }
        for msg in messages
    ]

# Создание администратора (использовать только при первом запуске)
@app.post("/create-admin")
async def create_admin(
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Admin).where(models.Admin.username == username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Администратор с таким именем уже существует"
        )
    
    admin = models.Admin(
        username=username,
        hashed_password=security.get_password_hash(password)
    )
    db.add(admin)
    await db.commit()
    return {"message": "Администратор успешно создан"} 