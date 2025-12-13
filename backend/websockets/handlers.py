# backend/websockets/handlers.py

from fastapi import WebSocket
from backend.managers.game_manager import game_manager
from backend.database import AsyncSessionLocal
from backend.database.models import Lobby, User
from sqlalchemy import select
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class GameWebSocketHandler:
    """Обработчик WebSocket соединений для игр"""
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.user_id = None
    
    async def connect(self, user_id: int):
        """Подключить пользователя"""
        self.user_id = user_id
        await game_manager.connect_user(self.websocket, user_id)
        
        await self.websocket.send_json({
            "type": "connected",
            "message": "Successfully connected to game server",
            "user_id": user_id
        })
    
    async def disconnect(self):
        """Отключить пользователя"""
        if self.user_id:
            game_manager.disconnect_user(self.user_id)
            
            # Очищаем лобби созданные этим пользователем
            lobbies_to_remove = []
            for lid, lobby in game_manager.active_lobbies.items():
                if lobby["creator_id"] == self.user_id:
                    lobbies_to_remove.append(lid)
            
            for lid in lobbies_to_remove:
                del game_manager.active_lobbies[lid]
            
            logger.info(f"Cleaned up {len(lobbies_to_remove)} lobbies for user {self.user_id}")
    
    async def handle_messages(self):
        """Обработка входящих сообщений"""
        while True:
            try:
                data = await self.websocket.receive_json()
                logger.info(f"Received message from user {self.user_id}: {data}")
                
                action = data.get("action")
                
                # Роутинг действий
                if action == "join_queue":
                    await self.handle_join_queue(data)
                elif action == "leave_queue":
                    await self.handle_leave_queue(data)
                elif action == "get_lobby_list":
                    await self.handle_get_lobby_list(data)
                elif action == "create_lobby":
                    await self.handle_create_lobby(data)
                elif action == "join_lobby":
                    await self.handle_join_lobby(data)
                elif action == "leave_lobby":
                    await self.handle_leave_lobby(data)
                elif action == "set_lobby_ready":
                    await self.handle_set_lobby_ready(data)
                elif action == "kick_player":
                    await self.handle_kick_player(data)
                elif action == "make_move":
                    await self.handle_make_move(data)
                elif action == "ping":
                    await self.websocket.send_json({"type": "pong"})
                else:
                    await self.websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from user {self.user_id}")
                await self.websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error processing message from user {self.user_id}: {e}", exc_info=True)
                await self.websocket.send_json({
                    "type": "error",
                    "message": "Internal server error"
                })
    
    async def handle_join_queue(self, data: dict):
        """Присоединиться к очереди"""
        game_type = data.get("game_type", "rps")
        stake = data.get("stake")
        currency = data.get("currency", "TON")
        
        if stake is None:
            await self.websocket.send_json({
                "type": "error",
                "message": "Stake is required to join queue"
            })
            return
        
        await game_manager.add_to_queue(self.user_id, game_type, stake, currency)
        await self.websocket.send_json({
            "type": "queue_joined",
            "message": f"Joined queue for {game_type} with stake {stake} {currency}"
        })
    
    async def handle_leave_queue(self, data: dict):
        """Покинуть очередь"""
        removed = await game_manager.remove_from_queue(self.user_id)
        await self.websocket.send_json({
            "type": "queue_left",
            "message": "Left the queue",
            "success": removed
        })
    
    async def handle_get_lobby_list(self, data: dict):
        """Получить список лобби"""
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
                    "currency": lobby.currency,
                    "has_password": lobby.password_hash is not None,
                    "creator_id": lobby.creator_id,
                    "creator_name": username or "Player",
                    "players_count": 1
                })
            await self.websocket.send_json({
                "type": "lobby_list",
                "lobbies": lobbies
            })
    
    async def handle_create_lobby(self, data: dict):
        """Создать лобби"""
        game_type = data.get("game_type")
        stake = data.get("stake")
        currency = data.get("currency", "TON")
        password = data.get("password")
        
        if not game_type or stake is None:
            await self.websocket.send_json({
                "type": "error",
                "message": "game_type and stake required"
            })
            return
        
        result = await game_manager.create_lobby(self.user_id, game_type, stake, password, currency)
        
        if isinstance(result, tuple):
            lobby_id, message = result
            if lobby_id:
                await self.websocket.send_json({
                    "type": "lobby_created",
                    "lobby_id": lobby_id,
                    "game_type": game_type,
                    "stake": stake,
                    "currency": currency,
                    "has_password": password is not None
                })
            else:
                await self.websocket.send_json({
                    "type": "error",
                    "message": message
                })
        else:
            lobby_id = result
            await self.websocket.send_json({
                "type": "lobby_created",
                "lobby_id": lobby_id,
                "game_type": game_type,
                "stake": stake,
                "currency": currency,
                "has_password": password is not None
            })
    
    async def handle_join_lobby(self, data: dict):
        """Присоединиться к лобби"""
        lobby_id = data.get("lobby_id")
        password = data.get("password")
        
        if not lobby_id:
            await self.websocket.send_json({
                "type": "error",
                "message": "lobby_id required"
            })
            return
        
        success, msg = await game_manager.join_lobby(self.user_id, lobby_id, password)
        
        if success:
            lobby = game_manager.active_lobbies.get(lobby_id)
            if lobby:
                await game_manager._send_to_user(lobby["creator_id"], {
                    "type": "lobby_joined",
                    "lobby_id": lobby_id,
                    "joiner_id": self.user_id,
                    "game_type": lobby["game_type"],
                    "stake": lobby["stake"],
                    "currency": lobby["currency"],
                    "has_password": lobby["has_password"]
                })
                await self.websocket.send_json({
                    "type": "lobby_joined",
                    "lobby_id": lobby_id,
                    "creator_id": lobby["creator_id"]
                })
        else:
            await self.websocket.send_json({
                "type": "error",
                "message": msg
            })
    
    async def handle_leave_lobby(self, data: dict):
        """Покинуть лобби"""
        lobby_id = data.get("lobby_id")
        
        if lobby_id:
            await game_manager.leave_lobby(self.user_id, lobby_id)
            await self.websocket.send_json({
                "type": "lobby_left",
                "lobby_id": lobby_id
            })
    
    async def handle_set_lobby_ready(self, data: dict):
        """Установить статус готовности"""
        lobby_id = data.get("lobby_id")
        is_ready = data.get("is_ready", False)
        
        if lobby_id:
            await game_manager.set_lobby_ready(self.user_id, lobby_id, is_ready)
            
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
    
    async def handle_kick_player(self, data: dict):
        """Кикнуть игрока из лобби"""
        lobby_id = data.get("lobby_id")
        target_id = data.get("target_id")
        
        if lobby_id and target_id:
            success = await game_manager.kick_from_lobby(self.user_id, lobby_id, target_id)
            if success:
                await game_manager._send_to_user(target_id, {
                    "type": "kicked_from_lobby",
                    "lobby_id": lobby_id
                })
                
                if lobby_id in game_manager.active_lobbies:
                    lobby = game_manager.active_lobbies[lobby_id]
                    await game_manager._send_to_user(lobby["creator_id"], {
                        "type": "lobby_updated",
                        "lobby_id": lobby_id,
                        "players": [{"user_id": lobby["creator_id"], "ready": False}]
                    })
    
    async def handle_make_move(self, data: dict):
        """Сделать ход в игре"""
        game_id = data.get("game_id")
        move = data.get("move")
        
        if not game_id or not move:
            await self.websocket.send_json({
                "type": "error",
                "message": "Game ID and move are required"
            })
            return
        
        await game_manager.handle_player_move(game_id, self.user_id, move)