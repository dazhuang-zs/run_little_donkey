"""
数据模型
"""

from .player import Player, PlayerCreate, PlayerUpdate, PlayerInDB
from .game import GameState, GameStateCreate, GameStateUpdate, GameStateInDB
from .event import Event, EventCreate, EventInDB, EventChoice, EventChoiceCreate
from .action import Action, ActionCreate, ActionInDB
from .ending import Ending, EndingCreate, EndingInDB
from .db_models import (
    PlayerDB,
    GameStateDB,
    EventDB,
    EventChoiceDB,
    ActionDB,
    PlayerActionDB,
    EndingDB,
    PlayerEndingDB,
    LeaderboardDB,
)

__all__ = [
    "Player",
    "PlayerCreate",
    "PlayerUpdate",
    "PlayerInDB",
    "GameState",
    "GameStateCreate",
    "GameStateUpdate",
    "GameStateInDB",
    "Event",
    "EventCreate",
    "EventInDB",
    "EventChoice",
    "EventChoiceCreate",
    "Action",
    "ActionCreate",
    "ActionInDB",
    "Ending",
    "EndingCreate",
    "EndingInDB",
    "PlayerDB",
    "GameStateDB",
    "EventDB",
    "EventChoiceDB",
    "ActionDB",
    "PlayerActionDB",
    "EndingDB",
    "PlayerEndingDB",
    "LeaderboardDB",
]