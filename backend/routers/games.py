# backend/routers/games.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.database import get_db
from backend.database.models import Game, User
from backend.utils.dependencies import get_current_user
from typing import Optional, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class GameHistoryResponse(BaseModel):
    id: int
    game_type: str
    mode: str
    player1_id: int
    player2_id: Optional[int]
    winner_id: Optional[int]
    result: Optional[str]
    stake_amount_ton: float
    stake_amount_coins: float
    currency: str
    created_at: str
    finished_at: Optional[str]
    duration_seconds: Optional[int]
    
    class Config:
        from_attributes = True


@router.get("/history")
async def get_game_history(
    limit: int = 20,
    offset: int = 0,
    game_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить историю игр пользователя
    """
    try:
        query = select(Game).where(
            (Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)
        )
        
        if game_type:
            query = query.where(Game.game_type == game_type)
        
        query = query.order_by(Game.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        games = result.scalars().all()
        
        return {
            "games": [
                {
                    "id": g.id,
                    "game_type": g.game_type,
                    "mode": g.mode,
                    "player1_id": g.player1_id,
                    "player2_id": g.player2_id,
                    "winner_id": g.winner_id,
                    "result": g.result,
                    "stake_amount_ton": float(g.stake_amount_ton or 0),
                    "stake_amount_coins": float(g.stake_amount_coins or 0),
                    "currency": g.currency,
                    "created_at": g.created_at.isoformat(),
                    "finished_at": g.finished_at.isoformat() if g.finished_at else None,
                    "duration_seconds": g.duration_seconds
                }
                for g in games
            ],
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting game history for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get game history")


@router.get("/stats")
async def get_game_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить статистику игр пользователя
    """
    try:
        # Статистика по типам игр
        query = select(
            Game.game_type,
            func.count(Game.id).label("total_games"),
            func.sum(func.cast((Game.winner_id == current_user.id), func.Integer)).label("wins")
        ).where(
            (Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)
        ).group_by(Game.game_type)
        
        result = await db.execute(query)
        game_type_stats = result.all()
        
        return {
            "total_games_played": current_user.total_games_played or 0,
            "total_wins": current_user.total_wins or 0,
            "total_losses": current_user.total_losses or 0,
            "win_rate": round((current_user.total_wins / current_user.total_games_played * 100) 
                            if current_user.total_games_played > 0 else 0, 2),
            "total_won_ton": float(current_user.total_won_ton or 0),
            "total_staked_ton": float(current_user.total_staked_ton or 0),
            "total_won_coins": float(current_user.total_won_coins or 0),
            "total_staked_coins": float(current_user.total_staked_coins or 0),
            "by_game_type": [
                {
                    "game_type": stat.game_type,
                    "total_games": stat.total_games,
                    "wins": stat.wins or 0,
                    "win_rate": round((stat.wins / stat.total_games * 100) 
                                    if stat.total_games > 0 else 0, 2)
                }
                for stat in game_type_stats
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting game stats for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get game stats")


@router.get("/{game_id}")
async def get_game_details(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить детали конкретной игры
    """
    try:
        query = select(Game).where(Game.id == game_id)
        result = await db.execute(query)
        game = result.scalar_one_or_none()
        
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Проверяем, что пользователь участвовал в игре
        if game.player1_id != current_user.id and game.player2_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "id": game.id,
            "game_type": game.game_type,
            "mode": game.mode,
            "player1_id": game.player1_id,
            "player2_id": game.player2_id,
            "winner_id": game.winner_id,
            "result": game.result,
            "stake_amount_ton": float(game.stake_amount_ton or 0),
            "stake_amount_coins": float(game.stake_amount_coins or 0),
            "currency": game.currency,
            "game_state": game.game_state_json,
            "final_state": game.final_state_json,
            "move_count": game.move_count,
            "duration_seconds": game.duration_seconds,
            "started_at": game.started_at.isoformat() if game.started_at else None,
            "finished_at": game.finished_at.isoformat() if game.finished_at else None,
            "created_at": game.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game details {game_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get game details")