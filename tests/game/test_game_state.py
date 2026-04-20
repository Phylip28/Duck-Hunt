from __future__ import annotations

import unittest

from duck_hunt.config import Config
from duck_hunt.game_state import GameState
from duck_hunt.rng import RNG


class TestGameState(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config()
        self.rng = RNG()
        self.game = GameState(self.config, self.rng)

    def test_start_new_game_initializes_state(self) -> None:
        self.game.start_new_game(123456789, 362436069)

        self.assertTrue(self.game.game_active)
        self.assertEqual(self.game.current_round, 1)
        self.assertEqual(self.game.total_score, 0)
        self.assertEqual(self.game.duck_speed, self.config.initial_duck_speed)
        self.assertIn(self.game.current_map_name, [m.name for m in self.config.maps])

    def test_hit_after_one_miss_gives_second_shot_points(self) -> None:
        self.game.start_new_game(123, 456)
        self.game.spawn_next_creature()

        miss_result = self.game.record_miss()
        self.assertEqual(miss_result.result, "creature_alive")

        hit_result = self.game.record_hit()
        self.assertEqual(hit_result.result, "creature_cleared")
        self.assertEqual(hit_result.points, self.config.points_second_shot)

    def test_three_misses_trigger_game_over(self) -> None:
        self.game.start_new_game(999, 111)
        self.game.spawn_next_creature()

        self.game.record_miss()
        self.game.record_miss()
        final_result = self.game.record_miss()

        self.assertEqual(final_result.result, "game_over")
        self.assertFalse(self.game.game_active)

    def test_round_completion_applies_bonus_and_progression(self) -> None:
        self.game.start_new_game(7, 8)
        initial_speed = self.game.duck_speed

        for _ in range(self.config.ducks_per_round - 1):
            self.game.spawn_next_creature()
            hit_result = self.game.record_hit()
            self.assertEqual(hit_result.result, "creature_cleared")

        self.game.spawn_next_creature()
        final_hit = self.game.record_hit()

        self.assertEqual(final_hit.result, "round_completed")
        self.assertEqual(final_hit.round_bonus, 10)
        self.assertEqual(self.game.current_round, 2)
        self.assertEqual(
            self.game.duck_speed, initial_speed + self.config.speed_increase_per_round
        )


if __name__ == "__main__":
    unittest.main()
