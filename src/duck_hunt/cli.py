"""Minimal CLI simulation entrypoint for migrated logic."""

from __future__ import annotations

import json

from .command_adapter import CommandAdapter
from .config import Config
from .rng import RNG
from .runtime import GameRuntime
from .session import Session
from .storage import Storage


def main() -> None:
    config = Config()
    rng = RNG()
    storage = Storage()
    session = Session(config=config, rng=rng, storage=storage)
    runtime = GameRuntime(session)
    adapter = CommandAdapter(runtime)

    print("Duck Hunt CLI (migration mode)")
    print(
        "Commands: start <name> <seed_a> <seed_b> | "
        "hit | miss | status | tick <ms> | telemetry [limit] | "
        "rng-seq <seed_a> <seed_b> <length> [round map session_nonce mode version] | "
        "plan <seed_a> <seed_b> <rounds> [creatures_per_round] | "
        "parity-check | quit"
    )

    while True:
        raw = input("dh> ").strip()
        if raw.lower() in {"quit", "exit"}:
            print("bye")
            break

        try:
            events = adapter.execute(raw)
            for event in events:
                print(
                    json.dumps(
                        {"type": event.type, "payload": event.payload},
                        ensure_ascii=True,
                    )
                )
        except Exception as exc:  # pragma: no cover - user-facing loop
            print(f"error: {exc}")


if __name__ == "__main__":
    main()
