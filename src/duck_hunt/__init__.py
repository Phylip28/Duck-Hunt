"""Duck Hunt Python migration package (phase 1)."""

from .config import Config
from .game_state import GameState, ShotResult
from .rng import RNG
from .storage import RankingEntry, Storage

__all__ = [
    "Config",
    "RNG",
    "Storage",
    "RankingEntry",
    "GameState",
    "ShotResult",
]
