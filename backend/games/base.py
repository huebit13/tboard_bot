from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseGameEngine(ABC):
    """Базовый класс для всех игровых движков"""
    
    @abstractmethod
    def get_initial_state(self) -> Dict[str, Any]:
        """
        Возвращает начальное состояние игры.
        Должно включать все необходимые поля для игры.
        """
        pass
    
    @abstractmethod
    def validate_move(self, move: Any, player_key: str, game_state: Dict[str, Any]) -> bool:
        """
        Проверяет, валиден ли ход.
        
        Args:
            move: Ход игрока (формат зависит от игры)
            player_key: "player1" или "player2"
            game_state: Текущее состояние игры
            
        Returns:
            True если ход валиден, False иначе
        """
        pass
    
    @abstractmethod
    def apply_move(self, move: Any, player_key: str, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применяет ход к состоянию игры.
        
        Args:
            move: Ход игрока
            player_key: "player1" или "player2"
            game_state: Текущее состояние игры
            
        Returns:
            Обновлённое состояние игры
        """
        pass
    
    @abstractmethod
    def check_round_end(self, game_state: Dict[str, Any]) -> Optional[str]:
        """
        Проверяет, закончился ли текущий раунд.
        
        Args:
            game_state: Текущее состояние игры
            
        Returns:
            "player1", "player2", "draw" или None если раунд не закончен
        """
        pass
    
    @abstractmethod
    def is_game_over(self, game_state: Dict[str, Any]) -> bool:
        """
        Проверяет, закончилась ли вся игра.
        
        Args:
            game_state: Текущее состояние игры
            
        Returns:
            True если игра закончена, False иначе
        """
        pass
    
    @abstractmethod
    def get_winner(self, game_state: Dict[str, Any]) -> Optional[str]:
        """
        Определяет победителя игры.
        
        Args:
            game_state: Текущее состояние игры
            
        Returns:
            "player1", "player2", "draw" или None если нет победителя
        """
        pass
    
    def reset_round(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сбрасывает состояние для нового раунда (опционально).
        По умолчанию просто очищает ходы.
        
        Args:
            game_state: Текущее состояние игры
            
        Returns:
            Обновлённое состояние для нового раунда
        """
        if "moves" in game_state:
            game_state["moves"] = {}
        return game_state