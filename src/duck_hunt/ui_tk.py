"""Pygame gameplay UI for Duck Hunt."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image, ImageSequence
except ModuleNotFoundError:  # pragma: no cover - optional at import time
    Image = None
    ImageSequence = None

try:
    import pygame
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency
    raise SystemExit("pygame is required. Run: uv sync") from exc

if __package__:
    from .config import Config
    from .rng import RNG
    from .runtime import GameRuntime
    from .session import Session
    from .storage import Storage
else:
    # Allow `python src/duck_hunt/ui_tk.py` by adding `src` to sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from duck_hunt.config import Config
    from duck_hunt.rng import RNG
    from duck_hunt.runtime import GameRuntime
    from duck_hunt.session import Session
    from duck_hunt.storage import Storage


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
TOP_MARGIN = 72
BOTTOM_MARGIN = 132


@dataclass
class CreatureSprite:
    kind: str
    movement_type: str
    width: int
    height: int
    x: float
    y: float
    vx: float
    vy: float
    phase: float
    age: float = 0.0

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, dt: float, width_limit: int, height_limit: int) -> None:
        self.age += dt
        self.x += self.vx * dt

        if self.movement_type == "zigzag":
            self.y += (self.vy + math.sin((self.age * 8.0) + self.phase) * 130.0) * dt
        elif self.movement_type == "wave":
            self.y += (self.vy + math.sin((self.age * 5.0) + self.phase) * 95.0) * dt
        else:
            self.y += self.vy * dt

        min_y = TOP_MARGIN
        max_y = height_limit - BOTTOM_MARGIN - self.height
        if self.y < min_y:
            self.y = float(min_y)
            self.vy = abs(self.vy) + 12.0
        elif self.y > max_y:
            self.y = float(max_y)
            self.vy = -abs(self.vy) - 12.0

        min_x = -self.width * 0.35
        max_x = width_limit - (self.width * 0.65)
        if self.x < min_x:
            self.x = min_x
            self.vx = abs(self.vx)
        elif self.x > max_x:
            self.x = max_x
            self.vx = -abs(self.vx)


class DuckHuntTkApp:
    """Backward-compatible class name with a real Pygame game UI."""

    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Duck Hunt - Python")
        self.clock = pygame.time.Clock()
        self.running = True

        self.config = Config(game_width=WINDOW_WIDTH, game_height=WINDOW_HEIGHT)
        self.storage = Storage()
        self.session = Session(config=self.config, rng=RNG(), storage=self.storage)
        self.runtime = GameRuntime(session=self.session)

        self.repo_root = Path(__file__).resolve().parents[2]
        self.background_cache = self._load_background_cache()
        self.menu_background = self._load_menu_background()
        self.menu_blood_layers = self._load_menu_blood_layers()
        self.dog_hunter_surface = self._load_dog_hunter_surface()
        self.name_entry_illustration = self._load_name_entry_illustration()
        self.map_preview_cache = self._build_map_preview_cache()
        self.creature_frames = self._load_creature_frames()
        self.target_surface = self._load_target_surface()
        self.scanline_overlay = self._build_scanline_overlay()

        self.title_font = self._load_font(54)
        self.hud_font = self._load_font(28)
        self.body_font = self._load_font(22)
        self.small_font = self._load_font(18)

        self.state = "menu"
        self.last_message = "Selecciona una opcion"
        self.banner_text = ""
        self.banner_timer = 0.0

        self.current_creature: CreatureSprite | None = None
        self.hit_flash = 0.0
        self.miss_flash = 0.0

        self.menu_pulse = 0.0

        self.menu_option_order = ["play", "instructions", "rankings", "seed"]
        self.menu_selected_index = 0
        self.menu_option_rects: dict[str, pygame.Rect] = {}

        self.selected_seed_index = 0
        self.seed_presets = [
            ("Clasica", "123456789", "362436069"),
            ("Arcade", "42424242", "13371337"),
            ("Caos", "987654321", "123123123"),
            ("Infierno", "66666666", "314159265"),
        ]

        self.player_name_input = ""
        self.name_confirm_rect = pygame.Rect(0, 0, 0, 0)
        self.name_back_rect = pygame.Rect(0, 0, 0, 0)
        self.instructions_back_rect = pygame.Rect(0, 0, 0, 0)
        self.rankings_back_rect = pygame.Rect(0, 0, 0, 0)

        self.pending_player_name = ""
        self.pending_seed_a = 0
        self.pending_seed_b = 0
        self.selected_map_index = 0
        self.map_selector_rng = RNG()
        self.map_carousel_running = False
        self.map_carousel_position = 0.0
        self.map_carousel_start_pos = 0.0
        self.map_carousel_end_pos = 0.0
        self.map_carousel_target_index = 0
        self.map_carousel_elapsed_ms = 0
        self.map_carousel_duration_ms = 0

    def _load_font(self, size: int) -> pygame.font.Font:
        font_path = self.repo_root / self.config.fonts["game_font"]
        if font_path.exists():
            try:
                return pygame.font.Font(str(font_path), size)
            except OSError:
                pass
        return pygame.font.SysFont("verdana", size, bold=True)

    def _load_background_cache(self) -> dict[str, pygame.Surface]:
        cache: dict[str, pygame.Surface] = {}
        for game_map in self.config.maps:
            bg_path = self.repo_root / game_map.file
            if not bg_path.exists():
                continue
            try:
                image = pygame.image.load(str(bg_path)).convert()
            except pygame.error:
                continue
            cache[game_map.name] = pygame.transform.smoothscale(
                image, (WINDOW_WIDTH, WINDOW_HEIGHT)
            )
        return cache

    def _load_menu_background(self) -> pygame.Surface | None:
        bg_path = self.repo_root / "assets/images/bg-menu.jpg"
        if not bg_path.exists():
            return None
        try:
            image = pygame.image.load(str(bg_path)).convert()
        except pygame.error:
            return None
        return pygame.transform.smoothscale(image, (WINDOW_WIDTH, WINDOW_HEIGHT))

    def _load_menu_blood_layers(self) -> list[pygame.Surface]:
        layers: list[pygame.Surface] = []
        for path in [
            self.repo_root / "assets/images/blood.png",
            self.repo_root / "assets/images/blood2.png",
        ]:
            surface = self._load_surface(path)
            if surface is None:
                continue
            layers.append(surface)
        return layers

    def _load_dog_hunter_surface(self) -> pygame.Surface | None:
        candidates = [
            self.repo_root / "assets/images/dog-duck1.png",
            self.repo_root / "assets/images/dog-duck2.png",
        ]
        for path in candidates:
            surface = self._load_surface(path)
            if surface is not None:
                return surface
        return None

    def _load_name_entry_illustration(self) -> pygame.Surface | None:
        candidates = [
            self.repo_root / "assets/images/name_screeen.jpeg",
            self.repo_root / "assets/images/ilustracion.png",
        ]
        for path in candidates:
            image = self._load_surface(path)
            if image is not None:
                return image
        return None

    def _build_map_preview_cache(self) -> dict[int, pygame.Surface]:
        previews: dict[int, pygame.Surface] = {}
        card_size = (360, 202)

        for idx, game_map in enumerate(self.config.maps):
            bg = self.background_cache.get(game_map.name)
            if bg is not None:
                card = pygame.transform.smoothscale(bg, card_size)
            else:
                card = pygame.Surface(card_size)
                card.fill((58, 26, 28))

            shade = pygame.Surface(card_size, pygame.SRCALPHA)
            shade.fill((12, 4, 6, 36))
            card.blit(shade, (0, 0))
            previews[idx] = card

        return previews

    def _load_creature_frames(self) -> dict[str, dict[str, list[pygame.Surface]]]:
        frames: dict[str, dict[str, list[pygame.Surface]]] = {}
        base_dir = self.repo_root / "assets/images"

        for creature_name, spec in self.config.creature_types.items():
            image_names = getattr(self.config, spec.image_names_key, None)
            if not isinstance(image_names, list) or len(image_names) < 2:
                continue

            left_name = image_names[0]
            right_name = image_names[1]

            left_path = base_dir / left_name
            right_path = base_dir / right_name

            left_frames = self._load_animation_frames(left_path)
            right_frames = self._load_animation_frames(right_path)

            if not left_frames and not right_frames:
                continue

            if not left_frames and right_frames:
                left_frames = [
                    pygame.transform.flip(surface, True, False)
                    for surface in right_frames
                ]
            if not right_frames and left_frames:
                right_frames = [
                    pygame.transform.flip(surface, True, False)
                    for surface in left_frames
                ]

            if not left_frames or not right_frames:
                continue

            target_size = (spec.width, spec.height)
            frames[creature_name] = {
                "left": [
                    pygame.transform.smoothscale(surface, target_size)
                    for surface in left_frames
                ],
                "right": [
                    pygame.transform.smoothscale(surface, target_size)
                    for surface in right_frames
                ],
            }

        return frames

    def _load_animation_frames(self, path: Path) -> list[pygame.Surface]:
        if not path.exists():
            return []

        if (
            Image is not None
            and ImageSequence is not None
            and path.suffix.lower() == ".gif"
        ):
            try:
                frames: list[pygame.Surface] = []
                with Image.open(path) as image:
                    for frame in ImageSequence.Iterator(image):
                        rgba = frame.convert("RGBA")
                        surface = pygame.image.fromstring(
                            rgba.tobytes(), rgba.size, "RGBA"
                        ).convert_alpha()
                        frames.append(surface)
                if frames:
                    return frames
            except Exception:
                pass

        static_surface = self._load_surface(path)
        if static_surface is None:
            return []
        return [static_surface]

    @staticmethod
    def _load_surface(path: Path) -> pygame.Surface | None:
        if not path.exists():
            return None
        try:
            return pygame.image.load(str(path)).convert_alpha()
        except pygame.error:
            return None

    def _load_target_surface(self) -> pygame.Surface | None:
        candidates = [
            self.repo_root / "assets/images/targeti.png",
            self.repo_root / self.config.images["target"],
        ]

        image: pygame.Surface | None = None
        for path in candidates:
            image = self._load_surface(path)
            if image is not None:
                break

        if image is None:
            return None

        scaled = pygame.transform.smoothscale(image, (44, 44))

        white = scaled.copy()
        white.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)

        outline = white.copy()
        outline.fill((12, 12, 12, 255), special_flags=pygame.BLEND_RGBA_MULT)

        result = pygame.Surface((52, 52), pygame.SRCALPHA)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            result.blit(outline, (4 + dx, 4 + dy))
        result.blit(white, (4, 4))
        return result

    def _build_scanline_overlay(self) -> pygame.Surface:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for y in range(0, WINDOW_HEIGHT, 4):
            pygame.draw.line(overlay, (0, 0, 0, 28), (0, y), (WINDOW_WIDTH, y), 1)
        return overlay

    def _top_score_text(self) -> str:
        rows = self.session.menu.get_rankings_view(limit=1)
        if not rows:
            return "TOP SCORE: 0"
        top = rows[0]
        return f"TOP SCORE: {top.score} - {top.player_name}"

    def run(self) -> None:
        while self.running:
            dt_ms = self.clock.tick(FPS)
            dt = dt_ms / 1000.0

            self._handle_events()
            self._update(dt, dt_ms)
            self._render()

        pygame.mouse.set_visible(True)
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if event.type == pygame.KEYDOWN:
                self._on_keydown(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == "menu":
                    self._on_menu_click(event.pos)
                elif self.state == "name_entry":
                    self._on_name_entry_click(event.pos)
                elif self.state == "map_selector":
                    self._on_map_selector_click(event.pos)
                elif self.state == "instructions":
                    self._on_instructions_click(event.pos)
                elif self.state == "rankings":
                    self._on_rankings_click(event.pos)
                elif self.state == "playing":
                    self._shoot_at(event.pos)
                elif self.state == "game_over":
                    self._go_to_menu()

    def _on_keydown(self, event: pygame.event.Event) -> None:
        if self.state == "menu":
            self._on_menu_keydown(event)
            return

        if self.state == "name_entry":
            self._on_name_entry_keydown(event)
            return

        if self.state == "map_selector":
            self._on_map_selector_keydown(event)
            return

        if self.state == "instructions":
            if event.key in {pygame.K_RETURN, pygame.K_ESCAPE}:
                self._go_to_menu()
            return

        if self.state == "playing":
            if event.key == pygame.K_ESCAPE:
                self._go_to_menu()
            return

        if self.state in {"rankings", "game_over"}:
            if event.key in {pygame.K_RETURN, pygame.K_ESCAPE}:
                self._go_to_menu()
            return

    def _on_menu_keydown(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            self.running = False
            return

        if event.key == pygame.K_UP:
            self.menu_selected_index = (self.menu_selected_index - 1) % len(
                self.menu_option_order
            )
            return

        if event.key == pygame.K_DOWN:
            self.menu_selected_index = (self.menu_selected_index + 1) % len(
                self.menu_option_order
            )
            return

        if event.key == pygame.K_TAB:
            self.menu_selected_index = (self.menu_selected_index + 1) % len(
                self.menu_option_order
            )
            return

        current_option = self.menu_option_order[self.menu_selected_index]
        if current_option == "seed" and event.key == pygame.K_LEFT:
            self.selected_seed_index = (self.selected_seed_index - 1) % len(
                self.seed_presets
            )
            return

        if current_option == "seed" and event.key == pygame.K_RIGHT:
            self.selected_seed_index = (self.selected_seed_index + 1) % len(
                self.seed_presets
            )
            return

        if event.key == pygame.K_RETURN:
            self._activate_menu_option(self.menu_option_order[self.menu_selected_index])

    def _activate_menu_option(self, option_id: str) -> None:
        if option_id == "play":
            self.state = "name_entry"
            self.last_message = "Ingresa tu nombre para comenzar"
            return

        if option_id == "instructions":
            self.state = "instructions"
            self.last_message = "Instrucciones"
            return

        if option_id == "rankings":
            self.state = "rankings"
            self.last_message = "Rankings"
            return

        if option_id == "seed":
            self.selected_seed_index = (self.selected_seed_index + 1) % len(
                self.seed_presets
            )
            self.last_message = ""
            return

    def _on_name_entry_keydown(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            self._go_to_menu()
            return

        if event.key == pygame.K_RETURN:
            self._start_game_with_name()
            return

        if event.key == pygame.K_BACKSPACE:
            self.player_name_input = self.player_name_input[:-1]
            return

        char = event.unicode
        if char and char.isprintable() and len(self.player_name_input) < 14:
            self.player_name_input += char

    def _on_name_entry_click(self, mouse_pos: tuple[int, int]) -> None:
        del mouse_pos

    def _on_map_selector_click(self, mouse_pos: tuple[int, int]) -> None:
        del mouse_pos

    def _on_instructions_click(self, mouse_pos: tuple[int, int]) -> None:
        if self.instructions_back_rect.collidepoint(mouse_pos):
            self._go_to_menu()

    def _on_rankings_click(self, mouse_pos: tuple[int, int]) -> None:
        if self.rankings_back_rect.collidepoint(mouse_pos):
            self._go_to_menu()

    def _on_map_selector_keydown(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            self.state = "name_entry"
            self.map_carousel_running = False
            return

        if self.map_carousel_running:
            if event.key == pygame.K_SPACE:
                self._start_map_roulette()
            return

        if event.key in {pygame.K_LEFT, pygame.K_UP}:
            self.selected_map_index = (self.selected_map_index - 1) % len(
                self.config.maps
            )
            self.map_carousel_position = float(self.selected_map_index)
            return

        if event.key in {pygame.K_RIGHT, pygame.K_DOWN, pygame.K_TAB}:
            self.selected_map_index = (self.selected_map_index + 1) % len(
                self.config.maps
            )
            self.map_carousel_position = float(self.selected_map_index)
            return

        if event.key == pygame.K_SPACE:
            self._start_map_roulette()
            return

        if event.key == pygame.K_RETURN:
            self._start_game_from_map_selector()

    def _on_menu_click(self, mouse_pos: tuple[int, int]) -> None:
        for idx, option_id in enumerate(self.menu_option_order):
            rect = self.menu_option_rects.get(option_id)
            if rect and rect.collidepoint(mouse_pos):
                self.menu_selected_index = idx
                self._activate_menu_option(option_id)
                return

    def _start_game_with_name(self) -> None:
        player_name = self.player_name_input.strip()
        if not player_name:
            self.last_message = "Escribe tu nombre"
            return

        _, seed_a_text, seed_b_text = self.seed_presets[self.selected_seed_index]
        try:
            seed_a = int(seed_a_text)
            seed_b = int(seed_b_text)
        except ValueError:
            self.last_message = "La semilla seleccionada es invalida"
            return

        self.pending_player_name = player_name
        self.pending_seed_a = seed_a
        self.pending_seed_b = seed_b

        self._enter_map_selector()

    def _enter_map_selector(self) -> None:
        self.state = "map_selector"
        self.map_carousel_running = False
        self.map_carousel_elapsed_ms = 0

        context = {
            "version": 1,
            "session_nonce": len(self.pending_player_name),
            "round": 0,
            "map_index": self.selected_map_index,
            "mode": 2,
        }
        self.map_selector_rng.set_seeds(self.pending_seed_a, self.pending_seed_b)
        self.map_selector_rng.derive_seed_c(context)
        self.selected_map_index = self.map_selector_rng.randint(
            0, len(self.config.maps) - 1
        )
        self.map_carousel_position = float(self.selected_map_index)
        self._start_map_roulette()
        self.last_message = ""

    def _start_map_roulette(self) -> None:
        total_maps = len(self.config.maps)
        if total_maps <= 0:
            self.map_carousel_running = False
            return

        self.map_carousel_target_index = self.map_selector_rng.randint(
            0, total_maps - 1
        )
        extra_loops = self.map_selector_rng.randint(3, 5)

        start_pos = self.map_carousel_position
        start_mod = start_pos % total_maps
        delta_to_target = (self.map_carousel_target_index - start_mod) % total_maps
        total_delta = (extra_loops * total_maps) + delta_to_target

        self.map_carousel_start_pos = start_pos
        self.map_carousel_end_pos = start_pos + total_delta
        self.map_carousel_elapsed_ms = 0
        self.map_carousel_duration_ms = self.map_selector_rng.randint(2400, 3400)
        self.map_carousel_running = True

    def _start_game_from_map_selector(self) -> None:
        context = {
            "version": 1,
            "session_nonce": len(self.pending_player_name),
            "round": 1,
            "map_index": self.selected_map_index,
            "mode": 1,
        }

        try:
            events = self.runtime.start(
                player_name=self.pending_player_name,
                seed_a=self.pending_seed_a,
                seed_b=self.pending_seed_b,
                context=context,
            )
        except Exception as exc:
            self.last_message = f"Cannot start game: {exc}"
            return

        self.state = "playing"
        self.current_creature = None
        self.banner_text = ""
        self.banner_timer = 0.0
        self.hit_flash = 0.0
        self.miss_flash = 0.0
        pygame.mouse.set_visible(False)
        self._process_runtime_events(events)

    def _process_runtime_events(self, events: list[object]) -> None:
        for event in events:
            event_type = getattr(event, "type", "")
            payload = getattr(event, "payload", {})

            if event_type == "session_started":
                map_name = payload.get("map_name", "Unknown")
                self.last_message = f"Hunt started at {map_name}"

            elif event_type == "creature_spawned":
                creature_type = str(payload.get("creature_type", "duck"))
                self._spawn_creature(creature_type)
                shots_left = self.session.game.shots_remaining
                self.last_message = f"Target: {creature_type} | Shots: {shots_left}"

            elif event_type == "action_resolved":
                action = payload.get("action")
                result = payload.get("result")
                if action == "hit":
                    points = int(payload.get("points", 0))
                    self.hit_flash = 0.12
                    self.last_message = f"Hit! +{points}"
                elif action == "miss":
                    self.miss_flash = 0.12
                    if result == "game_over":
                        self.last_message = "No shots left"
                    else:
                        shots_left = int(payload.get("shots_remaining", 0))
                        self.last_message = f"Miss! Shots left: {shots_left}"

            elif event_type == "round_completed":
                bonus = int(payload.get("round_bonus", 0))
                next_round = int(payload.get("next_round", 1))
                self.banner_text = f"Round clear! Bonus +{bonus} | Round {next_round}"
                self.banner_timer = 1.8

            elif event_type == "game_over":
                self.state = "game_over"
                self.current_creature = None
                self.banner_text = "GAME OVER"
                self.banner_timer = 3.0
                self.last_message = "Press ENTER to return to menu"
                pygame.mouse.set_visible(True)

    def _spawn_creature(self, creature_type: str) -> None:
        spec = self.config.creature_types.get(creature_type)
        if spec is None:
            spec = self.config.creature_types["duck"]
            creature_type = "duck"

        start_on_left = bool(self.session.rng.randint(0, 1))
        x = -float(spec.width) if start_on_left else float(WINDOW_WIDTH + spec.width)
        y = float(
            self.session.rng.randint(
                TOP_MARGIN + 10,
                WINDOW_HEIGHT - BOTTOM_MARGIN - spec.height,
            )
        )

        speed_factor = max(0.75, float(self.session.game.duck_speed) / 4.0)
        base_speed = (115.0 + (spec.base_speed * 25.0)) * speed_factor
        vx = base_speed if start_on_left else -base_speed
        vy = float(self.session.rng.randint(-85, 85))
        phase = self.session.rng.next_float() * math.tau

        self.current_creature = CreatureSprite(
            kind=creature_type,
            movement_type=spec.movement_type,
            width=spec.width,
            height=spec.height,
            x=x,
            y=y,
            vx=vx,
            vy=vy,
            phase=phase,
        )

    def _shoot_at(self, mouse_pos: tuple[int, int]) -> None:
        if self.current_creature is None:
            return

        hit = self.current_creature.rect().collidepoint(mouse_pos)
        action = "hit" if hit else "miss"

        try:
            events = self.runtime.perform_action(action)
        except Exception as exc:
            self.last_message = f"Action error: {exc}"
            return

        if not hit and self.current_creature is not None:
            # Keep moving target if the creature survives the miss.
            if self.session.game.creature_active:
                self.current_creature.vy *= 1.08

        self._process_runtime_events(events)

    def _go_to_menu(self, message: str | None = None) -> None:
        self.state = "menu"
        self.current_creature = None
        self.banner_text = ""
        self.banner_timer = 0.0
        self.last_message = message or ""
        pygame.mouse.set_visible(True)

        if self.session.game.game_active:
            self.session.stop_game_and_return_to_menu()

    def _update(self, dt: float, dt_ms: int) -> None:
        self.menu_pulse += dt

        if self.state == "map_selector" and self.map_carousel_running:
            self.map_carousel_elapsed_ms += dt_ms

            progress = min(
                1.0, self.map_carousel_elapsed_ms / self.map_carousel_duration_ms
            )
            eased = 1.0 - ((1.0 - progress) ** 3)
            self.map_carousel_position = self.map_carousel_start_pos + (
                (self.map_carousel_end_pos - self.map_carousel_start_pos) * eased
            )

            if progress >= 1.0:
                self.map_carousel_running = False
                self.selected_map_index = self.map_carousel_target_index
                self.map_carousel_position = float(self.selected_map_index)

        if self.banner_timer > 0.0:
            self.banner_timer = max(0.0, self.banner_timer - dt)

        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        if self.miss_flash > 0.0:
            self.miss_flash = max(0.0, self.miss_flash - dt)

        if self.state != "playing":
            return

        self.runtime.advance_time(dt_ms)

        if self.current_creature is not None and self.session.game.creature_active:
            self.current_creature.update(dt, WINDOW_WIDTH, WINDOW_HEIGHT)

    def _render(self) -> None:
        if self.state == "menu":
            self._draw_menu()
        elif self.state == "name_entry":
            self._draw_name_entry()
        elif self.state == "map_selector":
            self._draw_map_selector()
        elif self.state == "instructions":
            self._draw_instructions()
        elif self.state == "rankings":
            self._draw_rankings()
        elif self.state == "playing":
            self._draw_playing()
        else:
            self._draw_game_over()

        pygame.display.flip()

    def _draw_menu(self) -> None:
        self.menu_option_rects = {}

        if self.menu_background is not None:
            self.screen.blit(self.menu_background, (0, 0))
            veil = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            veil.fill((12, 5, 8, 146))
            self.screen.blit(veil, (0, 0))
        else:
            self.screen.fill((12, 20, 30))

        for idx, layer in enumerate(self.menu_blood_layers):
            alpha = 92 if idx == 0 else 78
            blood = pygame.transform.smoothscale(
                layer, (330 + idx * 120, 250 + idx * 80)
            )
            blood.set_alpha(alpha)
            self.screen.blit(blood, (40 + idx * 830, 6 + idx * 360))

        glow_alpha = int(70 + (math.sin(self.menu_pulse * 2.8) * 22))
        glow = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        glow.fill((220, 58, 45, max(0, glow_alpha)))
        self.screen.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self._draw_title_block("DUCK HUNT")

        self._draw_menu_options()

        top_score_surface = self.small_font.render(
            self._top_score_text(),
            True,
            (255, 223, 161),
        )
        self.screen.blit(
            top_score_surface,
            (WINDOW_WIDTH - top_score_surface.get_width() - 20, WINDOW_HEIGHT - 34),
        )
        self.screen.blit(self.scanline_overlay, (0, 0))

    def _draw_menu_options(self) -> None:
        options = [
            ("play", "Jugar", (WINDOW_WIDTH // 2, 248)),
            ("instructions", "Instrucciones", (WINDOW_WIDTH // 2, 300)),
            ("rankings", "Rankings", (WINDOW_WIDTH // 2, 352)),
            (
                "seed",
                f"Seleccionar generador: {self.seed_presets[self.selected_seed_index][0]}",
                (32, WINDOW_HEIGHT - 34),
            ),
        ]

        for index, (option_id, label, position) in enumerate(options):
            selected = self.menu_selected_index == index
            color = (255, 229, 167) if selected else (226, 213, 194)
            option_font = self.small_font if option_id == "seed" else self.body_font
            text = option_font.render(label, True, color)
            shadow = option_font.render(label, True, (36, 9, 8))

            if selected:
                scale = 1.24 if option_id == "seed" else 1.18
                text = pygame.transform.smoothscale(
                    text,
                    (
                        int(text.get_width() * scale),
                        int(text.get_height() * scale),
                    ),
                )
                shadow = pygame.transform.smoothscale(
                    shadow,
                    (
                        int(shadow.get_width() * scale),
                        int(shadow.get_height() * scale),
                    ),
                )

            if option_id == "seed":
                x, y = position
                self.screen.blit(shadow, (x + 2, y + 2))
                self.screen.blit(text, (x, y))
                rect = pygame.Rect(x, y, text.get_width(), text.get_height())
            else:
                center_x, y = position
                text_rect = text.get_rect(center=(center_x, y))
                shadow_rect = shadow.get_rect(center=(center_x + 2, y + 2))
                self.screen.blit(shadow, shadow_rect)
                self.screen.blit(text, text_rect)
                rect = text_rect

            self.menu_option_rects[option_id] = rect

    def _draw_dog_hunter_backdrop(self, variant: str) -> None:
        if self.menu_background is not None:
            self.screen.blit(self.menu_background, (0, 0))
            veil = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            veil.fill((10, 6, 9, 168))
            self.screen.blit(veil, (0, 0))
        else:
            self.screen.fill((13, 9, 12))

        for idx, layer in enumerate(self.menu_blood_layers):
            alpha = 86 if idx == 0 else 68
            blood = pygame.transform.smoothscale(
                layer, (300 + idx * 100, 220 + idx * 72)
            )
            blood.set_alpha(alpha)
            self.screen.blit(blood, (60 + idx * 848, 28 + idx * 356))

        if self.dog_hunter_surface is not None:
            dog_scale = (430, 335) if variant == "instructions" else (520, 400)
            dog = pygame.transform.smoothscale(self.dog_hunter_surface, dog_scale)
            dog = pygame.transform.flip(dog, True, False)
            dog_pos = (56, 302) if variant == "instructions" else (36, 268)
            dog_shadow = dog.copy()
            dog_shadow.fill((0, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(dog_shadow, (dog_pos[0] + 12, dog_pos[1] + 12))
            self.screen.blit(dog, dog_pos)

    def _draw_name_entry(self) -> None:
        if self.name_entry_illustration is not None:
            bg = pygame.transform.smoothscale(
                self.name_entry_illustration,
                (WINDOW_WIDTH, WINDOW_HEIGHT),
            )
            self.screen.blit(bg, (0, 0))
        else:
            self._draw_dog_hunter_backdrop(variant="name")

        player_text = self.player_name_input or "_"
        name_surface = self.hud_font.render(player_text, True, (236, 225, 204))
        name_shadow = self.hud_font.render(player_text, True, (18, 12, 10))
        name_rect = name_surface.get_rect(center=(640, 362))
        shadow_rect = name_shadow.get_rect(center=(642, 364))
        self.screen.blit(name_shadow, shadow_rect)
        self.screen.blit(name_surface, name_rect)

        hint = self.small_font.render(
            "ENTER para continuar | ESC para volver", True, (222, 223, 214)
        )
        self.screen.blit(hint, hint.get_rect(center=(640, 574)))
        self.screen.blit(self.scanline_overlay, (0, 0))

    def _draw_map_selector(self) -> None:
        map_count = len(self.config.maps)
        if map_count == 0:
            self.screen.fill((18, 10, 12))
            empty = self.body_font.render(
                "No hay mapas disponibles", True, (240, 219, 194)
            )
            self.screen.blit(
                empty, empty.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            )
            self.screen.blit(self.scanline_overlay, (0, 0))
            return

        center_map_index = int(round(self.map_carousel_position)) % map_count
        selected_map = self.config.maps[center_map_index]

        background = self.background_cache.get(selected_map.name)
        if background is not None:
            self.screen.blit(background, (0, 0))
        else:
            self._draw_fallback_background(selected_map.name)

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 6, 10, 168))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("SELECCION DE MAPA", True, (245, 214, 146))
        title_shadow = self.title_font.render("SELECCION DE MAPA", True, (35, 11, 9))
        self.screen.blit(title_shadow, title_shadow.get_rect(center=(642, 98)))
        self.screen.blit(title, title.get_rect(center=(640, 96)))

        center_x = WINDOW_WIDTH // 2
        center_y = 350
        spacing = 290
        base_index = int(math.floor(self.map_carousel_position))
        frac = self.map_carousel_position - base_index

        for slot in range(-4, 5):
            virtual_index = base_index + slot
            map_idx = virtual_index % map_count
            rel = slot - frac
            dist = abs(rel)
            if dist > 4.6:
                continue

            scale = max(0.54, 1.0 - (dist * 0.16))
            if dist < 0.35:
                scale += 0.16 * (1.0 - (dist / 0.35))

            alpha = max(65, 255 - int(dist * 95))
            x = int(center_x + (rel * spacing))

            card_base = self.map_preview_cache.get(map_idx)
            if card_base is None:
                continue

            card_w = max(90, int(card_base.get_width() * scale))
            card_h = max(60, int(card_base.get_height() * scale))
            card = pygame.transform.smoothscale(
                card_base, (card_w, card_h)
            ).convert_alpha()
            card.set_alpha(alpha)
            card_rect = card.get_rect(center=(x, center_y))

            if card_rect.right < -40 or card_rect.left > WINDOW_WIDTH + 40:
                continue

            self.screen.blit(card, card_rect)

            border_color = (255, 219, 150) if dist < 0.5 else (152, 70, 60)
            border_width = 3 if dist < 0.5 else 1
            pygame.draw.rect(
                self.screen, border_color, card_rect, border_width, border_radius=10
            )

        arrow = [
            (center_x, 190),
            (center_x - 18, 158),
            (center_x + 18, 158),
        ]
        pygame.draw.polygon(self.screen, (255, 220, 149), arrow)
        pygame.draw.polygon(self.screen, (86, 31, 28), arrow, 2)

        map_surface = self.body_font.render(selected_map.name, True, (255, 231, 188))
        self.screen.blit(map_surface, map_surface.get_rect(center=(640, 515)))

        hint = self.small_font.render(
            "ENTER confirmar | ESPACIO relanzar | FLECHAS ajustar | ESC volver",
            True,
            (224, 224, 214),
        )
        self.screen.blit(hint, hint.get_rect(center=(640, 548)))

        self.screen.blit(self.scanline_overlay, (0, 0))

    def _draw_instructions(self) -> None:
        self._draw_dog_hunter_backdrop(variant="instructions")

        self._draw_title_block("INSTRUCCIONES")

        lines = [
            "1. Dispara con click izquierdo.",
            "2. Cada objetivo tiene 3 disparos maximo.",
            "3. Si se acaban los disparos, termina la partida.",
            "4. selecciona tu generador aleatorio favorito.",
        ]
        base_y = 236
        for index, line in enumerate(lines):
            txt = self.body_font.render(line, True, (236, 228, 205))
            self.screen.blit(txt, txt.get_rect(center=(850, base_y + index * 42)))

        back = self.small_font.render("Regresar", True, (255, 198, 174))
        self.instructions_back_rect = back.get_rect(center=(852, 472))
        self.screen.blit(back, self.instructions_back_rect)

        self.screen.blit(self.scanline_overlay, (0, 0))

    def _draw_rankings(self) -> None:
        if self.menu_background is not None:
            self.screen.blit(self.menu_background, (0, 0))
            veil = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            veil.fill((12, 5, 8, 156))
            self.screen.blit(veil, (0, 0))
        else:
            self.screen.fill((9, 16, 28))

        for idx, layer in enumerate(self.menu_blood_layers):
            alpha = 75 if idx == 0 else 62
            blood = pygame.transform.smoothscale(
                layer, (290 + idx * 90, 220 + idx * 60)
            )
            blood.set_alpha(alpha)
            self.screen.blit(blood, (72 + idx * 860, 36 + idx * 334))

        self._draw_title_block("RANKINGS")

        rows = self.session.menu.get_rankings_view(limit=10)
        panel = pygame.Rect(130, 176, 1020, 470)
        pygame.draw.rect(self.screen, (20, 10, 12), panel, border_radius=12)
        pygame.draw.rect(self.screen, (178, 70, 60), panel, 3, border_radius=12)

        col_x = {
            "pos": 182,
            "name": 260,
            "pts": 520,
            "round": 630,
            "map": 742,
        }

        header_style = (255, 226, 176)
        self.screen.blit(
            self.small_font.render("POS", True, header_style), (col_x["pos"], 206)
        )
        self.screen.blit(
            self.small_font.render("NOMBRE", True, header_style), (col_x["name"], 206)
        )
        self.screen.blit(
            self.small_font.render("PTS", True, header_style), (col_x["pts"], 206)
        )
        self.screen.blit(
            self.small_font.render("RONDA", True, header_style), (col_x["round"], 206)
        )
        self.screen.blit(
            self.small_font.render("MAPA", True, header_style), (col_x["map"], 206)
        )

        if not rows:
            empty = self.body_font.render("Aun no hay puntajes", True, (239, 224, 209))
            self.screen.blit(empty, (190, 258))
        else:
            for idx, row in enumerate(rows):
                y = 246 + (idx * 36)
                row_style = (239, 224, 209)
                self.screen.blit(
                    self.body_font.render(str(row.rank), True, row_style),
                    (col_x["pos"], y),
                )
                self.screen.blit(
                    self.body_font.render(row.player_name, True, row_style),
                    (col_x["name"], y),
                )
                self.screen.blit(
                    self.body_font.render(str(row.score), True, row_style),
                    (col_x["pts"], y),
                )
                self.screen.blit(
                    self.body_font.render(f"R{row.round}", True, row_style),
                    (col_x["round"], y),
                )
                self.screen.blit(
                    self.body_font.render(row.map_name, True, row_style),
                    (col_x["map"], y),
                )

        hint = self.small_font.render("Regresar", True, (255, 207, 182))
        self.rankings_back_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, 612))
        self.screen.blit(hint, self.rankings_back_rect)
        self.screen.blit(self.scanline_overlay, (0, 0))

    def _draw_playing(self) -> None:
        self._draw_map_background()
        self._draw_hud()

        if self.current_creature is not None:
            self._draw_creature(self.current_creature)

        if self.banner_timer > 0.0 and self.banner_text:
            banner = self.body_font.render(self.banner_text, True, (255, 219, 122))
            banner_bg = pygame.Rect(
                0, 0, banner.get_width() + 22, banner.get_height() + 12
            )
            banner_bg.center = (WINDOW_WIDTH // 2, 98)
            pygame.draw.rect(self.screen, (17, 10, 6), banner_bg, border_radius=8)
            pygame.draw.rect(self.screen, (252, 178, 53), banner_bg, 2, border_radius=8)
            self.screen.blit(banner, (banner_bg.x + 11, banner_bg.y + 6))

        if self.hit_flash > 0.0:
            flash = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            flash.fill((160, 255, 160, int(85 * (self.hit_flash / 0.12))))
            self.screen.blit(flash, (0, 0))

        if self.miss_flash > 0.0:
            flash = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 115, 115, int(95 * (self.miss_flash / 0.12))))
            self.screen.blit(flash, (0, 0))

        self.screen.blit(self.scanline_overlay, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        self._draw_crosshair(mouse_pos)

    def _draw_game_over(self) -> None:
        self._draw_map_background()
        self._draw_hud()

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("GAME OVER", True, (255, 138, 120))
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 132))

        status = self.runtime.status()
        score_line = self.body_font.render(
            f"Score: {status['score']} | Round: {status['round']}",
            True,
            (246, 236, 210),
        )
        self.screen.blit(
            score_line, (WINDOW_WIDTH // 2 - score_line.get_width() // 2, 220)
        )

        rows = self.session.menu.get_rankings_view(limit=5)
        top_label = self.body_font.render("Top Rankings", True, (255, 223, 144))
        self.screen.blit(
            top_label, (WINDOW_WIDTH // 2 - top_label.get_width() // 2, 286)
        )

        for idx, row in enumerate(rows):
            line = f"{row.rank}. {row.player_name} - {row.score}"
            surf = self.small_font.render(line, True, (223, 237, 255))
            self.screen.blit(
                surf, (WINDOW_WIDTH // 2 - surf.get_width() // 2, 328 + (idx * 28))
            )

        hint = self.small_font.render(
            "ENTER or ESC to return to menu", True, (224, 224, 224)
        )
        self.screen.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, 540))
        self.screen.blit(self.scanline_overlay, (0, 0))

    def _draw_map_background(self) -> None:
        map_name = str(self.runtime.status().get("current_map", "---"))
        bg = self.background_cache.get(map_name)
        if bg is not None:
            self.screen.blit(bg, (0, 0))
        else:
            self._draw_fallback_background(map_name)

    def _draw_fallback_background(self, map_name: str) -> None:
        palette = {
            "DEATH VALLEY": ((81, 120, 180), (38, 63, 123), (30, 85, 35)),
            "PLAGUE": ((86, 109, 69), (42, 70, 33), (40, 66, 30)),
            "DANGER ZONE": ((120, 84, 72), (72, 42, 35), (63, 78, 31)),
            "HAUNTED CASTLE": ((67, 79, 127), (28, 34, 67), (35, 55, 25)),
            "WITCH HOUSE": ((55, 78, 118), (21, 36, 74), (29, 65, 34)),
            "GATE TO HELL": ((135, 68, 49), (82, 31, 23), (58, 45, 20)),
            "HELL": ((159, 55, 52), (102, 20, 24), (67, 23, 18)),
        }
        sky, horizon, ground = palette.get(
            map_name, ((74, 110, 165), (33, 61, 118), (41, 90, 38))
        )
        self.screen.fill(sky)
        pygame.draw.rect(self.screen, horizon, pygame.Rect(0, 360, WINDOW_WIDTH, 170))
        pygame.draw.rect(self.screen, ground, pygame.Rect(0, 520, WINDOW_WIDTH, 200))

    def _draw_hud(self) -> None:
        status = self.runtime.status()

        top_bar = pygame.Rect(0, 0, WINDOW_WIDTH, 58)
        pygame.draw.rect(self.screen, (8, 11, 16), top_bar)
        pygame.draw.line(self.screen, (190, 153, 81), (0, 58), (WINDOW_WIDTH, 58), 2)

        score_line = (
            f"Player: {status['player_name'] or 'Player'}    "
            f"Round: {status['round']}    "
            f"Score: {status['score']}    "
            f"Shots: {status['shots_remaining']}"
        )
        score_surface = self.hud_font.render(score_line, True, (234, 228, 212))
        self.screen.blit(score_surface, (18, 14))

        map_surface = self.small_font.render(
            f"Map: {status['current_map']}", True, (231, 199, 128)
        )
        self.screen.blit(map_surface, (WINDOW_WIDTH - map_surface.get_width() - 20, 20))

        bottom_bar = pygame.Rect(0, WINDOW_HEIGHT - 46, WINDOW_WIDTH, 46)
        pygame.draw.rect(self.screen, (11, 15, 20), bottom_bar)
        pygame.draw.line(
            self.screen,
            (106, 141, 164),
            (0, WINDOW_HEIGHT - 46),
            (WINDOW_WIDTH, WINDOW_HEIGHT - 46),
            1,
        )

        controls = "LMB: Shoot    ESC: Back to menu"
        controls_surface = self.small_font.render(controls, True, (173, 204, 230))
        self.screen.blit(controls_surface, (18, WINDOW_HEIGHT - 34))

        msg_surface = self.small_font.render(self.last_message, True, (255, 231, 153))
        self.screen.blit(
            msg_surface,
            (WINDOW_WIDTH - msg_surface.get_width() - 18, WINDOW_HEIGHT - 34),
        )

    def _draw_creature(self, creature: CreatureSprite) -> None:
        rect = creature.rect()
        sprite_set = self.creature_frames.get(creature.kind)
        if sprite_set:
            direction = "right" if creature.vx >= 0 else "left"
            sprite_frames = sprite_set.get(direction, [])
            if sprite_frames:
                frame_index = int((creature.age * 11.0) % len(sprite_frames))
                sprite = sprite_frames[frame_index]
                bob = int(math.sin((creature.age * 12.0) + creature.phase) * 4)
                sprite_rect = sprite.get_rect(center=(rect.centerx, rect.centery + bob))
                self.screen.blit(sprite, sprite_rect)
                return

        center = rect.center

        palettes = {
            "duck": ((96, 188, 86), (57, 117, 52), (251, 198, 83)),
            "seagull": ((226, 230, 239), (139, 147, 161), (251, 181, 67)),
            "bat": ((119, 90, 152), (56, 34, 83), (230, 95, 84)),
            "ghost": ((210, 218, 255), (131, 145, 198), (255, 115, 126)),
        }
        primary, outline, accent = palettes.get(creature.kind, palettes["duck"])

        wing_offset = int(math.sin((creature.age * 14.0) + creature.phase) * 9)

        body_rect = pygame.Rect(
            rect.x + 12, rect.y + 14, rect.width - 24, rect.height - 24
        )
        pygame.draw.ellipse(self.screen, primary, body_rect)
        pygame.draw.ellipse(self.screen, outline, body_rect, 3)

        left_wing = [
            (center[0] - 12, center[1] - 6),
            (rect.x - 16, center[1] - 18 + wing_offset),
            (rect.x + 18, center[1] + 8),
        ]
        right_wing = [
            (center[0] + 12, center[1] - 6),
            (rect.right + 16, center[1] - 18 - wing_offset),
            (rect.right - 18, center[1] + 8),
        ]
        pygame.draw.polygon(self.screen, primary, left_wing)
        pygame.draw.polygon(self.screen, primary, right_wing)
        pygame.draw.polygon(self.screen, outline, left_wing, 2)
        pygame.draw.polygon(self.screen, outline, right_wing, 2)

        beak = [
            (rect.right - 8, center[1] - 5),
            (rect.right + 14, center[1]),
            (rect.right - 8, center[1] + 7),
        ]
        pygame.draw.polygon(self.screen, accent, beak)

        eye_center = (rect.right - 26, rect.y + 28)
        pygame.draw.circle(self.screen, (255, 255, 255), eye_center, 7)
        pygame.draw.circle(self.screen, (18, 19, 22), eye_center, 3)

    def _draw_crosshair(self, mouse_pos: tuple[int, int]) -> None:
        x, y = mouse_pos
        if self.target_surface is not None:
            target_rect = self.target_surface.get_rect(center=(x, y))
            self.screen.blit(self.target_surface, target_rect)
            return

        outline = (14, 14, 14)
        color = (255, 255, 255)
        pygame.draw.circle(self.screen, outline, (x, y), 21, 3)
        pygame.draw.line(self.screen, outline, (x - 28, y), (x + 28, y), 4)
        pygame.draw.line(self.screen, outline, (x, y - 28), (x, y + 28), 4)
        pygame.draw.circle(self.screen, color, (x, y), 20, 2)
        pygame.draw.line(self.screen, color, (x - 28, y), (x + 28, y), 2)
        pygame.draw.line(self.screen, color, (x, y - 28), (x, y + 28), 2)

    def _draw_title_block(self, title: str) -> None:
        title_surface = self.title_font.render(title, True, (244, 209, 117))
        title_shadow = self.title_font.render(title, True, (45, 8, 6))
        center_x = WINDOW_WIDTH // 2
        y = 76
        self.screen.blit(
            title_shadow, title_shadow.get_rect(center=(center_x + 2, y + 2))
        )
        self.screen.blit(title_surface, title_surface.get_rect(center=(center_x, y)))


def main() -> None:
    app = DuckHuntTkApp()
    app.run()


if __name__ == "__main__":
    main()
