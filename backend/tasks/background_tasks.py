# backend/tasks/background_tasks.py

import asyncio
import logging
from datetime import datetime, timedelta
from backend.managers.game_manager import game_manager
from backend.database import AsyncSessionLocal
from backend.database.models import Lobby

logger = logging.getLogger(__name__)

_background_tasks = set()
_running = False


async def cleanup_expired_lobbies():
    """Очистка истёкших лобби каждые 5 минут"""
    while _running:
        try:
            await asyncio.sleep(300)  # 5 минут
            
            now = datetime.utcnow()
            expired = []
            
            # Проверяем лобби в памяти
            for lid, lobby in list(game_manager.active_lobbies.items()):
                expires_at = lobby.get("expires_at")
                if expires_at and expires_at < now:
                    expired.append(lid)
            
            # Удаляем из памяти
            for lid in expired:
                logger.info(f"Cleaning up expired lobby {lid}")
                del game_manager.active_lobbies[lid]
            
            # Удаляем из БД
            if expired:
                async with AsyncSessionLocal() as db:
                    for lid in expired:
                        db_lobby = await db.get(Lobby, lid)
                        if db_lobby:
                            await db.delete(db_lobby)
                    await db.commit()
                
                logger.info(f"Cleaned up {len(expired)} expired lobbies")
                
        except Exception as e:
            logger.error(f"Error in cleanup_expired_lobbies: {e}", exc_info=True)


async def cleanup_abandoned_games():
    """Очистка заброшенных игр (игры без активности > 30 минут)"""
    while _running:
        try:
            await asyncio.sleep(600)  # 10 минут
            
            now = datetime.utcnow()
            abandoned_timeout = timedelta(minutes=30)
            
            abandoned = []
            
            for game_id, game in list(game_manager.active_games.items()):
                time_since_creation = now - game.created_at
                if time_since_creation > abandoned_timeout:
                    abandoned.append(game_id)
            
            for game_id in abandoned:
                logger.warning(f"Cleaning up abandoned game {game_id}")
                # Завершаем игру как ничью
                await game_manager._end_game(game_id, winner_id=None)
            
            if abandoned:
                logger.info(f"Cleaned up {len(abandoned)} abandoned games")
                
        except Exception as e:
            logger.error(f"Error in cleanup_abandoned_games: {e}", exc_info=True)


def start():
    """Запустить фоновые задачи"""
    global _running
    _running = True
    
    # Очистка лобби
    task1 = asyncio.create_task(cleanup_expired_lobbies())
    _background_tasks.add(task1)
    task1.add_done_callback(_background_tasks.discard)
    
    # Очистка игр
    task2 = asyncio.create_task(cleanup_abandoned_games())
    _background_tasks.add(task2)
    task2.add_done_callback(_background_tasks.discard)
    
    logger.info("Background tasks started")


def stop():
    """Остановить фоновые задачи"""
    global _running
    _running = False
    
    for task in _background_tasks:
        task.cancel()
    
    logger.info("Background tasks stopped")