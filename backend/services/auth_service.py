# backend/services/auth_service.py

import json
import logging
from datetime import timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.crud.user import create_or_update_user
from backend.utils.jwt import create_access_token
from backend.services.coin_service import coin_service
from decimal import Decimal

logger = logging.getLogger(__name__)


class AuthService:
    """Сервис для аутентификации и авторизации"""
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, init_data: str) -> Dict[str, Any]:
        """
        Аутентифицирует пользователя через Telegram initData
        
        Args:
            db: Сессия БД
            init_data: Строка initData от Telegram WebApp
            
        Returns:
            dict: {"success": bool, "user": dict, "access_token": str, "message": str}
        """
        try:
            # Парсим initData
            params = {}
            for pair in init_data.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    if key != "hash":
                        import urllib.parse
                        params[key] = urllib.parse.unquote(value)
            
            if 'user' not in params:
                return {
                    "success": False,
                    "message": "User data not found in initData"
                }
            
            # Парсим данные пользователя
            user_data = json.loads(params['user'])
            telegram_id = user_data.get("id")
            username = user_data.get("username")
            
            if not telegram_id:
                return {
                    "success": False,
                    "message": "Telegram ID not found"
                }
            
            logger.info(f"Authenticating user: telegram_id={telegram_id}, username={username}")
            
            # Создаём или обновляем пользователя
            user = await create_or_update_user(
                db=db,
                telegram_id=telegram_id,
                username=username
            )
            
            # Проверяем, новый ли это пользователь (нужен стартовый бонус)
            if user.balance_coins == 0 or user.balance_coins is None:
                logger.info(f"New user detected, giving initial bonus: user_id={user.id}")
                await coin_service.add_coins(
                    db=db,
                    user_id=user.id,
                    amount=Decimal("1000.00"),
                    transaction_type="initial_bonus",
                    description="Welcome bonus for new user"
                )
                # Обновляем баланс в объекте user
                await db.refresh(user)
            
            # Создаём access token
            access_token_data = {"sub": str(user.id)}
            access_token = create_access_token(
                data=access_token_data,
                expires_delta=timedelta(hours=24)
            )
            
            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "balance_ton": float(user.balance_ton) if user.balance_ton else 0.0,
                    "balance_coins": float(user.balance_coins) if user.balance_coins else 0.0,
                    "referral_link": user.referral_link,
                    "total_games_played": user.total_games_played or 0,
                    "total_wins": user.total_wins or 0,
                    "total_losses": user.total_losses or 0
                },
                "access_token": access_token,
                "message": "Authentication successful"
            }
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Authentication failed: {str(e)}"
            }
    
    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
        """
        Обновляет access token используя refresh token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            dict: {"success": bool, "access_token": str, "message": str}
        """
        try:
            from backend.utils.jwt import verify_token
            
            # Верифицируем refresh token
            payload = verify_token(refresh_token)
            
            if not payload:
                return {
                    "success": False,
                    "message": "Invalid or expired refresh token"
                }
            
            # Создаём новый access token
            access_token_data = {"sub": str(payload["user_id"])}
            access_token = create_access_token(
                data=access_token_data,
                expires_delta=timedelta(hours=24)
            )
            
            return {
                "success": True,
                "access_token": access_token,
                "message": "Token refreshed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Token refresh failed: {str(e)}"
            }


# Экспортируем единственный экземпляр
auth_service = AuthService()