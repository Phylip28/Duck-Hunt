"""Deterministic planning helpers built on top of RNG + Config."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import Config
from .rng import RNG
from .rng_tools import SeedContext


@dataclass(frozen=True)
class RoundPlan:
    round_number: int
    map_index: int
    map_name: str
    creatures: list[str]


@dataclass(frozen=True)
class GamePlan:
    seed_a: int
    seed_b: int
    seed_c: int
    rounds: list[RoundPlan]

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed_a": self.seed_a,
            "seed_b": self.seed_b,
            "seed_c": self.seed_c,
            "rounds": [
                {
                    "round_number": item.round_number,
                    "map_index": item.map_index,
                    "map_name": item.map_name,
                    "creatures": list(item.creatures),
                }
                for item in self.rounds
            ],
        }


class DeterministicPlanner:
    """Generates deterministic round plans for experimentation and balancing."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()

    def build_game_plan(
        self,
        seed_a: int,
        seed_b: int,
        total_rounds: int,
        creatures_per_round: int | None = None,
        context: SeedContext | None = None,
    ) -> GamePlan:
        if not isinstance(total_rounds, int):
            raise TypeError("total_rounds must be an integer")
        if total_rounds <= 0:
            raise ValueError("total_rounds must be > 0")

        per_round = creatures_per_round or self.config.ducks_per_round
        if not isinstance(per_round, int):
            raise TypeError("creatures_per_round must be an integer")
        if per_round <= 0:
            raise ValueError("creatures_per_round must be > 0")

        ctx = context or SeedContext()

        rng = RNG()
        rng.set_seeds(seed_a, seed_b)
        seed_c = rng.derive_seed_c(ctx.to_dict())

        self.config.generate_random_map_queue(rng)

        rounds: list[RoundPlan] = []
        for round_number in range(1, total_rounds + 1):
            game_map = self.config.get_next_random_map(round_number, rng)
            map_index = self.config.maps.index(game_map)
            creatures = [
                self.config.get_random_creature_type(rng, map_file=game_map.file)
                for _ in range(per_round)
            ]
            rounds.append(
                RoundPlan(
                    round_number=round_number,
                    map_index=map_index,
                    map_name=game_map.name,
                    creatures=creatures,
                )
            )

        return GamePlan(
            seed_a=rng.seed_a if rng.seed_a is not None else 0,
            seed_b=rng.seed_b if rng.seed_b is not None else 0,
            seed_c=seed_c,
            rounds=rounds,
        )
