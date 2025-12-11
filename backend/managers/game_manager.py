import asyncio
import logging
import random
from typing import Dict, Optional, Set
from backend.database.models import Game, User
from sqlalchemy.ext.asyncio import AsyncSession
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
        self.state = {"status": "playing", "moves": {}}
        self.created_at = datetime.utcnow()

class GameManager:
    def __init__(self):
        self.wait_queue: asyncio.Queue[PendingMatchRequest] = asyncio.Queue()
        self.active_games: Dict[int, ActiveGame] = {}
        self.active_connections: Dict[int, PlayerConnection] = {}
        self._lock = asyncio.Lock()

    async def connect_user(self, websocket, user_id: int):
        """Добавляет соединение пользователя."""
        await websocket.accept()
        self.active_connections[user_id] = PlayerConnection(websocket, user_id)
        logger.info(f"User {user_id} connected to WebSocket.")

    def disconnect_user(self, user_id: int):
        """Удаляет соединение пользователя."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket.")

    async def add_to_queue(self, user_id: int, game_type: str, stake: float):
        """Добавляет пользователя в очередь ожидания."""
        request = PendingMatchRequest(user_id, game_type, stake)
        await self.wait_queue.put(request)
        logger.info(f"User {user_id} added to queue for {game_type} with stake {stake}.")
        
        await self._attempt_matchmaking()

    async def _attempt_matchmaking(self):
        """Пытается найти пару для игроков в очереди."""
        while self.wait_queue.qsize() >= 2:
            try:
                player1_req = await self.wait_queue.get()
                
                matched = False
                temp_queue = []
                
                while not self.wait_queue.empty():
                    player2_req = await self.wait_queue.get()
                    
                    if (player1_req.game_type == player2_req.game_type and 
                        player1_req.stake == player2_req.stake):
                        logger.info(f"Match found between {player1_req.user_id} and {player2_req.user_id} for {player1_req.game_type} with stake {player1_req.stake}.")
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
                logger.error(f"Error in matchmaking: {e}")
                break

    async def _create_game(self, player1_id: int, player2_id: int, game_type: str, stake: float):
        """Создаёт новую игру в БД и добавляет в список активных."""
        from backend.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                new_game = Game(
                    game_type=game_type,
                    mode="1v1",
                    player1_id=player1_id,
                    player2_id=player2_id,
                    stake_amount_ton=Decimal(stake),
                    currency="TON",
                    game_state_json={"status": "playing", "moves": {}, "player1_move": None, "player2_move": None},
                    created_at=datetime.utcnow()
                )
                db.add(new_game)
                await db.commit()
                await db.refresh(new_game)

                active_game = ActiveGame(new_game.id, player1_id, player2_id, game_type, stake)
                self.active_games[new_game.id] = active_game

                logger.info(f"Game {new_game.id} created in DB and added to active games.")

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
                logger.error(f"Error creating game in DB: {e}", exc_info=True)
                await self.wait_queue.put(PendingMatchRequest(player1_id, game_type, stake))
                await self.wait_queue.put(PendingMatchRequest(player2_id, game_type, stake))

    async def handle_player_move(self, game_id: int, user_id: int, move: str):
        """Обрабатывает ход игрока."""
        if game_id not in self.active_games:
            logger.warning(f"Game {game_id} not found for move by user {user_id}.")
            return

        game = self.active_games[game_id]
        
        if user_id != game.player1_id and user_id != game.player2_id:
            logger.warning(f"User {user_id} tried to make a move in game {game_id} they are not part of.")
            return

        if game.state["status"] != "playing":
            logger.info(f"Game {game_id} is not in playing state, ignoring move from {user_id}.")
            return

        if user_id == game.player1_id:
            game.state["moves"]["player1"] = move
        elif user_id == game.player2_id:
            game.state["moves"]["player2"] = move

        logger.info(f"Move {move} received from user {user_id} in game {game_id}. Current state: {game.state}")

        if "player1" in game.state["moves"] and "player2" in game.state["moves"]:
            winner_id = self._determine_winner(game_id, game.state["moves"]["player1"], game.state["moves"]["player2"])
            await self._end_game(game_id, winner_id)

    def _determine_winner(self, game_id: int, move1: str, move2: str) -> Optional[int]:
        """Определяет победителя RPS."""
        game = self.active_games[game_id]
        
        if move1 == move2:
            return None
        elif (move1 == "rock" and move2 == "scissors") or \
             (move1 == "paper" and move2 == "rock") or \
             (move1 == "scissors" and move2 == "paper"):
            return game.player1_id
        else:
            return game.player2_id

    async def _end_game(self, game_id: int, winner_id: Optional[int]):
        """Завершает игру, обновляет БД, отправляет результаты."""
        if game_id not in self.active_games:
            logger.warning(f"Attempted to end non-existent game {game_id}.")
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

                logger.info(f"Game {game_id} ended. Winner: {winner_id}, Pot: {total_pot}, Rake: {rake_amount}, Winner Payout: {winner_payout}")

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
                    await db.execute(update(User).where(User.id == winner_id).values(
                        total_rake_paid_ton=User.total_rake_paid_ton + Decimal(rake_amount)
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
                logger.info(f"Game {game_id} ended and removed from active games.")

            except Exception as e:
                logger.error(f"Error ending game {game_id} in DB: {e}", exc_info=True)

    async def _send_to_user(self, user_id: int, message: dict):
        """Отправляет сообщение конкретному пользователю через его WebSocket."""
        if user_id in self.active_connections:
            connection = self.active_connections[user_id]
            try:
                await connection.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect_user(user_id)
        else:
            logger.warning(f"Attempted to send message to disconnected user {user_id}.")

game_manager = GameManager()