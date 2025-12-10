from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, get_db, Base, AsyncSession 
from backend.schemas.user import UserCreate, WalletConnect
from backend.crud.user import create_or_update_user, connect_wallet
from backend.routers import users
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TBoard Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api", tags=["users"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@app.post("/api/auth/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)): 
    try:
        logger.info("Login endpoint called") # Добавьте лог
        body = await request.json()
        init_data = body.get("initData")
        
        if not init_data:
            logger.warning("Init data is missing in request") # Добавьте лог
            raise HTTPException(status_code=400, detail="Init data is required")
        
        # Парсим initData
        params = {}
        for pair in init_data.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                if key != "hash":
                    import urllib.parse
                    params[key] = urllib.parse.unquote(value)
        
        # Получаем данные пользователя
        if 'user' not in params:
            logger.warning("User data not found in init data") # Добавьте лог
            raise HTTPException(status_code=400, detail="User data not found")
        
        user_data = json.loads(params['user'])
        telegram_id = user_data.get("id")
        username = user_data.get("username")
        
        if not telegram_id:
            logger.warning("Telegram ID not found in user data") # Добавьте лог
            raise HTTPException(status_code=400, detail="Telegram ID not found")
        
        logger.info(f"Processing user: telegram_id={telegram_id}, username={username}") # Добавьте лог

        # Создаем/обновляем пользователя
        user = await create_or_update_user(
            db=db,
            telegram_id=telegram_id,
            username=username
        )
        
        logger.info(f"User processed successfully: telegram_id={telegram_id}, id={user.id if user else 'None'}") # Добавьте лог
        
        return {
            "status": "ok",
            "message": "User authenticated",
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "balance_ton": float(user.balance_ton) if user.balance_ton else 0.0,
                "referral_link": user.referral_link
            }
        }
        
    except HTTPException:
        logger.error("HTTPException in login", exc_info=True) # Добавьте лог
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}", exc_info=True) # Добавьте лог
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(users.router, prefix="/api", tags=["users"])


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def read_root():
    return {"message": "TBoard Backend is running!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)