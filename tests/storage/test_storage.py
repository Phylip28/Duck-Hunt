from __future__ import annotations

import pathlib
import tempfile
import unittest

from duck_hunt.storage import Storage


class TestStorage(unittest.TestCase):
    def test_save_score_sorts_desc(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = pathlib.Path(temp_dir) / "rankings.json"
            storage = Storage(file_path)

            storage.save_score(20, 2, "A", 0)
            storage.save_score(50, 3, "B", 1)
            storage.save_score(35, 4, "C", 2)

            rankings = storage.get_rankings()
            self.assertEqual([entry.score for entry in rankings], [50, 35, 20])
            self.assertEqual(rankings[0].player_name, "B")

    def test_top_rankings_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = pathlib.Path(temp_dir) / "rankings.json"
            storage = Storage(file_path)

            for score in [100, 95, 80, 40]:
                storage.save_score(score, 1, "Player", 0)

            top2 = storage.get_top_rankings(2)
            self.assertEqual(len(top2), 2)
            self.assertEqual([entry.score for entry in top2], [100, 95])

    def test_clear_rankings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = pathlib.Path(temp_dir) / "rankings.json"
            storage = Storage(file_path)

            storage.save_score(10, 1, "X", 0)
            self.assertTrue(file_path.exists())

            storage.clear_rankings()
            self.assertFalse(file_path.exists())
            self.assertEqual(storage.get_rankings(), [])

    def test_invalid_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = pathlib.Path(temp_dir) / "rankings.json"
            storage = Storage(file_path)

            with self.assertRaises(TypeError):
                storage.get_top_rankings(1.2)

            with self.assertRaises(ValueError):
                storage.get_top_rankings(-1)


if __name__ == "__main__":
    unittest.main()
