# backend/routers/coins.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.services.coin_service import coin_service
from backend.utils.dependencies import get_current_user
from backend.database.models import User
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class CoinTransactionResponse(BaseModel):
    id: int
    amount: float
    transaction_type: str
    description: Optional[str]
    balance_before: float
    balance_after: float
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/balance")
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить текущий баланс коинов пользователя
    """
    try:
        balance = await coin_service.get_balance(db, current_user.id)
        return {
            "user_id": current_user.id,
            "balance": float(balance),
            "currency": "COINS"
        }
    except Exception as e:
        logger.error(f"Error getting balance for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get balance")


@router.post("/daily-reward")
async def claim_daily_reward(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить ежедневную награду
    """
    try:
        result = await coin_service.claim_daily_reward(db, current_user.id)
        
        if not result["success"]:
            if result["message"] == "Already claimed today":
                raise HTTPException(status_code=400, detail="Daily reward already claimed today")
            else:
                raise HTTPException(status_code=500, detail=result["message"])
        
        return {
            "success": True,
            "coins_earned": float(result["coins_earned"]),
            "streak_days": result["streak_days"],
            "message": result["message"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error claiming daily reward for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to claim daily reward")


@router.get("/daily-reward/status")
async def get_daily_reward_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить статус ежедневной награды (можно ли забрать сегодня)
    """
    try:
        streak_info = await coin_service.get_streak_info(db, current_user.id)
        
        return {
            "can_claim_today": streak_info["can_claim_today"],
            "current_streak": streak_info["current_streak"],
            "next_reward": float(coin_service.DAILY_REWARD_BASE + 
                               coin_service.DAILY_REWARD_STREAK_BONUS * streak_info["current_streak"])
        }
        
    except Exception as e:
        logger.error(f"Error getting daily reward status for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get daily reward status")


@router.get("/transactions")
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить историю транзакций коинов
    """
    try:
        from sqlalchemy import select
        from backend.database.models import CoinTransaction
        
        query = (
            select(CoinTransaction)
            .where(CoinTransaction.user_id == current_user.id)
            .order_by(CoinTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return {
            "transactions": [
                {
                    "id": t.id,
                    "amount": float(t.amount),
                    "transaction_type": t.transaction_type,
                    "description": t.description,
                    "balance_before": float(t.balance_before),
                    "balance_after": float(t.balance_after),
                    "created_at": t.created_at.isoformat(),
                    "related_game_id": t.related_game_id
                }
                for t in transactions
            ],
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting transactions for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get transactions")


@router.get("/stats")
async def get_coin_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить статистику по коинам
    """
    try:
        from sqlalchemy import select, func
        from backend.database.models import CoinTransaction
        
        # Получаем агрегированную статистику
        query = select(
            func.sum(CoinTransaction.amount).filter(CoinTransaction.amount > 0).label("total_earned"),
            func.sum(CoinTransaction.amount).filter(CoinTransaction.amount < 0).label("total_spent"),
            func.count(CoinTransaction.id).label("total_transactions")
        ).where(CoinTransaction.user_id == current_user.id)
        
        result = await db.execute(query)
        stats = result.first()
        
        return {
            "current_balance": float(current_user.balance_coins or 0),
            "total_earned": float(stats.total_earned or 0),
            "total_spent": abs(float(stats.total_spent or 0)),
            "total_transactions": stats.total_transactions or 0,
            "total_won_coins": float(current_user.total_won_coins or 0),
            "total_staked_coins": float(current_user.total_staked_coins or 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting coin stats for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get coin stats")