"""Core non-UI game state for Duck Hunt Python migration."""

from __future__ import annotations

from dataclasses import dataclass

from .config import Config
from .rng import RNG


@dataclass(frozen=True)
class ShotResult:
    result: str
    points: int = 0
    round_bonus: int = 0


class GameState:
    """Pure gameplay state machine without rendering or audio concerns."""

    def __init__(self, config: Config, rng: RNG) -> None:
        self.config = config
        self.rng = rng

        self.current_round = 1
        self.total_score = 0
        self.shots_remaining = self.config.shots_per_duck
        self.duck_speed = self.config.initial_duck_speed

        self.current_duck_index = 0
        self.ducks_caught = 0
        self.creature_active = False
        self.game_active = False

        self.current_map_index = 0
        self.current_map_name = "---"
        self.fixed_map_index: int | None = None

    def start_new_game(
        self, seed_a: int, seed_b: int, context: dict | None = None
    ) -> None:
        self.rng.set_seeds(seed_a, seed_b)
        self.rng.derive_seed_c(context)

        preferred_map_index: int | None = None
        if isinstance(context, dict):
            raw_map_index = context.get("map_index")
            if isinstance(raw_map_index, int) and not isinstance(raw_map_index, bool):
                if 0 <= raw_map_index < len(self.config.maps):
                    preferred_map_index = raw_map_index

        if preferred_map_index is None and self.config.maps:
            preferred_map_index = self.rng.randint(0, len(self.config.maps) - 1)

        self.current_round = 1
        self.total_score = 0
        self.duck_speed = self.config.initial_duck_speed
        self.game_active = True

        self.fixed_map_index = preferred_map_index
        self._change_map_for_round()
        self._reset_round_counters()

    def _reset_round_counters(self) -> None:
        self.current_duck_index = 0
        self.ducks_caught = 0
        self.shots_remaining = self.config.shots_per_duck
        self.creature_active = False

    def _change_map_for_round(self) -> None:
        if not self.config.maps:
            self.current_map_index = 0
            self.current_map_name = "---"
            return

        if self.fixed_map_index is not None:
            game_map = self.config.maps[self.fixed_map_index]
            self.current_map_index = self.fixed_map_index
        else:
            game_map = self.config.get_next_random_map(self.current_round, self.rng)
            self.current_map_index = self.config.maps.index(game_map)

        self.current_map_name = game_map.name

    def spawn_next_creature(self) -> str:
        if not self.game_active:
            raise RuntimeError("Game is not active")
        if self.creature_active:
            raise RuntimeError("Current creature must be resolved first")

        if self.current_duck_index >= self.config.ducks_per_round:
            raise RuntimeError("Round already completed")

        creature_type = self.config.get_random_creature_type(self.rng)
        self.shots_remaining = self.config.shots_per_duck
        self.creature_active = True
        return creature_type

    def record_hit(self) -> ShotResult:
        if not self.game_active or not self.creature_active:
            raise RuntimeError("No active creature")
        if self.shots_remaining <= 0:
            raise RuntimeError("No shots remaining")

        self.shots_remaining -= 1

        if self.shots_remaining == 2:
            points = self.config.points_first_shot
        elif self.shots_remaining == 1:
            points = self.config.points_second_shot
        else:
            points = self.config.points_third_shot

        self.total_score += points
        self.ducks_caught += 1
        self.current_duck_index += 1
        self.creature_active = False

        if self.current_duck_index >= self.config.ducks_per_round:
            round_bonus = self._complete_round()
            return ShotResult(
                result="round_completed", points=points, round_bonus=round_bonus
            )

        return ShotResult(result="creature_cleared", points=points)

    def record_miss(self) -> ShotResult:
        if not self.game_active or not self.creature_active:
            raise RuntimeError("No active creature")
        if self.shots_remaining <= 0:
            raise RuntimeError("No shots remaining")

        self.shots_remaining -= 1

        if self.shots_remaining <= 0:
            self.game_active = False
            self.creature_active = False
            return ShotResult(result="game_over")

        return ShotResult(result="creature_alive")

    def _complete_round(self) -> int:
        round_bonus = self.current_round * self.config.round_bonus_multiplier
        self.total_score += round_bonus

        self.current_round += 1
        self.duck_speed += self.config.speed_increase_per_round

        self._change_map_for_round()
        self._reset_round_counters()

        return round_bonus
