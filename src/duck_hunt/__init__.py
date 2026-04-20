"""Duck Hunt Python migration package (phase 1)."""

from .command_adapter import CommandAdapter
from .config import Config
from .game_state import GameState, ShotResult
from .menu_flow import MenuFlow, RankingRow
from .parity_tools import ParityCaseResult, ParityChecker
from .planner import DeterministicPlanner, GamePlan, RoundPlan
from .rng import RNG
from .rng_tools import RNGPreview, SeedContext, preview_sequence
from .runtime import GameRuntime, RuntimeEvent
from .session import Session
from .storage import RankingEntry, Storage
from .telemetry import TelemetryEvent, TelemetryLog
from .timing import ScheduledAction, TimingConfig, TimingEngine

try:
    from .ui_tk import DuckHuntTkApp
except Exception:  # pragma: no cover - optional UI dependency
    DuckHuntTkApp = None

__all__ = [
    "Config",
    "RNG",
    "Storage",
    "RankingEntry",
    "GameState",
    "ShotResult",
    "MenuFlow",
    "RankingRow",
    "Session",
    "GameRuntime",
    "RuntimeEvent",
    "CommandAdapter",
    "TimingEngine",
    "TimingConfig",
    "ScheduledAction",
    "TelemetryLog",
    "TelemetryEvent",
    "SeedContext",
    "RNGPreview",
    "preview_sequence",
    "DeterministicPlanner",
    "RoundPlan",
    "GamePlan",
    "ParityChecker",
    "ParityCaseResult",
]

if DuckHuntTkApp is not None:
    __all__.append("DuckHuntTkApp")
