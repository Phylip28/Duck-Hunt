"""Command adapter for testing the migrated game logic via terminal."""

from __future__ import annotations

from .runtime import GameRuntime, RuntimeEvent


class CommandAdapter:
    """Parses simple commands and routes them to the runtime."""

    def __init__(self, runtime: GameRuntime) -> None:
        self.runtime = runtime

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

        raise ValueError(f"unsupported command: {keyword}")
