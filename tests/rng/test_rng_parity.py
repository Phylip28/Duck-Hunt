from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PYTHON_SRC = ROOT / "src"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from duck_hunt.rng import RNG, U32_MOD  # noqa: E402


def _load_vectors() -> dict:
    vectors_file = ROOT / "tests" / "rng" / "parity_vectors.json"
    return json.loads(vectors_file.read_text(encoding="utf-8"))


class TestRngParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vectors = _load_vectors()

    def test_contract_version(self) -> None:
        self.assertEqual(self.vectors["contract_version"], "v1")

    def test_vector_parity(self) -> None:
        for case in self.vectors["cases"]:
            with self.subTest(case=case["name"]):
                rng = RNG()
                rng.set_seeds(case["seed_a"], case["seed_b"])
                seed_c = rng.derive_seed_c(case["context"])
                self.assertEqual(seed_c, case["expected"]["seed_c"])

                first10_u32 = [rng.next_u32() for _ in range(10)]
                self.assertEqual(first10_u32, case["expected"]["first10_u32"])

                rng = RNG()
                rng.set_seeds(case["seed_a"], case["seed_b"])
                rng.derive_seed_c(case["context"])
                first3_float = [rng.next_float() for _ in range(3)]
                for actual, expected in zip(
                    first3_float, case["expected"]["first3_float"]
                ):
                    self.assertAlmostEqual(actual, expected, places=15)

                rng = RNG()
                rng.set_seeds(case["seed_a"], case["seed_b"])
                rng.derive_seed_c(case["context"])
                self.assertEqual(
                    rng.randint(0, 0), case["expected"]["sample_randint"]["range_0_0"]
                )
                self.assertEqual(
                    rng.randint(0, 5), case["expected"]["sample_randint"]["range_0_5"]
                )
                self.assertEqual(
                    rng.randint(10, 20),
                    case["expected"]["sample_randint"]["range_10_20"],
                )

                expected_seed_a = case["expected"].get("normalized_seed_a")
                if expected_seed_a is not None:
                    self.assertEqual(rng.seed_a, expected_seed_a)

                expected_seed_b = case["expected"].get("normalized_seed_b")
                if expected_seed_b is not None:
                    self.assertEqual(rng.seed_b, expected_seed_b)

    def test_deterministic_replay(self) -> None:
        case = self.vectors["cases"][1]

        rng_a = RNG()
        rng_a.set_seeds(case["seed_a"], case["seed_b"])
        rng_a.derive_seed_c(case["context"])
        run_a = [rng_a.next_u32() for _ in range(25)]

        rng_b = RNG()
        rng_b.set_seeds(case["seed_a"], case["seed_b"])
        rng_b.derive_seed_c(case["context"])
        run_b = [rng_b.next_u32() for _ in range(25)]

        self.assertEqual(run_a, run_b)

    def test_uninitialized_state_errors(self) -> None:
        rng = RNG()
        with self.assertRaises(RuntimeError):
            rng.next_u32()
        with self.assertRaises(RuntimeError):
            rng.next_float()
        with self.assertRaises(RuntimeError):
            rng.randint(0, 1)

    def test_invalid_seed_types(self) -> None:
        rng = RNG()
        with self.assertRaises(TypeError):
            rng.set_seeds("1", 2)
        with self.assertRaises(TypeError):
            rng.set_seeds(1.2, 2)
        with self.assertRaises(TypeError):
            rng.set_seeds(True, 2)

    def test_invalid_context_types(self) -> None:
        rng = RNG()
        rng.set_seeds(1, 2)

        with self.assertRaises(TypeError):
            rng.derive_seed_c("bad")

        with self.assertRaises(TypeError):
            rng.derive_seed_c({"round": 1.5})

        with self.assertRaises(TypeError):
            rng.derive_seed_c({"mode": None})

    def test_randint_validation(self) -> None:
        rng = RNG()
        rng.set_seeds(1, 2)

        with self.assertRaises(ValueError):
            rng.randint(5, 4)

        with self.assertRaises(TypeError):
            rng.randint(0.1, 4)

        with self.assertRaises(ValueError):
            rng.randint(0, U32_MOD)


if __name__ == "__main__":
    unittest.main()
