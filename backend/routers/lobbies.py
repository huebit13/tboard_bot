# backend/routers/lobbies.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.database.models import Lobby, User
from backend.utils.dependencies import get_current_user
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class LobbyResponse(BaseModel):
    id: int
    game_type: str
    stake: float
    currency: str
    has_password: bool
    creator_id: int
    creator_name: Optional[str]
    joiner_id: Optional[int]
    joiner_name: Optional[str]
    status: str
    players_count: int
    created_at: str
    expires_at: str
    
    class Config:
        from_attributes = True


@router.get("/list")
async def get_lobby_list(
    game_type: Optional[str] = None,
    currency: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список активных лобби (HTTP версия для обновления списка)
    """
    try:
        now = datetime.utcnow()
        
        query = (
            select(Lobby, User.username.label("creator_username"))
            .join(User, Lobby.creator_id == User.id)
            .where(Lobby.status == "waiting", Lobby.expires_at > now)
        )
        
        if game_type:
            query = query.where(Lobby.game_type == game_type)
        
        if currency:
            query = query.where(Lobby.currency == currency)
        
        result = await db.execute(query)
        lobbies_data = result.all()
        
        lobbies = []
        for lobby, creator_username in lobbies_data:
            # Получаем имя второго игрока если есть
            joiner_username = None
            if lobby.joiner_id:
                joiner_query = select(User.username).where(User.id == lobby.joiner_id)
                joiner_result = await db.execute(joiner_query)
                joiner_username = joiner_result.scalar_one_or_none()
            
            lobbies.append({
                "id": lobby.id,
                "game_type": lobby.game_type,
                "stake": float(lobby.stake),
                "currency": lobby.currency,
                "has_password": lobby.password_hash is not None,
                "creator_id": lobby.creator_id,
                "creator_name": creator_username or "Player",
                "joiner_id": lobby.joiner_id,
                "joiner_name": joiner_username,
                "status": lobby.status,
                "players_count": 2 if lobby.joiner_id else 1,
                "created_at": lobby.created_at.isoformat(),
                "expires_at": lobby.expires_at.isoformat()
            })
        
        return {
            "lobbies": lobbies,
            "total": len(lobbies)
        }
        
    except Exception as e:
        logger.error(f"Error getting lobby list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get lobby list")


@router.get("/{lobby_id}")
async def get_lobby_details(
    lobby_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить детали конкретного лобби
    """
    try:
        query = select(Lobby).where(Lobby.id == lobby_id)
        result = await db.execute(query)
        lobby = result.scalar_one_or_none()
        
        if not lobby:
            raise HTTPException(status_code=404, detail="Lobby not found")
        
        # Получаем имена игроков
        creator_query = select(User.username).where(User.id == lobby.creator_id)
        creator_result = await db.execute(creator_query)
        creator_name = creator_result.scalar_one_or_none()
        
        joiner_name = None
        if lobby.joiner_id:
            joiner_query = select(User.username).where(User.id == lobby.joiner_id)
            joiner_result = await db.execute(joiner_query)
            joiner_name = joiner_result.scalar_one_or_none()
        
        return {
            "id": lobby.id,
            "game_type": lobby.game_type,
            "stake": float(lobby.stake),
            "currency": lobby.currency,
            "has_password": lobby.password_hash is not None,
            "creator_id": lobby.creator_id,
            "creator_name": creator_name or "Player",
            "joiner_id": lobby.joiner_id,
            "joiner_name": joiner_name,
            "status": lobby.status,
            "players_count": 2 if lobby.joiner_id else 1,
            "created_at": lobby.created_at.isoformat(),
            "expires_at": lobby.expires_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lobby details {lobby_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get lobby details")