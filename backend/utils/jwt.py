import os
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
    """
    Проверяет JWT-токен и возвращает встроенные данные (например, user_id).
    :param token: Токен для проверки.
    :return: Данные из токена (dict) или None, если токен недействителен.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub") 
        if user_id is None:
            return None
        return {"user_id": user_id}
    except jwt.ExpiredSignatureError:
        
        return None
    except jwt.JWTError:
        
        return None
    except Exception:
        return None
