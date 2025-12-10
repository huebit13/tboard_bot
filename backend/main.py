from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, get_db, Base, AsyncSession 
from backend.schemas.user import UserCreate, WalletConnect
from backend.crud.user import create_or_update_user, connect_wallet
from backend.routers import users
from datetime import timedelta
from backend.utils.jwt import create_access_token, verify_token
from backend.managers.game_manager import game_manager
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

        access_token_data = {"sub": user.id} 
        access_token = create_access_token(data=access_token_data, expires_delta=timedelta(hours=1))
        
        return {
            "status": "ok",
            "message": "User authenticated",
            "access_token": access_token,
            "token_type": "bearer",
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

@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    # Проверяем токен из URL-параметра (например, /ws/game?token=...)
    token = websocket.query_params.get("token")
    if not token:
        logger.warning("WebSocket connection attempt without token.")
        await websocket.close(code=1008) # Policy Violation
        return

    user_data = verify_token(token)
    if not user_data:
        logger.warning("WebSocket connection attempt with invalid token.")
        await websocket.close(code=1008) # Policy Violation
        return

    user_id = user_data["user_id"]
    logger.info(f"WebSocket connection attempt for user {user_id}.")

    # Подключаем пользователя через менеджер
    await game_manager.connect_user(websocket, user_id)

    try:
        while True:
            # Ждём сообщение от клиента
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "join_queue":
                game_type = data.get("game_type", "rps") # По умолчанию RPS
                stake = data.get("stake")
                if stake is None:
                    await websocket.send_json({"type": "error", "message": "Stake is required to join queue."})
                    continue
                # Добавляем в очередь через менеджер
                await game_manager.add_to_queue(user_id, game_type, stake)

            elif action == "make_move":
                game_id = data.get("game_id")
                move = data.get("move")
                if not game_id or not move:
                    await websocket.send_json({"type": "error", "message": "Game ID and move are required."})
                    continue
                # Обрабатываем ход через менеджер
                await game_manager.handle_player_move(game_id, user_id, move)

            # Добавьте другие действия по мере необходимости (например, leave_queue)

    except WebSocketDisconnect:
        # Обрабатываем отключение клиента
        game_manager.disconnect_user(user_id)
        logger.info(f"WebSocket disconnected for user {user_id}.")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for user {user_id}: {e}")
        game_manager.disconnect_user(user_id)


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