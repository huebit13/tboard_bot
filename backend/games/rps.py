from typing import Optional, Dict, Any
from .base import BaseGameEngine


class RPSGameEngine(BaseGameEngine):
    """Движок для игры Rock Paper Scissors"""
    
    VALID_MOVES = {"rock", "paper", "scissors"}
    WINS_NEEDED = 3  # Первый до 3 побед
    
    def get_initial_state(self) -> Dict[str, Any]:
        return {
            "status": "playing",
            "moves": {},
            "score": {"player1": 0, "player2": 0},
            "rounds_played": 0
        }
    
    def validate_move(self, move: Any, player_key: str, game_state: Dict[str, Any]) -> bool:
        # Проверяем, что ход - строка и входит в допустимые
        if not isinstance(move, str):
            return False
        if move not in self.VALID_MOVES:
            return False
        # Проверяем, что игрок ещё не сделал ход в этом раунде
        if player_key in game_state.get("moves", {}):
            return False
        return True
    
    def apply_move(self, move: Any, player_key: str, game_state: Dict[str, Any]) -> Dict[str, Any]:
        game_state["moves"][player_key] = move
        return game_state
    
    def check_round_end(self, game_state: Dict[str, Any]) -> Optional[str]:
        """Проверяет, закончился ли раунд (оба игрока сделали ход)"""
        moves = game_state.get("moves", {})
        
        if "player1" not in moves or "player2" not in moves:
            return None  # Раунд не закончен
        
        move1 = moves["player1"]
        move2 = moves["player2"]
        
        # Определяем победителя раунда
        if move1 == move2:
            return "draw"
        elif (move1 == "rock" and move2 == "scissors") or \
             (move1 == "paper" and move2 == "rock") or \
             (move1 == "scissors" and move2 == "paper"):
            return "player1"
        else:
            return "player2"
    
    def is_game_over(self, game_state: Dict[str, Any]) -> bool:
        score = game_state.get("score", {"player1": 0, "player2": 0})
        return score["player1"] >= self.WINS_NEEDED or score["player2"] >= self.WINS_NEEDED
    
    def get_winner(self, game_state: Dict[str, Any]) -> Optional[str]:
        if not self.is_game_over(game_state):
            return None
        
        score = game_state.get("score", {"player1": 0, "player2": 0})
        if score["player1"] >= self.WINS_NEEDED:
            return "player1"
        elif score["player2"] >= self.WINS_NEEDED:
            return "player2"
        return None
    
    def reset_round(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Сбрасывает состояние для нового раунда"""
        game_state["moves"] = {}
        game_state["rounds_played"] = game_state.get("rounds_played", 0) + 1
        return game_state