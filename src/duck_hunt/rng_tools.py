"""Utilities for RNG experimentation and reproducibility reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .rng import RNG


@dataclass(frozen=True)
class SeedContext:
    version: int = 1
    session_nonce: int = 0
    round: int = 0
    map_index: int = 0
    mode: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class RNGPreview:
    seed_a: int
    seed_b: int
    seed_c: int
    context: SeedContext
    u32_sequence: list[int]
    float_sequence: list[float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed_a": self.seed_a,
            "seed_b": self.seed_b,
            "seed_c": self.seed_c,
            "context": self.context.to_dict(),
            "u32_sequence": self.u32_sequence,
            "float_sequence": self.float_sequence,
        }


def preview_sequence(
    seed_a: int,
    seed_b: int,
    length: int,
    context: SeedContext | None = None,
    float_count: int = 3,
) -> RNGPreview:
    if not isinstance(length, int):
        raise TypeError("length must be an integer")
    if length < 0:
        raise ValueError("length must be >= 0")
    if not isinstance(float_count, int):
        raise TypeError("float_count must be an integer")
    if float_count < 0:
        raise ValueError("float_count must be >= 0")

    ctx = context or SeedContext()

    rng = RNG()
    rng.set_seeds(seed_a, seed_b)
    seed_c = rng.derive_seed_c(ctx.to_dict())

    u32_sequence = [rng.next_u32() for _ in range(length)]

    rng_float = RNG()
    rng_float.set_seeds(seed_a, seed_b)
    rng_float.derive_seed_c(ctx.to_dict())
    float_sequence = [rng_float.next_float() for _ in range(float_count)]

    return RNGPreview(
        seed_a=rng.seed_a if rng.seed_a is not None else 0,
        seed_b=rng.seed_b if rng.seed_b is not None else 0,
        seed_c=seed_c,
        context=ctx,
        u32_sequence=u32_sequence,
        float_sequence=float_sequence,
    )
