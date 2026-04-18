"""Menu flow domain logic for the Python migration."""

from __future__ import annotations

from dataclasses import dataclass

from .config import Config
from .storage import Storage


@dataclass(frozen=True)
class RankingRow:
    rank: int
    player_name: str
    score: int
    map_name: str
    round: int


class MenuFlow:
    """Non-UI menu state and actions mirroring JS menu behavior."""

    MAIN_MENU = "main_menu"
    PLAYER_NAME_MODAL = "player_name_modal"
    RANKINGS_MENU = "rankings_menu"
    GAME_SCENE = "game_scene"
    GAME_OVER_SCREEN = "game_over_screen"

    def __init__(self, config: Config, storage: Storage) -> None:
        self.config = config
        self.storage = storage

        self.current_screen = self.MAIN_MENU
        self.player_name = ""
        self.selected_map: int | None = None

        self.final_score = 0
        self.final_round = 1

    def show_main_menu(self) -> None:
        self.current_screen = self.MAIN_MENU
        self.selected_map = None

    def show_player_name_modal(self) -> None:
        self.current_screen = self.PLAYER_NAME_MODAL

    def confirm_player_name(self, player_name: str) -> None:
        clean_name = player_name.strip()
        if not clean_name:
            raise ValueError("Please enter your name")

        self.player_name = clean_name
        self.current_screen = self.GAME_SCENE

    def cancel_player_name(self) -> None:
        self.player_name = ""
        self.show_main_menu()

    def show_rankings(self) -> None:
        self.current_screen = self.RANKINGS_MENU

    def get_rankings_view(self, limit: int = 10) -> list[RankingRow]:
        rankings = self.storage.get_top_rankings(limit)
        rows: list[RankingRow] = []

        for index, rank in enumerate(rankings, start=1):
            if 0 <= rank.map_index < len(self.config.maps):
                map_name = self.config.maps[rank.map_index].name
            else:
                map_name = "Unknown"

            rows.append(
                RankingRow(
                    rank=index,
                    player_name=rank.player_name,
                    score=rank.score,
                    map_name=map_name,
                    round=rank.round,
                )
            )

        return rows

    def show_game_over(
        self, final_score: int, final_round: int, map_index: int = 0
    ) -> None:
        self.current_screen = self.GAME_OVER_SCREEN
        self.final_score = int(final_score)
        self.final_round = int(final_round)

        self.storage.save_score(
            self.final_score,
            self.final_round,
            self.player_name or "Player",
            int(map_index),
        )

    def back_to_menu_from_game_over(self) -> None:
        self.show_main_menu()

    def clear_rankings(self) -> None:
        self.storage.clear_rankings()
