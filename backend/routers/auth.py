# backend/routers/auth.py

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.services.auth_service import auth_service
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Аутентификация пользователя через Telegram WebApp initData
    
    Ожидает JSON: {"initData": "query_id=...&user=...&hash=..."}
    Возвращает: access_token и информацию о пользователе
    """
    try:
        logger.info("Login endpoint called")
        body = await request.json()
        init_data = body.get("initData")
        
        if not init_data:
            logger.warning("Init data is missing in request")
            raise HTTPException(status_code=400, detail="Init data is required")
        
        # Аутентификация через сервис
        result = await auth_service.authenticate_user(db, init_data)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        logger.info(f"User authenticated successfully: telegram_id={result['user']['telegram_id']}")
        
        return {
            "status": "ok",
            "message": "User authenticated",
            "access_token": result["access_token"],
            "token_type": "bearer",
            "user": result["user"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Обновление access токена
    
    Ожидает JSON: {"refresh_token": "..."}
    """
    try:
        body = await request.json()
        refresh_token = body.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is required")
        
        result = await auth_service.refresh_access_token(refresh_token)
        
        if not result["success"]:
            raise HTTPException(status_code=401, detail=result["message"])
        
        return {
            "status": "ok",
            "access_token": result["access_token"],
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))