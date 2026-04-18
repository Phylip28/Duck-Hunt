from __future__ import annotations

import pathlib
import tempfile
import unittest

from duck_hunt.command_adapter import CommandAdapter
from duck_hunt.config import Config
from duck_hunt.rng import RNG
from duck_hunt.runtime import GameRuntime
from duck_hunt.session import Session
from duck_hunt.storage import Storage


class TestCommandAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        storage_file = pathlib.Path(self.temp_dir.name) / "rankings.json"
        storage = Storage(storage_file)
        session = Session(config=Config(), rng=RNG(), storage=storage)
        runtime = GameRuntime(session=session)
        self.adapter = CommandAdapter(runtime=runtime)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_start_command_supports_names_with_spaces(self) -> None:
        events = self.adapter.execute("start Player One 123 456")
        self.assertEqual(events[0].type, "session_started")
        self.assertEqual(events[0].payload["player_name"], "Player One")

    def test_status_command_returns_status_event(self) -> None:
        self.adapter.execute("start P 1 2")
        events = self.adapter.execute("status")
        self.assertEqual(events[0].type, "status")
        self.assertTrue(events[0].payload["game_active"])

    def test_tick_command_advances_runtime_time(self) -> None:
        self.adapter.execute("start P 1 2")
        events = self.adapter.execute("tick 1500")

        self.assertEqual(events[0].type, "time_advanced")
        self.assertEqual(events[0].payload["time_ms"], 1500)
        self.assertEqual(events[1].type, "timer_elapsed")

    def test_telemetry_command_returns_snapshot(self) -> None:
        self.adapter.execute("start P 1 2")
        events = self.adapter.execute("telemetry 3")

        self.assertEqual(events[0].type, "telemetry_snapshot")
        self.assertLessEqual(events[0].payload["count"], 3)

    def test_tick_requires_integer_delta(self) -> None:
        with self.assertRaises(ValueError):
            self.adapter.execute("tick x")

    def test_telemetry_requires_integer_limit(self) -> None:
        with self.assertRaises(ValueError):
            self.adapter.execute("telemetry x")

    def test_invalid_command_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.adapter.execute("dance")

    def test_empty_command_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.adapter.execute("   ")


if __name__ == "__main__":
    unittest.main()
