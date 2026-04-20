from __future__ import annotations

import unittest

from duck_hunt.telemetry import TelemetryLog


class TestTelemetryLog(unittest.TestCase):
    def test_record_snapshot_and_counts(self) -> None:
        log = TelemetryLog()
        log.record(0, "session_started", {"player": "A"})
        log.record(10, "creature_spawned", {"round": 1})
        log.record(20, "action_resolved", {"result": "hit"})

        snapshot = log.snapshot()
        self.assertEqual(len(snapshot), 3)
        self.assertEqual(snapshot[0].seq, 1)
        self.assertEqual(snapshot[-1].event_type, "action_resolved")

        tail = log.snapshot(limit=2)
        self.assertEqual(len(tail), 2)
        self.assertEqual(tail[0].event_type, "creature_spawned")

        counts = log.counts_by_type()
        self.assertEqual(counts["session_started"], 1)
        self.assertEqual(counts["creature_spawned"], 1)
        self.assertEqual(counts["action_resolved"], 1)

    def test_snapshot_validation(self) -> None:
        log = TelemetryLog()

        with self.assertRaises(TypeError):
            log.record(1.2, "x", {})

        with self.assertRaises(TypeError):
            log.snapshot(limit=1.2)

        with self.assertRaises(ValueError):
            log.snapshot(limit=-1)


if __name__ == "__main__":
    unittest.main()
