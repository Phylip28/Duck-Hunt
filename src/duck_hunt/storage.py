"""Storage foundations for Duck Hunt Python migration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class RankingEntry:
    player_name: str
    score: int
    round: int
    map_index: int


class Storage:
    """File-backed ranking storage mirroring JS Storage behavior."""

    STORAGE_KEY = "duckHuntRankings"

    def __init__(
        self, storage_file: str | Path = "data/duck_hunt_rankings.json"
    ) -> None:
        self.storage_file = Path(storage_file)

    def save_score(
        self,
        score: int,
        round_number: int,
        player_name: str = "Player",
        map_index: int = 0,
    ) -> None:
        rankings = self.get_rankings()
        rankings.append(
            RankingEntry(
                player_name=player_name,
                score=int(score),
                round=int(round_number),
                map_index=int(map_index),
            )
        )
        rankings.sort(key=lambda rank: rank.score, reverse=True)
        self._write_rankings(rankings)

    def get_rankings(self) -> list[RankingEntry]:
        if not self.storage_file.exists():
            return []

        raw_data = self.storage_file.read_text(encoding="utf-8").strip()
        if not raw_data:
            return []

        try:
            payload = json.loads(raw_data)
        except json.JSONDecodeError:
            return []

        if not isinstance(payload, list):
            return []

        rankings: list[RankingEntry] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                rankings.append(
                    RankingEntry(
                        player_name=str(item.get("player_name", "Player")),
                        score=int(item.get("score", 0)),
                        round=int(item.get("round", 0)),
                        map_index=int(item.get("map_index", 0)),
                    )
                )
            except (TypeError, ValueError):
                continue

        rankings.sort(key=lambda rank: rank.score, reverse=True)
        return rankings

    def get_top_rankings(self, limit: int = 10) -> list[RankingEntry]:
        if not isinstance(limit, int):
            raise TypeError("limit must be an integer")
        if limit < 0:
            raise ValueError("limit must be >= 0")
        return self.get_rankings()[:limit]

    def clear_rankings(self) -> None:
        if self.storage_file.exists():
            self.storage_file.unlink()

    def _write_rankings(self, rankings: list[RankingEntry]) -> None:
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(rank) for rank in rankings]
        self.storage_file.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
