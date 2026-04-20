from __future__ import annotations

import unittest

from duck_hunt.timing import TimingEngine


class TestTimingEngine(unittest.TestCase):
    def test_schedule_and_advance_returns_due_actions_in_order(self) -> None:
        engine = TimingEngine()
        engine.schedule_in(100, "a")
        engine.schedule_in(50, "b")

        due = engine.advance(40)
        self.assertEqual(due, [])

        due = engine.advance(10)
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0].action_type, "b")

        due = engine.advance(50)
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0].action_type, "a")
        self.assertEqual(engine.pending_count(), 0)

    def test_invalid_delay_and_advance_values(self) -> None:
        engine = TimingEngine()

        with self.assertRaises(TypeError):
            engine.schedule_in(1.2, "x")

        with self.assertRaises(ValueError):
            engine.schedule_in(-1, "x")

        with self.assertRaises(TypeError):
            engine.advance(1.2)

        with self.assertRaises(ValueError):
            engine.advance(-5)


if __name__ == "__main__":
    unittest.main()
