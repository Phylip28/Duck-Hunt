"""Runtime orchestration for the Python migration without rendering."""

from __future__ import annotations

from dataclasses import dataclass, field

from .session import Session
from .telemetry import TelemetryLog
from .timing import TimingEngine


@dataclass(frozen=True)
class RuntimeEvent:
    type: str
    payload: dict[str, object] = field(default_factory=dict)


class GameRuntime:
    """Coordinates session actions and emits structured runtime events."""

    def __init__(
        self,
        session: Session,
        timing_engine: TimingEngine | None = None,
        telemetry: TelemetryLog | None = None,
    ) -> None:
        self.session = session
        self.timing = timing_engine or TimingEngine()
        self.telemetry = telemetry or TelemetryLog()

    def _emit(self, event_type: str, payload: dict[str, object]) -> RuntimeEvent:
        event = RuntimeEvent(type=event_type, payload=payload)
        self.telemetry.record(
            timestamp_ms=self.timing.current_time_ms,
            event_type=event_type,
            payload=payload,
        )
        return event

    def start(
        self,
        player_name: str,
        seed_a: int,
        seed_b: int,
        context: dict | None = None,
    ) -> list[RuntimeEvent]:
        self.session.start_new_game(
            player_name=player_name,
            seed_a=seed_a,
            seed_b=seed_b,
            context=context,
        )

        creature_type = self.session.spawn_next_creature()

        self.timing.clear()
        self.timing.schedule_in(
            self.timing.config.spawn_delay_ms,
            "spawn_delay_window",
            {"round": self.session.game.current_round},
        )

        return [
            self._emit(
                event_type="session_started",
                payload={
                    "player_name": self.session.menu.player_name,
                    "round": self.session.game.current_round,
                    "map_name": self.session.game.current_map_name,
                },
            ),
            self._emit(
                event_type="creature_spawned",
                payload={
                    "creature_type": creature_type,
                    "round": self.session.game.current_round,
                    "shots_remaining": self.session.game.shots_remaining,
                },
            ),
        ]

    def perform_action(self, action: str) -> list[RuntimeEvent]:
        normalized_action = action.strip().lower()
        if normalized_action not in {"hit", "miss"}:
            raise ValueError("action must be 'hit' or 'miss'")

        if not self.session.game.game_active:
            raise RuntimeError("Game is not active")

        events: list[RuntimeEvent] = []

        if normalized_action == "hit":
            result = self.session.hit_current_creature()
            events.append(
                self._emit(
                    event_type="action_resolved",
                    payload={
                        "action": "hit",
                        "result": result.result,
                        "points": result.points,
                        "round_bonus": result.round_bonus,
                        "score": self.session.game.total_score,
                    },
                )
            )

            if result.result == "round_completed":
                self.timing.schedule_in(
                    self.timing.config.round_delay_ms,
                    "round_delay_window",
                    {"next_round": self.session.game.current_round},
                )
                events.append(
                    self._emit(
                        event_type="round_completed",
                        payload={
                            "round_bonus": result.round_bonus,
                            "next_round": self.session.game.current_round,
                            "score": self.session.game.total_score,
                            "map_name": self.session.game.current_map_name,
                        },
                    )
                )

            creature_type = self.session.spawn_next_creature()
            events.append(
                self._emit(
                    event_type="creature_spawned",
                    payload={
                        "creature_type": creature_type,
                        "round": self.session.game.current_round,
                        "shots_remaining": self.session.game.shots_remaining,
                    },
                )
            )
            return events

        miss_result = self.session.miss_current_creature()
        events.append(
            self._emit(
                event_type="action_resolved",
                payload={
                    "action": "miss",
                    "result": miss_result.result,
                    "shots_remaining": self.session.game.shots_remaining,
                    "score": self.session.game.total_score,
                },
            )
        )

        if miss_result.result == "game_over":
            self.timing.schedule_in(
                self.timing.config.game_over_delay_ms,
                "game_over_screen_delay",
                {"round": self.session.menu.final_round},
            )
            events.append(
                self._emit(
                    event_type="game_over",
                    payload={
                        "final_score": self.session.menu.final_score,
                        "final_round": self.session.menu.final_round,
                        "map_index": self.session.game.current_map_index,
                    },
                )
            )

        return events

    def advance_time(self, delta_ms: int) -> list[RuntimeEvent]:
        due_actions = self.timing.advance(delta_ms)

        events = [
            self._emit(
                event_type="time_advanced",
                payload={
                    "delta_ms": delta_ms,
                    "time_ms": self.timing.current_time_ms,
                    "due_actions": len(due_actions),
                },
            )
        ]

        for action in due_actions:
            events.append(
                self._emit(
                    event_type="timer_elapsed",
                    payload={
                        "id": action.id,
                        "action_type": action.action_type,
                        "due_time_ms": action.due_time_ms,
                        "payload": action.payload,
                    },
                )
            )

        return events

    def telemetry_snapshot(self, limit: int | None = None) -> list[RuntimeEvent]:
        snapshot = self.telemetry.snapshot(limit=limit)
        payload = {
            "count": len(snapshot),
            "events": [
                {
                    "seq": item.seq,
                    "timestamp_ms": item.timestamp_ms,
                    "event_type": item.event_type,
                    "payload": item.payload,
                }
                for item in snapshot
            ],
            "counts_by_type": self.telemetry.counts_by_type(),
        }
        return [self._emit(event_type="telemetry_snapshot", payload=payload)]

    def status(self) -> dict[str, object]:
        game = self.session.game
        menu = self.session.menu
        return {
            "screen": menu.current_screen,
            "player_name": menu.player_name,
            "round": game.current_round,
            "score": game.total_score,
            "shots_remaining": game.shots_remaining,
            "duck_speed": game.duck_speed,
            "ducks_caught": game.ducks_caught,
            "current_map": game.current_map_name,
            "game_active": game.game_active,
            "creature_active": game.creature_active,
            "time_ms": self.timing.current_time_ms,
            "pending_timers": self.timing.pending_count(),
            "telemetry_events": len(self.telemetry.snapshot()),
        }
