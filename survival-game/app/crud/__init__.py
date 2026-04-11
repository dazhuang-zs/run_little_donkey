"""
CRUD操作
"""

from .player import crud_player
from .game import crud_game
from .event import crud_event
from .action import crud_action
from .ending import crud_ending

__all__ = [
    "crud_player",
    "crud_game",
    "crud_event",
    "crud_action",
    "crud_ending",
]