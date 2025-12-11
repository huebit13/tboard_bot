from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, get_db, Base, AsyncSession 
from backend.schemas.user import UserCreate, WalletConnect
from backend.crud.user import create_or_update_user, connect_wallet
from backend.routers import users
from datetime import timedelta, datetime
from backend.utils.jwt import create_access_token, verify_token
from backend.managers.game_manager import game_manager
from backend.database.models import Game, User, Lobby
from sqlalchemy import select
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TBoard Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tboard.space",
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

app.include_router(users.router, prefix="/api", tags=["users"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

_background_tasks = set()


@app.post("/api/auth/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)): 
    try:
        logger.info("Login endpoint called")
        body = await request.json()
        init_data = body.get("initData")
        
        if not init_data:
            logger.warning("Init data is missing in request")
            raise HTTPException(status_code=400, detail="Init data is required")
        
        params = {}
        for pair in init_data.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                if key != "hash":
                    import urllib.parse
                    params[key] = urllib.parse.unquote(value)
        
        if 'user' not in params:
            logger.warning("User data not found in init data")
            raise HTTPException(status_code=400, detail="User data not found")
        
        user_data = json.loads(params['user'])
        telegram_id = user_data.get("id")
        username = user_data.get("username")
        
        if not telegram_id:
            logger.warning("Telegram ID not found in user data")
            raise HTTPException(status_code=400, detail="Telegram ID not found")
        
        logger.info(f"Processing user: telegram_id={telegram_id}, username={username}")

        user = await create_or_update_user(
            db=db,
            telegram_id=telegram_id,
            username=username
        )
        
        logger.info(f"User processed successfully: telegram_id={telegram_id}, id={user.id if user else 'None'}")

        access_token_data = {"sub": str(user.id)} 
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
        logger.error("HTTPException in login", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint для игровых взаимодействий.
    Требует токен в query параметрах: /ws/game?token=<JWT_TOKEN>
    """
    try:
        logger.info(f"WebSocket connection attempt from {websocket.client}")
        
        token = websocket.query_params.get("token")
        if not token:
            logger.warning("WebSocket connection attempt without token.")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
            return

        user_data = verify_token(token)
        if not user_data:
            logger.warning(f"WebSocket connection attempt with invalid token: {token[:20]}...")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return

        user_id = user_data["user_id"]
        logger.info(f"WebSocket authenticated for user {user_id}")

        await game_manager.connect_user(websocket, user_id)
        
        await websocket.send_json({
            "type": "connected",
            "message": "Successfully connected to game server",
            "user_id": user_id
        })

        while True:
            try:
                data = await websocket.receive_json()
                logger.info(f"Received message from user {user_id}: {data}")
                
                action = data.get("action")

                if action == "join_queue":
                    game_type = data.get("game_type", "rps")
                    stake = data.get("stake")
                    if stake is None:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Stake is required to join queue."
                        })
                        continue
                    await game_manager.add_to_queue(user_id, game_type, stake)
                    await websocket.send_json({
                        "type": "queue_joined",
                        "message": f"Joined queue for {game_type} with stake {stake}"
                    })

                elif action == "get_lobby_list":
                    from backend.database import AsyncSessionLocal
                    async with AsyncSessionLocal() as db:
                        now = datetime.utcnow()
                        result = await db.execute(
                            select(Lobby, User.username)
                            .join(User, Lobby.creator_id == User.id)
                            .where(Lobby.status == "waiting", Lobby.expires_at > now)
                        )
                        lobbies = []
                        for lobby, username in result:
                            lobbies.append({
                                "id": lobby.id,
                                "game_type": lobby.game_type,
                                "stake": float(lobby.stake),
                                "has_password": lobby.password_hash is not None,
                                "creator_id": lobby.creator_id,
                                "creator_name": username or "Player",
                                "players_count": 1
                            })
                        await websocket.send_json({
                            "type": "lobby_list",
                            "lobbies": lobbies
                        })

                elif action == "create_lobby":
                    game_type = data.get("game_type")
                    stake = data.get("stake")
                    password = data.get("password")
                    if not game_type or stake is None:
                        await websocket.send_json({"type": "error", "message": "game_type and stake required"})
                        continue
                    lobby_id = await game_manager.create_lobby(user_id, game_type, stake, password)
                    await websocket.send_json({
                        "type": "lobby_created",
                        "lobby_id": lobby_id,
                        "game_type": game_type,
                        "stake": stake,
                        "has_password": password is not None
                    })

                elif action == "join_lobby":
                    lobby_id = data.get("lobby_id")
                    password = data.get("password")
                    if not lobby_id:
                        await websocket.send_json({"type": "error", "message": "lobby_id required"})
                        continue
                    success, msg = await game_manager.join_lobby(user_id, lobby_id, password)
                    if success:
                        lobby = game_manager.active_lobbies[lobby_id]
                        await game_manager._send_to_user(lobby["creator_id"], {
                            "type": "lobby_joined",
                            "lobby_id": lobby_id,
                            "joiner_id": user_id
                        })
                        await websocket.send_json({
                            "type": "lobby_joined",
                            "lobby_id": lobby_id,
                            "creator_id": lobby["creator_id"]
                        })
                    else:
                        await websocket.send_json({"type": "error", "message": msg})

                elif action == "set_lobby_ready":
                    lobby_id = data.get("lobby_id")
                    is_ready = data.get("is_ready", False)
                    if lobby_id:
                        await game_manager.set_lobby_ready(user_id, lobby_id, is_ready)
                        if lobby_id in game_manager.active_lobbies:
                            lobby = game_manager.active_lobbies[lobby_id]
                            for uid in [lobby["creator_id"], lobby["joiner_id"]]:
                                if uid:
                                    await game_manager._send_to_user(uid, {
                                        "type": "lobby_updated",
                                        "lobby_id": lobby_id,
                                        "players": [
                                            {"user_id": lobby["creator_id"], "ready": lobby["creator_ready"]},
                                            {"user_id": lobby["joiner_id"], "ready": lobby["joiner_ready"]} if lobby["joiner_id"] else None
                                        ]
                                    })

                elif action == "kick_player":
                    lobby_id = data.get("lobby_id")
                    target_id = data.get("target_id")
                    if lobby_id and target_id:
                        success = await game_manager.kick_from_lobby(user_id, lobby_id, target_id)
                        if success:
                            await game_manager._send_to_user(target_id, {
                                "type": "kicked_from_lobby",  # ✅ исправлена опечатка
                                "lobby_id": lobby_id
                            })
                            lobby = game_manager.active_lobbies[lobby_id]
                            await game_manager._send_to_user(lobby["creator_id"], {
                                "type": "lobby_updated",
                                "lobby_id": lobby_id,
                                "players": [{"user_id": lobby["creator_id"], "ready": False}]
                            })

                elif action == "leave_queue":
                    await websocket.send_json({
                        "type": "queue_left",
                        "message": "Left the queue"
                    })

                elif action == "make_move":
                    game_id = data.get("game_id")
                    move = data.get("move")
                    if not game_id or not move:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Game ID and move are required."
                        })
                        continue
                    await game_manager.handle_player_move(game_id, user_id, move)
                
                elif action == "leave_lobby":
                    lobby_id = data.get("lobby_id")
                    if lobby_id:
                        await game_manager.leave_lobby(user_id, lobby_id)
                        await websocket.send_json({
                            "type": "lobby_left",
                            "lobby_id": lobby_id
                        })

                elif action == "ping":
                    await websocket.send_json({"type": "pong"})

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from user {user_id}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error processing message from user {user_id}: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal server error"
                })

    except WebSocketDisconnect:
        if 'user_id' in locals():
            game_manager.disconnect_user(user_id)
            lobbies_to_remove = []
            for lid, lobby in game_manager.active_lobbies.items():
                if lobby["creator_id"] == user_id:
                    lobbies_to_remove.append(lid)
            for lid in lobbies_to_remove:
                del game_manager.active_lobbies[lid]
            logger.info(f"WebSocket disconnected for user {user_id}. Cleaned up {len(lobbies_to_remove)} lobbies.")
        else:
            logger.info("WebSocket disconnected before authentication")
    
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {e}", exc_info=True)
        if 'user_id' in locals():
            game_manager.disconnect_user(user_id)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"message": "Test WebSocket works!"})
    logger.info("Test WebSocket connected")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"echo": data})
    except WebSocketDisconnect:
        logger.info("Test WebSocket disconnected")

async def cleanup_expired_lobbies():
    while True:
        await asyncio.sleep(300)  # 5 минут
        from datetime import datetime
        now = datetime.utcnow()
        expired = []
        for lid, lobby in list(game_manager.active_lobbies.items()):
            # Убедись, что в lobby есть expires_at (возможно, его нет)
            expires_at = lobby.get("expires_at")
            if expires_at and expires_at < now:
                expired.append(lid)

        for lid in expired:
            logger.info(f"Cleaning up expired lobby {lid}")
            del game_manager.active_lobbies[lid]
            # Опционально: удалить из БД
            from backend.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                db_lobby = await db.get(Lobby, lid)
                if db_lobby:
                    await db.delete(db_lobby)
                    await db.commit()


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Application started successfully")

    task = asyncio.create_task(cleanup_expired_lobbies())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


@app.get("/")
def read_root():
    return {"message": "TBoard Backend is running!"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "tboard-backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)