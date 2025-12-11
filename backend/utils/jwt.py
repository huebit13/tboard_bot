import os
import logger
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be set in environment variables")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256") # По умолчанию HS256


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Создает JWT-токен.
    :param data: Данные для включения в токен (например, user_id).
    :param expires_delta: Время жизни токена. По умолчанию 1 час.
    :return: Строка токена.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=1) # Токен жив 1 час
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        
        if user_id is None:
            logger.warning("Token verification failed: 'sub' claim missing")
            return None
        
        logger.info(f"Token verified successfully for user_id: {user_id}")
        return {"user_id": user_id}
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed: token expired")
        return None
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token verification failed: invalid token - {str(e)}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}", exc_info=True)
        return None