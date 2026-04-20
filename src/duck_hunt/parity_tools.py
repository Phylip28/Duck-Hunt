"""Parity checker utilities for RNG contract vectors."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .rng import RNG


@dataclass(frozen=True)
class ParityCaseResult:
    name: str
    passed: bool
    mismatches: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "mismatches": list(self.mismatches),
        }


class ParityChecker:
    """Validates RNG output against canonical parity vectors."""

    def __init__(self, vectors_file: str | Path) -> None:
        self.vectors_file = Path(vectors_file)

    def _load_vectors(self) -> dict[str, Any]:
        content = self.vectors_file.read_text(encoding="utf-8")
        return json.loads(content)

    def run_case(self, case: dict[str, Any]) -> ParityCaseResult:
        mismatches: list[str] = []

        rng = RNG()
        rng.set_seeds(case["seed_a"], case["seed_b"])
        seed_c = rng.derive_seed_c(case["context"])

        expected = case["expected"]

        if seed_c != expected["seed_c"]:
            mismatches.append(f"seed_c expected {expected['seed_c']} got {seed_c}")

        u32_actual = [rng.next_u32() for _ in range(10)]
        if u32_actual != expected["first10_u32"]:
            mismatches.append("first10_u32 mismatch")

        rng_float = RNG()
        rng_float.set_seeds(case["seed_a"], case["seed_b"])
        rng_float.derive_seed_c(case["context"])
        float_actual = [rng_float.next_float() for _ in range(3)]
        for index, (actual, exp) in enumerate(
            zip(float_actual, expected["first3_float"])
        ):
            if abs(actual - exp) > 1e-15:
                mismatches.append(f"first3_float[{index}] expected {exp} got {actual}")

        rng_int = RNG()
        rng_int.set_seeds(case["seed_a"], case["seed_b"])
        rng_int.derive_seed_c(case["context"])
        if rng_int.randint(0, 0) != expected["sample_randint"]["range_0_0"]:
            mismatches.append("sample randint range_0_0 mismatch")
        if rng_int.randint(0, 5) != expected["sample_randint"]["range_0_5"]:
            mismatches.append("sample randint range_0_5 mismatch")
        if rng_int.randint(10, 20) != expected["sample_randint"]["range_10_20"]:
            mismatches.append("sample randint range_10_20 mismatch")

        return ParityCaseResult(
            name=str(case["name"]),
            passed=(len(mismatches) == 0),
            mismatches=mismatches,
        )

    def run_all(self) -> dict[str, Any]:
        vectors = self._load_vectors()
        results = [self.run_case(case) for case in vectors["cases"]]
        passed = [item for item in results if item.passed]
        failed = [item for item in results if not item.passed]

        return {
            "contract_version": vectors.get("contract_version", "unknown"),
            "total_cases": len(results),
            "passed_cases": len(passed),
            "failed_cases": len(failed),
            "passed": len(failed) == 0,
            "results": [item.to_dict() for item in results],
        }
