import asyncio
import logging
from typing import Dict, Optional
from backend.database.models import Game, User, Lobby
from backend.games import GAME_ENGINES
from sqlalchemy import select, update
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class PlayerConnection:
    def __init__(self, websocket, user_id: int):
        self.websocket = websocket
        self.user_id = user_id


class PendingMatchRequest:
    def __init__(self, user_id: int, game_type: str, stake: float):
        self.user_id = user_id
        self.game_type = game_type
        self.stake = stake
        self.created_at = datetime.utcnow()


class ActiveGame:
    def __init__(self, game_id: int, player1_id: int, player2_id: int, game_type: str, stake: float):
        self.id = game_id
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.game_type = game_type
        self.stake = stake
        self.created_at = datetime.utcnow()
        
        # Создаём движок для конкретной игры
        engine_class = GAME_ENGINES.get(game_type)
        if not engine_class:
            raise ValueError(f"Unknown game type: {game_type}")
        
        self.engine = engine_class()
        self.state = self.engine.get_initial_state()


class GameManager:
    def __init__(self):
        self.wait_queue: asyncio.Queue[PendingMatchRequest] = asyncio.Queue()
        self.active_games: Dict[int, ActiveGame] = {}
        self.active_connections: Dict[int, PlayerConnection] = {}
        self._lock = asyncio.Lock()
        self.active_lobbies: Dict[int, Dict] = {}

    async def connect_user(self, websocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = PlayerConnection(websocket, user_id)
        logger.info(f"User {user_id} connected to WebSocket.")

    def disconnect_user(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket.")

    async def add_to_queue(self, user_id: int, game_type: str, stake: float):
        request = PendingMatchRequest(user_id, game_type, stake)
        await self.wait_queue.put(request)
        logger.info(f"User {user_id} added to queue for {game_type} with stake {stake}.")
        await self._attempt_matchmaking()

    async def _attempt_matchmaking(self):
        while self.wait_queue.qsize() >= 2:
            try:
                player1_req = await self.wait_queue.get()
                matched = False
                temp_queue = []
                
                while not self.wait_queue.empty():
                    player2_req = await self.wait_queue.get()
                    
                    if (player1_req.game_type == player2_req.game_type and 
                        player1_req.stake == player2_req.stake):
                        logger.info(f"Match found between {player1_req.user_id} and {player2_req.user_id} for {player1_req.game_type}")
                        await self._create_game(player1_req.user_id, player2_req.user_id, player1_req.game_type, player1_req.stake)
                        matched = True
                        break
                    else:
                        temp_queue.append(player2_req)
                
                for req in temp_queue:
                    await self.wait_queue.put(req)
                
                if not matched:
                    await self.wait_queue.put(player1_req)
                    break
            except Exception as e:
                logger.error(f"Error in matchmaking: {e}", exc_info=True)
                break

    async def _create_game(self, player1_id: int, player2_id: int, game_type: str, stake: float):
        from backend.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                # Создаём временный движок для получения начального состояния
                engine_class = GAME_ENGINES.get(game_type)
                if not engine_class:
                    raise ValueError(f"Unknown game type: {game_type}")
                temp_engine = engine_class()
                
                new_game = Game(
                    game_type=game_type,
                    mode="1v1",
                    player1_id=player1_id,
                    player2_id=player2_id,
                    stake_amount_ton=Decimal(stake),
                    currency="TON",
                    game_state_json=temp_engine.get_initial_state(),
                    created_at=datetime.utcnow()
                )
                db.add(new_game)
                await db.commit()
                await db.refresh(new_game)

                active_game = ActiveGame(new_game.id, player1_id, player2_id, game_type, stake)
                self.active_games[new_game.id] = active_game

                logger.info(f"Game {new_game.id} created with {game_type} engine")

                await self._send_to_user(player1_id, {
                    "type": "game_found",
                    "game_id": new_game.id,
                    "opponent_id": player2_id,
                    "stake": stake,
                    "game_type": game_type
                })
                await self._send_to_user(player2_id, {
                    "type": "game_found",
                    "game_id": new_game.id,
                    "opponent_id": player1_id,
                    "stake": stake,
                    "game_type": game_type
                })

            except Exception as e:
                logger.error(f"Error creating game: {e}", exc_info=True)
                await self.wait_queue.put(PendingMatchRequest(player1_id, game_type, stake))
                await self.wait_queue.put(PendingMatchRequest(player2_id, game_type, stake))

    async def handle_player_move(self, game_id: int, user_id: int, move: str):
        if game_id not in self.active_games:
            logger.warning(f"Game {game_id} not found")
            return

        game = self.active_games[game_id]
        
        # Определяем ключ игрока
        if user_id == game.player1_id:
            player_key = "player1"
        elif user_id == game.player2_id:
            player_key = "player2"
        else:
            logger.warning(f"User {user_id} not in game {game_id}")
            return

        # Валидируем ход через движок
        if not game.engine.validate_move(move, player_key, game.state):
            logger.warning(f"Invalid move {move} from {user_id} in game {game_id}")
            await self._send_to_user(user_id, {
                "type": "error",
                "message": "Invalid move"
            })
            return

        # Применяем ход
        game.state = game.engine.apply_move(move, player_key, game.state)
        logger.info(f"Move applied: {move} by {player_key} in game {game_id}")

        # Проверяем окончание раунда
        round_winner = game.engine.check_round_end(game.state)
        
        if round_winner is not None:
            # Раунд закончен
            if round_winner != "draw":
                # Обновляем счёт
                if "score" in game.state:
                    game.state["score"][round_winner] = game.state["score"].get(round_winner, 0) + 1
            
            logger.info(f"Round ended in game {game_id}. Winner: {round_winner}, Score: {game.state.get('score')}")
            
            # Отправляем результат раунда
            await self._send_to_user(game.player1_id, {
                "type": "round_result",
                "game_id": game_id,
                "round_winner": round_winner,
                "moves": game.state.get("moves", {}),
                "score": game.state.get("score", {})
            })
            await self._send_to_user(game.player2_id, {
                "type": "round_result",
                "game_id": game_id,
                "round_winner": round_winner,
                "moves": game.state.get("moves", {}),
                "score": game.state.get("score", {})
            })
            
            # Проверяем окончание всей игры
            if game.engine.is_game_over(game.state):
                final_winner = game.engine.get_winner(game.state)
                winner_id = None
                if final_winner == "player1":
                    winner_id = game.player1_id
                elif final_winner == "player2":
                    winner_id = game.player2_id
                
                await self._end_game(game_id, winner_id)
            else:
                # Игра продолжается, сбрасываем для нового раунда
                game.state = game.engine.reset_round(game.state)

    async def _end_game(self, game_id: int, winner_id: Optional[int]):
        if game_id not in self.active_games:
            return

        game = self.active_games[game_id]
        from backend.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                stmt = update(Game).where(Game.id == game_id).values(
                    winner_id=winner_id,
                    result="draw" if winner_id is None else ("player1_win" if winner_id == game.player1_id else "player2_win"),
                    finished_at=datetime.utcnow(),
                    final_state_json=game.state
                )
                await db.execute(stmt)

                rake_percentage = 0.05
                total_pot = game.stake * 2
                rake_amount = total_pot * rake_percentage
                winner_payout = total_pot - rake_amount if winner_id else total_pot / 2

                if winner_id:
                    loser_id = game.player2_id if winner_id == game.player1_id else game.player1_id
                    await db.execute(update(User).where(User.id == winner_id).values(
                        total_wins=User.total_wins + 1,
                        total_games_played=User.total_games_played + 1,
                        total_won_ton=User.total_won_ton + Decimal(winner_payout)
                    ))
                    await db.execute(update(User).where(User.id == loser_id).values(
                        total_losses=User.total_losses + 1,
                        total_games_played=User.total_games_played + 1
                    ))
                else:
                    await db.execute(update(User).where(User.id == game.player1_id).values(
                        total_games_played=User.total_games_played + 1
                    ))
                    await db.execute(update(User).where(User.id == game.player2_id).values(
                        total_games_played=User.total_games_played + 1
                    ))

                await db.commit()

                result_message = {
                    "type": "game_result",
                    "game_id": game_id,
                    "winner_id": winner_id,
                    "final_state": game.state
                }
                await self._send_to_user(game.player1_id, result_message)
                await self._send_to_user(game.player2_id, result_message)

                del self.active_games[game_id]
                logger.info(f"Game {game_id} ended. Winner: {winner_id}")

            except Exception as e:
                logger.error(f"Error ending game {game_id}: {e}", exc_info=True)

    async def _send_to_user(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                self.disconnect_user(user_id)
        else:
            logger.warning(f"User {user_id} not connected")
    
    async def create_lobby(self, user_id: int, game_type: str, stake: float, password: Optional[str] = None):
        from backend.database import AsyncSessionLocal
        from datetime import datetime, timedelta
        import bcrypt

        async with AsyncSessionLocal() as db:
            # Создаём запись в БД
            password_hash = None
            if password:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            expires_at = datetime.utcnow() + timedelta(minutes=10)

            lobby = Lobby(
                game_type=game_type,
                stake=Decimal(stake),
                password_hash=password_hash,
                creator_id=user_id,
                status="waiting",
                expires_at=expires_at
            )
            db.add(lobby)
            await db.commit()
            await db.refresh(lobby)

            # Храним в памяти для быстрого доступа
            self.active_lobbies[lobby.id] = {
                "id": lobby.id,
                "game_type": game_type,
                "stake": stake,
                "has_password": password is not None,
                "creator_id": user_id,
                "joiner_id": None,
                "creator_ready": False,
                "joiner_ready": False,
                "status": "waiting"
                "expires_at": expires_at
            }

            return lobby.id

    async def join_lobby(self, user_id: int, lobby_id: int, password: Optional[str] = None):
        import bcrypt
        if lobby_id not in self.active_lobbies:
            return False, "Lobby not found"

        lobby = self.active_lobbies[lobby_id]
        if lobby["joiner_id"] is not None:
            return False, "Lobby is full"

        from backend.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            db_lobby = await db.get(Lobby, lobby_id)
            if not db_lobby:
                return False, "Lobby not found in DB"

            # Проверка пароля
            if db_lobby.password_hash:
                if not password:
                    return False, "Password required"
                if not bcrypt.checkpw(password.encode('utf-8'), db_lobby.password_hash.encode('utf-8')):
                    return False, "Invalid password"

            # Обновляем в БД и в памяти
            db_lobby.joiner_id = user_id
            db_lobby.status = "full"
            await db.commit()

            lobby["joiner_id"] = user_id
            lobby["status"] = "full"

        return True, "Joined"

    async def leave_lobby(self, user_id: int, lobby_id: int):
        if lobby_id not in self.active_lobbies:
            return False

        lobby = self.active_lobbies[lobby_id]

        if lobby["creator_id"] == user_id:
            # Создатель выходит — удаляем лобби полностью
            del self.active_lobbies[lobby_id]
            from backend.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                db_lobby = await db.get(Lobby, lobby_id)
                if db_lobby:
                    await db.delete(db_lobby)
                    await db.commit()
            logger.info(f"Lobby {lobby_id} deleted by creator {user_id}")
            return True

        elif lobby["joiner_id"] == user_id:
            # Участник выходит — освобождаем слот
            lobby["joiner_id"] = None
            lobby["joiner_ready"] = False
            lobby["status"] = "waiting"

            from backend.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                db_lobby = await db.get(Lobby, lobby_id)
                if db_lobby:
                    db_lobby.joiner_id = None
                    db_lobby.status = "waiting"
                    await db.commit()

            # Уведомляем создателя
            await self._send_to_user(lobby["creator_id"], {
                "type": "lobby_joined_left",
                "lobby_id": lobby_id,
                "joiner_id": None
            })
            return True

        return False

    async def set_lobby_ready(self, user_id: int, lobby_id: int, is_ready: bool):
        if lobby_id not in self.active_lobbies:
            return
        lobby = self.active_lobbies[lobby_id]
        if user_id == lobby["creator_id"]:
            lobby["creator_ready"] = is_ready
        elif user_id == lobby["joiner_id"]:
            lobby["joiner_ready"] = is_ready
        else:
            return

        # Проверяем, оба ли ready
        if lobby["joiner_id"] and lobby["creator_ready"] and lobby["joiner_ready"]:
            await self._start_game_from_lobby(lobby_id)

    async def kick_from_lobby(self, kicker_id: int, lobby_id: int, target_id: int):
        if lobby_id not in self.active_lobbies:
            return False
        lobby = self.active_lobbies[lobby_id]
        if lobby["creator_id"] != kicker_id:
            return False  # Только создатель может кикать
        if target_id != lobby["joiner_id"]:
            return False

        lobby["joiner_id"] = None
        lobby["joiner_ready"] = False
        lobby["status"] = "waiting"

        from backend.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            db_lobby = await db.get(Lobby, lobby_id)
            if db_lobby:
                db_lobby.joiner_id = None
                db_lobby.status = "waiting"
                await db.commit()

        return True

    async def _start_game_from_lobby(self, lobby_id: int):
        lobby = self.active_lobbies[lobby_id]
        await self._create_game(
            player1_id=lobby["creator_id"],
            player2_id=lobby["joiner_id"],
            game_type=lobby["game_type"],
            stake=lobby["stake"]
        )
        # Удаляем лобби
        del self.active_lobbies[lobby_id]
        from backend.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            db_lobby = await db.get(Lobby, lobby_id)
            if db_lobby:
                await db.delete(db_lobby)
                await db.commit()


game_manager = GameManager()