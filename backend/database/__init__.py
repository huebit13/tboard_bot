# backend/database/__init__.py

# Импортируем нужные объекты из connection.py
from .connection import engine, AsyncSessionLocal as SessionLocal, get_db, Base # Добавлен Base
from .models import User, Game, Referral
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["engine", "SessionLocal", "get_db", "User", "Game", "Referral", "AsyncSession", "Base"] # Добавлен Base