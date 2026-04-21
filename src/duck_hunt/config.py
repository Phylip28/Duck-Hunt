"""Configuration foundations migrated from JS to Python (phase 1)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .rng import RNG


@dataclass(frozen=True)
class CreatureType:
    name: str
    image_names_key: str
    width: int
    height: int
    base_speed: int
    movement_type: str


@dataclass(frozen=True)
class GameMap:
    name: str
    file: str


class Config:
    """Python configuration mirror for gameplay constants and RNG-driven selectors."""

    def __init__(self, game_width: int = 0, game_height: int = 0) -> None:
        self.game_width = game_width
        self.game_height = game_height

        self.duck_image_names = ["duck-left.gif", "duck-right.gif"]
        self.seagull_image_names = ["seagull-left.gif", "seagull-right.gif"]
        self.ghost_image_names = ["ghost-left.gif", "ghost-right.gif"]
        self.bat_image_names = ["bat-left.gif", "bat-right.gif"]

        self.duck_width = 120
        self.duck_height = 115
        self.seagull_width = 160
        self.seagull_height = 135
        self.ghost_width = 100
        self.ghost_height = 120
        self.bat_width = 160
        self.bat_height = 160

        self.creature_types = {
            "duck": CreatureType("duck", "duck_image_names", 120, 115, 4, "linear"),
            "seagull": CreatureType(
                "seagull", "seagull_image_names", 160, 135, 5, "linear"
            ),
            "ghost": CreatureType("ghost", "ghost_image_names", 130, 150, 3, "wave"),
            "bat": CreatureType("bat", "bat_image_names", 160, 160, 6, "zigzag"),
        }

        self.available_creature_types = ["duck", "seagull", "bat"]

        self.ducks_per_round = 6
        self.shots_per_duck = 3

        self.points_first_shot = 3
        self.points_second_shot = 2
        self.points_third_shot = 1
        self.round_bonus_multiplier = 10

        self.initial_duck_speed = 4
        self.speed_increase_per_round = 1.15

        self.maps = [
            GameMap("PLAGUE", "assets/images/backgrounds/bg-plague.jpg"),
            GameMap("DANGER ZONE", "assets/images/backgrounds/bg-nuclear.jpg"),
            GameMap("HAUNTED CASTLE", "assets/images/backgrounds/bg-castle.jpg"),
            GameMap("WITCH HOUSE", "assets/images/backgrounds/bg-moon.jpg"),
            GameMap("GATE TO HELL", "assets/images/backgrounds/bg-volcano.jpg"),
            GameMap("HELL", "assets/images/backgrounds/bg-hell.jpg"),
        ]

        self.creature_rules_by_background = {
            "bg-moon.jpg": ["bat"],
            "bg-castle.jpg": ["ghost"],
            "bg-hell.jpg": ["duck"],
            "bg-volcano.jpg": ["duck"],
            "bg-nuclear.jpg": ["seagull"],
        }

        self.random_map_queue: list[int] = []

        self.sounds = {
            "duck_shot": "assets/audio/sfx/duck-shot.mp3",
            "duck_flap": "assets/audio/sfx/duck-flap.mp3",
            "duck_quack": "assets/audio/sfx/duck-quack.mp3",
            "dog_score": "assets/audio/sfx/dog-score.mp3",
            "soundtrack": "assets/audio/music/soundtrack.mp3",
        }

        self.images = {
            "background": "assets/images/backgrounds/duckhunt-bg-4k.jpg",
            "target": "assets/images/targets/target.png",
            "dog_happy_with_duck": "assets/images/creatures/dog-duck1.png",
            "dog_sad": "assets/images/creatures/dog-duck2.png",
            "duck_left": "assets/images/creatures/duck-left.gif",
            "duck_right": "assets/images/creatures/duck-right.gif",
        }

        self.fonts = {"game_font": "assets/fonts/game-font.otf"}

    def get_random_creature_type(self, rng: RNG, map_file: str | None = None) -> str:
        allowed_types = self._allowed_creature_types_for_map(map_file)
        index = rng.randint(0, len(allowed_types) - 1)
        return allowed_types[index]

    def _allowed_creature_types_for_map(self, map_file: str | None) -> list[str]:
        if map_file is None:
            allowed = list(self.available_creature_types)
        else:
            background_name = Path(map_file).name
            allowed = self.creature_rules_by_background.get(
                background_name,
                self.available_creature_types,
            )

        valid_allowed = [name for name in allowed if name in self.creature_types]
        if not valid_allowed:
            raise RuntimeError("No creature types available for map")
        return valid_allowed

    def generate_random_map_queue(self, rng: RNG) -> list[int]:
        indices = list(range(len(self.maps)))

        # Fisher-Yates shuffle driven by deterministic RNG.
        for i in range(len(indices) - 1, 0, -1):
            j = rng.randint(0, i)
            indices[i], indices[j] = indices[j], indices[i]

        self.random_map_queue = indices
        return list(indices)

    def get_next_random_map(self, round_number: int, rng: RNG) -> GameMap:
        del round_number  # Kept for API compatibility with JS side.

        if not self.random_map_queue:
            self.generate_random_map_queue(rng)

        map_index = self.random_map_queue.pop(0)
        return self.maps[map_index]

    def round_to_map_index(self, round_number: int) -> int:
        if round_number <= 2:
            return 0
        if round_number <= 4:
            return 1
        if round_number <= 6:
            return 2
        if round_number <= 8:
            return 3
        if round_number <= 10:
            return 4
        if round_number <= 12:
            return 5
        return 5
