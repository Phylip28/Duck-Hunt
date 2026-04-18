"""Deterministic RNG contract v1 for Duck Hunt migration."""

from __future__ import annotations

from collections.abc import Mapping

U32_MASK = 0xFFFFFFFF
U32_MOD = 0x100000000

_DEFAULT_CONTEXT = {
    "version": 1,
    "session_nonce": 0,
    "round": 0,
    "map_index": 0,
    "mode": 0,
}


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _to_u32(value: object, field_name: str) -> int:
    if not _is_int(value):
        raise TypeError(f"{field_name} must be an integer")
    return int(value) & U32_MASK


def _rotl32(x: int, r: int) -> int:
    x &= U32_MASK
    return ((x << r) | (x >> (32 - r))) & U32_MASK


def _mix32(x: int) -> int:
    x &= U32_MASK
    x ^= x >> 16
    x = (x * 0x85EBCA6B) & U32_MASK
    x ^= x >> 13
    x = (x * 0xC2B2AE35) & U32_MASK
    x ^= x >> 16
    return x & U32_MASK


def _normalize_context(context: Mapping[str, object] | None) -> dict[str, int]:
    if context is None:
        context = {}

    if not isinstance(context, Mapping):
        raise TypeError("context must be a mapping")

    normalized = dict(_DEFAULT_CONTEXT)
    for key, default in _DEFAULT_CONTEXT.items():
        raw_value = context.get(key, default)
        normalized[key] = _to_u32(raw_value, f"context.{key}")

    return normalized


class RNG:
    """RNG contract v1 with two explicit seeds and one derived seed."""

    def __init__(self) -> None:
        self.seed_a: int | None = None
        self.seed_b: int | None = None
        self.seed_c: int | None = None

        self.x: int | None = None
        self.y: int | None = None
        self.z: int | None = None

        self.calls = 0
        self._initialized = False

    def set_seeds(self, seed_a: object, seed_b: object) -> None:
        self.seed_a = _to_u32(seed_a, "seed_a")
        self.seed_b = _to_u32(seed_b, "seed_b")
        self.derive_seed_c(None)

    def derive_seed_c(self, context: Mapping[str, object] | None) -> int:
        if self.seed_a is None or self.seed_b is None:
            raise RuntimeError("RNG seeds are not initialized. Call set_seeds() first.")

        ctx = _normalize_context(context)

        c = 0x9E3779B9
        c = _mix32(c ^ self.seed_a)
        c = _mix32(c ^ _rotl32(self.seed_b, 16))
        c = _mix32(c ^ ctx["version"])
        c = _mix32(c ^ ctx["session_nonce"])
        c = _mix32(c ^ ctx["round"])
        c = _mix32(c ^ ctx["map_index"])
        c = _mix32(c ^ ctx["mode"])

        if c == 0:
            c = 0xA341316C

        self.seed_c = c
        self.x = self.seed_a if self.seed_a != 0 else 0x6D2B79F5
        self.y = self.seed_b if self.seed_b != 0 else 0x1B56C4E9
        self.z = self.seed_c

        if ((self.x | self.y | self.z) & U32_MASK) == 0:
            self.z = 0xA341316C

        self.calls = 0
        self._initialized = True

        return self.seed_c

    def _require_initialized(self) -> None:
        if not self._initialized or self.x is None or self.y is None or self.z is None:
            raise RuntimeError("RNG state is not initialized. Call set_seeds() first.")

    def next_u32(self) -> int:
        self._require_initialized()

        t = self.x & U32_MASK
        t ^= (t << 16) & U32_MASK
        t ^= t >> 5
        t ^= (t << 1) & U32_MASK

        self.x, self.y = self.y, self.z
        self.z = (t ^ self.x ^ self.y) & U32_MASK

        self.calls += 1
        return self.z

    def next_float(self) -> float:
        return self.next_u32() / float(U32_MOD)

    def randint(self, min_value: object, max_value: object) -> int:
        self._require_initialized()

        if not _is_int(min_value) or not _is_int(max_value):
            raise TypeError("min and max must be integers")

        low = int(min_value)
        high = int(max_value)

        if low > high:
            raise ValueError("min must be <= max")

        span = (high - low) + 1

        if span <= 0 or span > U32_MOD:
            raise ValueError("range size must be in [1, 4294967296]")

        if span == 1:
            return low

        limit = (U32_MOD // span) * span
        r = self.next_u32()
        while r >= limit:
            r = self.next_u32()

        return low + (r % span)
