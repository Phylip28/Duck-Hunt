from __future__ import annotations

import pathlib
import tempfile
import unittest

from duck_hunt.config import Config
from duck_hunt.menu_flow import MenuFlow
from duck_hunt.storage import Storage


class TestMenuFlow(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        storage_file = pathlib.Path(self.temp_dir.name) / "rankings.json"
        self.storage = Storage(storage_file)
        self.config = Config()
        self.menu = MenuFlow(config=self.config, storage=self.storage)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_confirm_player_name_requires_non_empty_value(self) -> None:
        self.menu.show_player_name_modal()
        with self.assertRaises(ValueError):
            self.menu.confirm_player_name("   ")

    def test_confirm_player_name_transitions_to_game_scene(self) -> None:
        self.menu.show_player_name_modal()
        self.menu.confirm_player_name("  Phylip  ")

        self.assertEqual(self.menu.player_name, "Phylip")
        self.assertEqual(self.menu.current_screen, MenuFlow.GAME_SCENE)

    def test_show_game_over_persists_score(self) -> None:
        self.menu.confirm_player_name("PlayerOne")
        self.menu.show_game_over(final_score=42, final_round=3, map_index=2)

        self.assertEqual(self.menu.current_screen, MenuFlow.GAME_OVER_SCREEN)
        rankings = self.storage.get_rankings()
        self.assertEqual(len(rankings), 1)
        self.assertEqual(rankings[0].player_name, "PlayerOne")
        self.assertEqual(rankings[0].score, 42)
        self.assertEqual(rankings[0].round, 3)
        self.assertEqual(rankings[0].map_index, 2)

    def test_rankings_view_maps_names_and_unknown(self) -> None:
        self.storage.save_score(10, 1, "A", 0)
        self.storage.save_score(20, 2, "B", 999)

        view = self.menu.get_rankings_view()
        self.assertEqual(len(view), 2)

        self.assertEqual(view[0].player_name, "B")
        self.assertEqual(view[0].map_name, "Unknown")

        self.assertEqual(view[1].player_name, "A")
        self.assertEqual(view[1].map_name, self.config.maps[0].name)


if __name__ == "__main__":
    unittest.main()
