from __future__ import annotations

import pathlib
import tempfile
import unittest

from duck_hunt.config import Config
from duck_hunt.rng import RNG
from duck_hunt.runtime import GameRuntime
from duck_hunt.session import Session
from duck_hunt.storage import Storage


class TestGameRuntime(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        storage_file = pathlib.Path(self.temp_dir.name) / "rankings.json"
        self.storage = Storage(storage_file)
        self.config = Config()
        self.rng = RNG()
        self.session = Session(config=self.config, rng=self.rng, storage=self.storage)
        self.runtime = GameRuntime(session=self.session)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_start_emits_session_and_spawn_events(self) -> None:
        events = self.runtime.start(player_name="PlayerA", seed_a=1, seed_b=2)
        self.assertEqual(
            [event.type for event in events], ["session_started", "creature_spawned"]
        )
        self.assertEqual(events[0].payload["player_name"], "PlayerA")

    def test_hit_emits_action_and_spawn(self) -> None:
        self.runtime.start(player_name="PlayerB", seed_a=3, seed_b=4)
        events = self.runtime.perform_action("hit")

        self.assertEqual(events[0].type, "action_resolved")
        self.assertEqual(events[0].payload["action"], "hit")
        self.assertEqual(events[1].type, "creature_spawned")

    def test_round_completion_emits_round_completed(self) -> None:
        self.runtime.start(player_name="PlayerC", seed_a=5, seed_b=6)

        final_events = []
        for _ in range(self.config.ducks_per_round):
            final_events = self.runtime.perform_action("hit")

        event_types = [event.type for event in final_events]
        self.assertIn("round_completed", event_types)
        self.assertEqual(self.session.game.current_round, 2)

    def test_three_misses_emit_game_over_event(self) -> None:
        self.runtime.start(player_name="PlayerD", seed_a=7, seed_b=8)

        self.runtime.perform_action("miss")
        self.runtime.perform_action("miss")
        events = self.runtime.perform_action("miss")

        self.assertEqual(events[-1].type, "game_over")
        self.assertEqual(
            self.session.menu.current_screen, self.session.menu.GAME_OVER_SCREEN
        )

    def test_advance_time_emits_timer_elapsed_events(self) -> None:
        self.runtime.start(player_name="PlayerE", seed_a=9, seed_b=10)
        events = self.runtime.advance_time(1500)

        self.assertEqual(events[0].type, "time_advanced")
        self.assertEqual(events[0].payload["due_actions"], 1)
        self.assertEqual(events[1].type, "timer_elapsed")

        status = self.runtime.status()
        self.assertEqual(status["time_ms"], 1500)
        self.assertGreaterEqual(status["telemetry_events"], 2)


if __name__ == "__main__":
    unittest.main()
