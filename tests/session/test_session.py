from __future__ import annotations

import pathlib
import tempfile
import unittest

from duck_hunt.config import Config
from duck_hunt.session import Session
from duck_hunt.rng import RNG
from duck_hunt.storage import Storage


class TestSession(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        storage_file = pathlib.Path(self.temp_dir.name) / "rankings.json"
        self.storage = Storage(storage_file)
        self.config = Config()
        self.rng = RNG()
        self.session = Session(config=self.config, rng=self.rng, storage=self.storage)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_start_new_game_initializes_menu_and_game(self) -> None:
        self.session.start_new_game("PlayerX", seed_a=123, seed_b=456)

        self.assertEqual(self.session.menu.player_name, "PlayerX")
        self.assertEqual(self.session.menu.current_screen, self.session.menu.GAME_SCENE)
        self.assertTrue(self.session.game.game_active)

    def test_miss_until_game_over_persists_score(self) -> None:
        self.session.start_new_game("PlayerY", seed_a=77, seed_b=88)
        self.session.spawn_next_creature()

        self.session.miss_current_creature()
        self.session.miss_current_creature()
        result = self.session.miss_current_creature()

        self.assertEqual(result.result, "game_over")
        self.assertEqual(self.session.menu.current_screen, self.session.menu.GAME_OVER_SCREEN)

        rankings = self.storage.get_rankings()
        self.assertEqual(len(rankings), 1)
        self.assertEqual(rankings[0].player_name, "PlayerY")
        self.assertEqual(rankings[0].score, self.session.game.total_score)

    def test_stop_game_and_return_to_menu(self) -> None:
        self.session.start_new_game("PlayerZ", seed_a=12, seed_b=34)
        self.session.spawn_next_creature()

        self.session.stop_game_and_return_to_menu()

        self.assertFalse(self.session.game.game_active)
        self.assertFalse(self.session.game.creature_active)
        self.assertEqual(self.session.menu.current_screen, self.session.menu.MAIN_MENU)


if __name__ == "__main__":
    unittest.main()
