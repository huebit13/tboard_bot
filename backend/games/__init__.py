from .base import BaseGameEngine
from .rps import RPSGameEngine
from .chess import ChessGameEngine
from .checkers import CheckersGameEngine

# Регистр всех доступных игровых движков
GAME_ENGINES = {
    'rps': RPSGameEngine,
    'chess': ChessGameEngine,
    'checkers': CheckersGameEngine
}

__all__ = [
    'BaseGameEngine',
    'RPSGameEngine',
    'ChessGameEngine',
    'CheckersGameEngine',
    'GAME_ENGINES'
]