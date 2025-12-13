# backend/services/coin_service.py

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.database.models import User, CoinTransaction, DailyReward

logger = logging.getLogger(__name__)


class CoinService:
    """Сервис для работы с внутренней игровой валютой"""
    
    INITIAL_BONUS = Decimal("1000.00")  # Стартовый бонус
    DAILY_REWARD_BASE = Decimal("100.00")  # Базовая дневная награда
    DAILY_REWARD_STREAK_BONUS = Decimal("50.00")  # Бонус за серию
    MAX_STREAK_BONUS = 7  # Максимальная серия для бонуса
    
    @staticmethod
    async def get_balance(db: AsyncSession, user_id: int) -> Decimal:
        """Получить баланс коинов пользователя"""
        result = await db.execute(
            select(User.balance_coins).where(User.id == user_id)
        )
        balance = result.scalar_one_or_none()
        return balance or Decimal("0")
    
    @staticmethod
    async def add_coins(
        db: AsyncSession,
        user_id: int,
        amount: Decimal,
        transaction_type: str,
        description: Optional[str] = None,
        related_game_id: Optional[int] = None
    ) -> bool:
        """
        Добавить коины пользователю
        
        Args:
            user_id: ID пользователя
            amount: Количество коинов (положительное число)
            transaction_type: Тип транзакции
            description: Описание транзакции
            related_game_id: ID связанной игры (если есть)
        """
        try:
            # Получаем текущий баланс
            user = await db.execute(select(User).where(User.id == user_id))
            user = user.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            balance_before = user.balance_coins or Decimal("0")
            balance_after = balance_before + amount
            
            # Обновляем баланс
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(balance_coins=balance_after)
            )
            
            # Создаём запись транзакции
            transaction = CoinTransaction(
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                related_game_id=related_game_id,
                balance_before=balance_before,
                balance_after=balance_after
            )
            db.add(transaction)
            
            await db.commit()
            logger.info(f"Added {amount} coins to user {user_id}. New balance: {balance_after}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding coins to user {user_id}: {e}", exc_info=True)
            await db.rollback()
            return False
    
    @staticmethod
    async def deduct_coins(
        db: AsyncSession,
        user_id: int,
        amount: Decimal,
        transaction_type: str,
        description: Optional[str] = None,
        related_game_id: Optional[int] = None
    ) -> bool:
        """
        Списать коины у пользователя
        
        Args:
            user_id: ID пользователя
            amount: Количество коинов для списания (положительное число)
            transaction_type: Тип транзакции
            description: Описание транзакции
            related_game_id: ID связанной игры (если есть)
        """
        try:
            # Получаем текущий баланс
            user = await db.execute(select(User).where(User.id == user_id))
            user = user.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            balance_before = user.balance_coins or Decimal("0")
            
            # Проверяем достаточность средств
            if balance_before < amount:
                logger.warning(f"Insufficient coins for user {user_id}. Has: {balance_before}, needs: {amount}")
                return False
            
            balance_after = balance_before - amount
            
            # Обновляем баланс
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(balance_coins=balance_after)
            )
            
            # Создаём запись транзакции (с отрицательной суммой)
            transaction = CoinTransaction(
                user_id=user_id,
                amount=-amount,
                transaction_type=transaction_type,
                description=description,
                related_game_id=related_game_id,
                balance_before=balance_before,
                balance_after=balance_after
            )
            db.add(transaction)
            
            await db.commit()
            logger.info(f"Deducted {amount} coins from user {user_id}. New balance: {balance_after}")
            return True
            
        except Exception as e:
            logger.error(f"Error deducting coins from user {user_id}: {e}", exc_info=True)
            await db.rollback()
            return False
    
    @staticmethod
    async def claim_daily_reward(db: AsyncSession, user_id: int) -> dict:
        """
        Получить ежедневную награду
        
        Returns:
            dict: {"success": bool, "coins_earned": Decimal, "streak_days": int, "message": str}
        """
        try:
            today = date.today()
            
            # Проверяем, получал ли уже награду сегодня
            existing = await db.execute(
                select(DailyReward)
                .where(DailyReward.user_id == user_id, DailyReward.reward_date == today)
            )
            if existing.scalar_one_or_none():
                return {
                    "success": False,
                    "coins_earned": Decimal("0"),
                    "streak_days": 0,
                    "message": "Already claimed today"
                }
            
            # Получаем последнюю награду
            last_reward = await db.execute(
                select(DailyReward)
                .where(DailyReward.user_id == user_id)
                .order_by(DailyReward.reward_date.desc())
                .limit(1)
            )
            last_reward = last_reward.scalar_one_or_none()
            
            # Вычисляем серию
            if last_reward:
                from datetime import timedelta
                yesterday = today - timedelta(days=1)
                if last_reward.reward_date == yesterday:
                    # Продолжение серии
                    streak_days = min(last_reward.streak_days + 1, CoinService.MAX_STREAK_BONUS)
                else:
                    # Серия прервана
                    streak_days = 1
            else:
                # Первая награда
                streak_days = 1
            
            # Вычисляем награду
            coins_earned = CoinService.DAILY_REWARD_BASE
            if streak_days > 1:
                bonus = CoinService.DAILY_REWARD_STREAK_BONUS * (streak_days - 1)
                coins_earned += bonus
            
            # Создаём запись награды
            reward = DailyReward(
                user_id=user_id,
                reward_date=today,
                coins_earned=coins_earned,
                streak_days=streak_days
            )
            db.add(reward)
            
            # Добавляем коины
            await CoinService.add_coins(
                db=db,
                user_id=user_id,
                amount=coins_earned,
                transaction_type="daily_bonus",
                description=f"Daily reward (streak: {streak_days} days)"
            )
            
            return {
                "success": True,
                "coins_earned": coins_earned,
                "streak_days": streak_days,
                "message": f"Claimed {coins_earned} coins! Streak: {streak_days} days"
            }
            
        except Exception as e:
            logger.error(f"Error claiming daily reward for user {user_id}: {e}", exc_info=True)
            await db.rollback()
            return {
                "success": False,
                "coins_earned": Decimal("0"),
                "streak_days": 0,
                "message": "Error claiming reward"
            }
    
    @staticmethod
    async def get_streak_info(db: AsyncSession, user_id: int) -> dict:
        """
        Получить информацию о текущей серии
        
        Returns:
            dict: {"current_streak": int, "can_claim_today": bool}
        """
        try:
            today = date.today()
            
            # Проверяем, получал ли награду сегодня
            today_reward = await db.execute(
                select(DailyReward)
                .where(DailyReward.user_id == user_id, DailyReward.reward_date == today)
            )
            can_claim_today = today_reward.scalar_one_or_none() is None
            
            # Получаем последнюю награду
            last_reward = await db.execute(
                select(DailyReward)
                .where(DailyReward.user_id == user_id)
                .order_by(DailyReward.reward_date.desc())
                .limit(1)
            )
            last_reward = last_reward.scalar_one_or_none()
            
            if not last_reward:
                return {"current_streak": 0, "can_claim_today": True}
            
            # Проверяем актуальность серии
            from datetime import timedelta
            yesterday = today - timedelta(days=1)
            
            if last_reward.reward_date == today:
                current_streak = last_reward.streak_days
            elif last_reward.reward_date == yesterday:
                current_streak = last_reward.streak_days
            else:
                current_streak = 0
            
            return {
                "current_streak": current_streak,
                "can_claim_today": can_claim_today
            }
            
        except Exception as e:
            logger.error(f"Error getting streak info for user {user_id}: {e}", exc_info=True)
            return {"current_streak": 0, "can_claim_today": False}


# Экспортируем единственный экземпляр
coin_service = CoinService()