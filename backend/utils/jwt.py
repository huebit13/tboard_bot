import os
import logging
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be set in environment variables")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        
        if user_id_str is None:
            logger.warning("Token verification failed: 'sub' claim missing")
            return None
        
        user_id = int(user_id_str)
        
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