"""Deterministic timing engine for the migration runtime."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimingConfig:
    spawn_delay_ms: int = 1500
    round_delay_ms: int = 3000
    dog_display_ms: int = 1500
    game_over_delay_ms: int = 2500


@dataclass(frozen=True)
class ScheduledAction:
    id: int
    due_time_ms: int
    action_type: str
    payload: dict[str, object] = field(default_factory=dict)


class TimingEngine:
    """Simple in-memory scheduler advanced manually by delta time."""

    def __init__(self, config: TimingConfig | None = None) -> None:
        self.config = config or TimingConfig()
        self.current_time_ms = 0
        self._next_id = 1
        self._queue: list[ScheduledAction] = []

    def schedule_in(
        self,
        delay_ms: int,
        action_type: str,
        payload: dict[str, object] | None = None,
    ) -> ScheduledAction:
        if not isinstance(delay_ms, int):
            raise TypeError("delay_ms must be an integer")
        if delay_ms < 0:
            raise ValueError("delay_ms must be >= 0")

        payload = payload or {}
        action = ScheduledAction(
            id=self._next_id,
            due_time_ms=self.current_time_ms + delay_ms,
            action_type=action_type,
            payload=dict(payload),
        )
        self._next_id += 1
        self._queue.append(action)
        self._queue.sort(key=lambda item: (item.due_time_ms, item.id))
        return action

    def advance(self, delta_ms: int) -> list[ScheduledAction]:
        if not isinstance(delta_ms, int):
            raise TypeError("delta_ms must be an integer")
        if delta_ms < 0:
            raise ValueError("delta_ms must be >= 0")

        self.current_time_ms += delta_ms

        due: list[ScheduledAction] = []
        pending: list[ScheduledAction] = []

        for action in self._queue:
            if action.due_time_ms <= self.current_time_ms:
                due.append(action)
            else:
                pending.append(action)

        self._queue = pending
        return due

    def clear(self) -> None:
        self._queue.clear()

    def pending_count(self) -> int:
        return len(self._queue)
