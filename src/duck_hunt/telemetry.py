"""Telemetry primitives for the migration runtime."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TelemetryEvent:
    seq: int
    timestamp_ms: int
    event_type: str
    payload: dict[str, object] = field(default_factory=dict)


class TelemetryLog:
    """In-memory telemetry log with sequence ordering."""

    def __init__(self) -> None:
        self._events: list[TelemetryEvent] = []
        self._seq = 0

    def record(
        self,
        timestamp_ms: int,
        event_type: str,
        payload: dict[str, object] | None = None,
    ) -> TelemetryEvent:
        if not isinstance(timestamp_ms, int):
            raise TypeError("timestamp_ms must be an integer")

        self._seq += 1
        event = TelemetryEvent(
            seq=self._seq,
            timestamp_ms=timestamp_ms,
            event_type=event_type,
            payload=dict(payload or {}),
        )
        self._events.append(event)
        return event

    def snapshot(self, limit: int | None = None) -> list[TelemetryEvent]:
        if limit is None:
            return list(self._events)
        if not isinstance(limit, int):
            raise TypeError("limit must be an integer or None")
        if limit < 0:
            raise ValueError("limit must be >= 0")
        return list(self._events[-limit:])

    def counts_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self._events:
            counts[event.event_type] = counts.get(event.event_type, 0) + 1
        return counts

    def clear(self) -> None:
        self._events.clear()
        self._seq = 0
