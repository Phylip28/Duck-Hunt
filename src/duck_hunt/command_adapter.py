"""Command adapter for testing the migrated game logic via terminal."""

from __future__ import annotations

from pathlib import Path

from .parity_tools import ParityChecker
from .planner import DeterministicPlanner
from .rng_tools import SeedContext, preview_sequence
from .runtime import GameRuntime, RuntimeEvent


class CommandAdapter:
    """Parses simple commands and routes them to the runtime."""

    def __init__(self, runtime: GameRuntime) -> None:
        self.runtime = runtime
        self.planner = DeterministicPlanner(runtime.session.config)
        repo_root = Path(__file__).resolve().parents[2]
        vectors_file = repo_root / "tests" / "rng" / "parity_vectors.json"
        self.parity_checker = ParityChecker(vectors_file=vectors_file)

    def execute(self, command: str) -> list[RuntimeEvent]:
        tokens = command.strip().split()
        if not tokens:
            raise ValueError("command is empty")

        keyword = tokens[0].lower()

        if keyword == "start":
            if len(tokens) < 4:
                raise ValueError(
                    "start command expects: start <player_name> <seed_a> <seed_b>"
                )

            seed_a_raw = tokens[-2]
            seed_b_raw = tokens[-1]
            player_name = " ".join(tokens[1:-2]).strip()

            if not player_name:
                raise ValueError("player_name is required")

            try:
                seed_a = int(seed_a_raw)
                seed_b = int(seed_b_raw)
            except ValueError as exc:
                raise ValueError("seed_a and seed_b must be integers") from exc

            return self.runtime.start(
                player_name=player_name, seed_a=seed_a, seed_b=seed_b
            )

        if keyword == "hit":
            return self.runtime.perform_action("hit")

        if keyword == "miss":
            return self.runtime.perform_action("miss")

        if keyword == "status":
            return [RuntimeEvent(type="status", payload=self.runtime.status())]

        if keyword == "tick":
            if len(tokens) != 2:
                raise ValueError("tick command expects: tick <delta_ms>")
            try:
                delta_ms = int(tokens[1])
            except ValueError as exc:
                raise ValueError("delta_ms must be an integer") from exc
            return self.runtime.advance_time(delta_ms)

        if keyword == "telemetry":
            if len(tokens) == 1:
                return self.runtime.telemetry_snapshot(limit=None)
            if len(tokens) != 2:
                raise ValueError("telemetry command expects: telemetry [limit]")
            try:
                limit = int(tokens[1])
            except ValueError as exc:
                raise ValueError("telemetry limit must be an integer") from exc
            return self.runtime.telemetry_snapshot(limit=limit)

        if keyword == "rng-seq":
            if len(tokens) not in {4, 9}:
                raise ValueError(
                    "rng-seq expects: rng-seq <seed_a> <seed_b> <length> "
                    "[round map_index session_nonce mode version]"
                )

            seed_a = self._parse_int(tokens[1], "seed_a")
            seed_b = self._parse_int(tokens[2], "seed_b")
            length = self._parse_int(tokens[3], "length")

            context = SeedContext()
            if len(tokens) == 9:
                context = SeedContext(
                    round=self._parse_int(tokens[4], "round"),
                    map_index=self._parse_int(tokens[5], "map_index"),
                    session_nonce=self._parse_int(tokens[6], "session_nonce"),
                    mode=self._parse_int(tokens[7], "mode"),
                    version=self._parse_int(tokens[8], "version"),
                )

            preview = preview_sequence(
                seed_a=seed_a,
                seed_b=seed_b,
                length=length,
                context=context,
                float_count=min(length, 6),
            )
            return [RuntimeEvent(type="rng_preview", payload=preview.to_dict())]

        if keyword == "plan":
            if len(tokens) not in {4, 5}:
                raise ValueError(
                    "plan expects: plan <seed_a> <seed_b> <rounds> [creatures_per_round]"
                )

            seed_a = self._parse_int(tokens[1], "seed_a")
            seed_b = self._parse_int(tokens[2], "seed_b")
            rounds = self._parse_int(tokens[3], "rounds")
            creatures_per_round = None
            if len(tokens) == 5:
                creatures_per_round = self._parse_int(tokens[4], "creatures_per_round")

            plan = self.planner.build_game_plan(
                seed_a=seed_a,
                seed_b=seed_b,
                total_rounds=rounds,
                creatures_per_round=creatures_per_round,
            )
            return [RuntimeEvent(type="plan", payload=plan.to_dict())]

        if keyword == "parity-check":
            report = self.parity_checker.run_all()
            return [RuntimeEvent(type="parity_report", payload=report)]

        raise ValueError(f"unsupported command: {keyword}")

    @staticmethod
    def _parse_int(raw_value: str, field_name: str) -> int:
        try:
            return int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an integer") from exc
