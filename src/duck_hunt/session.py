"""Session orchestration layer connecting menu flow and game state."""

from __future__ import annotations

from .config import Config
from .game_state import GameState, ShotResult
from .menu_flow import MenuFlow
from .rng import RNG
from .storage import Storage


class Session:
    """High-level coordinator for gameplay and menu transitions."""

    def __init__(self, config: Config, rng: RNG, storage: Storage) -> None:
        self.config = config
        self.rng = rng
        self.storage = storage

        self.menu = MenuFlow(config=config, storage=storage)
        self.game = GameState(config=config, rng=rng)

    def start_new_game(
        self,
        player_name: str,
        seed_a: int,
        seed_b: int,
        context: dict | None = None,
    ) -> None:
        self.menu.confirm_player_name(player_name)
        self.game.start_new_game(seed_a=seed_a, seed_b=seed_b, context=context)

    def spawn_next_creature(self) -> str:
        return self.game.spawn_next_creature()

    def hit_current_creature(self) -> ShotResult:
        return self.game.record_hit()

    def miss_current_creature(self) -> ShotResult:
        result = self.game.record_miss()
        if result.result == "game_over":
            self.finalize_game_over()
        return result

    def finalize_game_over(self) -> None:
        self.menu.show_game_over(
            final_score=self.game.total_score,
            final_round=self.game.current_round,
            map_index=self.game.current_map_index,
        )

    def stop_game_and_return_to_menu(self) -> None:
        self.game.game_active = False
        self.game.creature_active = False
        self.menu.back_to_menu_from_game_over()
