"""Pygame gameplay UI for Duck Hunt."""

from __future__ import annotations

import math
import sys
import time
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
    from .audio import AudioManager
    from .config import Config
    from .prng_lcg import LCG
    from .rng import RNG
    from .runtime import GameRuntime
    from .session import Session
    from .storage import Storage
    from .vision_control import HandVisionController
else:
    # Allow `python src/duck_hunt/ui_tk.py` by adding `src` to sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from duck_hunt.audio import AudioManager
    from duck_hunt.config import Config
    from duck_hunt.prng_lcg import LCG
    from duck_hunt.rng import RNG
    from duck_hunt.runtime import GameRuntime
    from duck_hunt.session import Session
    from duck_hunt.storage import Storage
    from duck_hunt.vision_control import HandVisionController


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
TOP_MARGIN = 72
BOTTOM_MARGIN = 132
INTRO_DURATION_SECONDS = 4.0


@dataclass
class BloodEffect:
    """Visual effect for hit impacts."""

    x: float
    y: float
    lifetime: float = 0.6  # seconds
    age: float = 0.0
    scale: float = 1.0
    rotation: float = 0.0


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
    entering_from_bottom: bool = False

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

        # Let creatures enter from below before applying normal vertical bounds.
        if self.entering_from_bottom:
            if self.y > max_y:
                return
            self.entering_from_bottom = False

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
        self.audio = AudioManager(self.repo_root)
        self.background_cache = self._load_background_cache()
        self.menu_background = self._load_menu_background()
        self.menu_blood_layers = self._load_menu_blood_layers()
        self.blood_effect_surfaces = self._load_blood_effects()
        self.dog_hunter_surface = self._load_dog_hunter_surface()
        self.dog_sad_surface = self._load_dog_sad_surface()
        self.intro_surface = self._load_intro_surface()
        self.name_entry_illustration = self._load_name_entry_illustration()
        self.map_preview_cache = self._build_map_preview_cache()
        self.creature_frames = self._load_creature_frames()
        self.boss_surfaces = self._load_boss_surfaces()
        self.target_surface = self._load_target_surface()
        self.scanline_overlay = self._build_scanline_overlay()
        self.audio_enabled = False
        self.sfx: dict[str, pygame.mixer.Sound] = {}
        self.music_path: Path | None = None
        self.music_started = False
        self._init_audio()
        self._ensure_music()

        self.title_font = self._load_font(54)
        self.hud_font = self._load_font(28)
        self.body_font = self._load_font(22)
        self.small_font = self._load_font(18)

        self.state = "intro"
        self.intro_timer = INTRO_DURATION_SECONDS
        self.last_message = "Selecciona una opcion"
        self.banner_text = ""
        self.banner_timer = 0.0

        self.current_creature: CreatureSprite | None = None
        self.hit_flash = 0.0
        self.miss_flash = 0.0
        self.blood_effects: list[BloodEffect] = []

        self.menu_pulse = 0.0

        self.menu_option_order = ["play", "instructions", "rankings", "game_mode"]
        self.menu_selected_index = 0
        self.menu_option_rects: dict[str, pygame.Rect] = {}

        self.game_mode_options = [
            ("classic", "Clasico"),
            ("futuristic", "Futurista"),
        ]
        self.selected_game_mode_index = 0
        self.active_game_mode_id = "classic"
        self.vision_controller = HandVisionController(
            WINDOW_WIDTH, WINDOW_HEIGHT, repo_root=self.repo_root
        )
        self.vision_cursor_pos = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        self.vision_status_message = ""
        self.futuristic_test_mode = True

        self.selected_seed_index = 0
        self.seed_presets = [
            ("Clasica", "123456789", "362436069"),
            ("Arcade", "42424242", "13371337"),
            ("Caos", "987654321", "123123123"),
            ("Infierno", "66666666", "314159265"),
        ]

        self.player_name_input = ""
        self.name_entry_text_center = (600, 435)
        self.name_entry_shadow_offset = (2, 2)
        self.name_entry_hint_center = (640, 574)
        self.name_confirm_rect = pygame.Rect(0, 0, 0, 0)
        self.name_back_rect = pygame.Rect(0, 0, 0, 0)
        self.instructions_back_rect = pygame.Rect(0, 0, 0, 0)
        self.rankings_back_rect = pygame.Rect(0, 0, 0, 0)
        self.rankings_tab_rects: list[pygame.Rect] = []
        self.rankings_filter_mode: str | None = None  # None = all
        self.game_over_play_rect = pygame.Rect(0, 0, 0, 0)
        self.game_over_exit_rect = pygame.Rect(0, 0, 0, 0)
        self.game_over_selected_index: int = 0  # 0=play again, 1=exit
        self.hud_creature_kind: str = "duck"
        self.is_fullscreen: bool = False
        # Boss / assassin animation
        self.boss_anim_state: str = "idle"  # idle | rising | holding | falling
        self.boss_anim_timer: float = 0.0
        self.boss_anim_y: float = 0.0
        self.boss_anim_kind: str = "duck"
        self.total_kills: int = 0
        self.pending_spawn_type: str | None = None  # deferred while boss is active

        # Extra (bonus) creatures for multi-creature rounds
        self.extra_creatures: list[CreatureSprite] = []

        # Score popups: list of {text, x, y, timer, max_timer}
        self.score_popups: list[dict] = []

        self.pending_player_name = ""
        self.pending_seed_a = 0
        self.pending_seed_b = 0
        self.selected_map_index = 0
        self.map_selector_rng = RNG()
        # Initialize LCG PRNG with seed based on current time (microseconds)
        # This ensures different random sequences on each run while maintaining
        # the ability to control randomness through the game's RNG system
        time_seed = int(time.time() * 1000000) % (2**32)
        self.map_selector_lcg = LCG(time_seed)
        self.map_carousel_running = False
        self.map_carousel_position = 0.0
        self.map_carousel_start_pos = 0.0
        self.map_carousel_end_pos = 0.0
        self.map_carousel_target_index = 0
        self.map_carousel_elapsed_ms = 0
        self.map_carousel_duration_ms = 0
        self.map_selector_phase = "idle"
        self.map_selector_phase_elapsed_ms = 0
        self.map_selector_hold_ms = 1700
        self.map_selector_started_game = False

        # Start background music from the presentation screen.
        self._ensure_music()
        self.audio.play_music()

    def _init_audio(self) -> None:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except pygame.error:
            self.audio_enabled = False
            return

        self.audio_enabled = True

        soundtrack_rel = self.config.sounds.get("soundtrack")
        if isinstance(soundtrack_rel, str):
            music_candidate = self.repo_root / soundtrack_rel
            if music_candidate.exists():
                self.music_path = music_candidate

        for key, rel_path in self.config.sounds.items():
            if key == "soundtrack":
                continue
            if not isinstance(rel_path, str):
                continue

            sound_path = self.repo_root / rel_path
            if not sound_path.exists():
                continue

            try:
                self.sfx[key] = pygame.mixer.Sound(str(sound_path))
            except pygame.error:
                continue

    def _play_sfx(self, key: str) -> bool:
        if not self.audio_enabled:
            return False

        sound = self.sfx.get(key)
        if sound is None:
            return False

        try:
            sound.play()
            return True
        except pygame.error:
            return False

    def _ensure_music(self) -> None:
        if not self.audio_enabled:
            return
        if self.music_path is None:
            return

        try:
            if not self.music_started:
                pygame.mixer.music.load(str(self.music_path))
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
                self.music_started = True
                return

            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)
        except pygame.error:
            self.music_started = False
            return

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
        bg_path = self.repo_root / "assets/images/backgrounds/bg-menu.jpg"
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
            self.repo_root / "assets/images/effects/blood.png",
            self.repo_root / "assets/images/effects/blood2.png",
        ]:
            surface = self._load_surface(path)
            if surface is None:
                continue
            layers.append(surface)
        return layers

    def _load_blood_effects(self) -> list[pygame.Surface]:
        """Load blood effect images for gameplay impacts."""
        effects: list[pygame.Surface] = []
        for path in [
            self.repo_root / "assets/images/effects/blood.png",
            self.repo_root / "assets/images/effects/blood2.png",
        ]:
            surface = self._load_surface(path)
            if surface is None:
                continue
            # Scale down for gameplay effects
            scaled = pygame.transform.smoothscale(surface, (80, 80))
            effects.append(scaled)
        return effects

    def _load_dog_hunter_surface(self) -> pygame.Surface | None:
        candidates = [
            self.repo_root / "assets/images/creatures/dog-duck1.png",
            self.repo_root / "assets/images/creatures/dog-duck2.png",
        ]
        for path in candidates:
            surface = self._load_surface(path)
            if surface is not None:
                return surface
        return None

    def _load_dog_sad_surface(self) -> pygame.Surface | None:
        """Load the sad dog image for game over screen."""
        candidates = [
            self.repo_root / self.config.images.get("dog_sad"),
            self.repo_root / "assets/images/creatures/dog-duck2.png",
        ]
        for path in candidates:
            if path and path.exists():
                surface = self._load_surface(path)
                if surface is not None:
                    return surface
        return None

    def _load_name_entry_illustration(self) -> pygame.Surface | None:
        candidates = [
            self.repo_root / "assets/images/ui/name_screeen.jpeg",
            self.repo_root / "assets/images/ui/ilustracion.png",
        ]
        for path in candidates:
            image = self._load_surface(path)
            if image is not None:
                return image
        return None

    def _load_intro_surface(self) -> pygame.Surface | None:
        path = self.repo_root / "assets/images/ui/intro.png"
        image = self._load_surface(path)
        if image is None:
            return None
        return pygame.transform.smoothscale(image, (WINDOW_WIDTH, WINDOW_HEIGHT))

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
        base_dir = self.repo_root / "assets/images/creatures"

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

    def _load_boss_surfaces(self) -> dict[str, pygame.Surface]:
        """Load assassin/boss images for each creature type."""
        result: dict[str, pygame.Surface] = {}
        for kind, rel_path in self.config.creature_boss_images.items():
            surface = self._load_surface(self.repo_root / rel_path)
            if surface is not None:
                result[kind] = surface
        return result

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
            self.repo_root / "assets/images/cursors/targeti.png",
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
                    allow_mouse_shot = self.active_game_mode_id == "classic"
                    if allow_mouse_shot:
                        self._shoot_at(event.pos)
                elif self.state == "game_over":
                    if self.game_over_play_rect.collidepoint(event.pos):
                        self._play_again()
                    elif self.game_over_exit_rect.collidepoint(event.pos):
                        self._go_to_menu()

    def _on_keydown(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_F11:
            self._toggle_fullscreen()
            return

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

        if self.state == "rankings":
            if event.key in {pygame.K_RETURN, pygame.K_ESCAPE}:
                self._go_to_menu()
            elif event.key in {pygame.K_LEFT}:
                # Cycle tabs backwards: None → futuristic → classic → None
                _tab_modes = [None, "classic", "futuristic"]
                cur = _tab_modes.index(self.rankings_filter_mode)
                self.rankings_filter_mode = _tab_modes[(cur - 1) % len(_tab_modes)]
            elif event.key in {pygame.K_RIGHT, pygame.K_TAB}:
                _tab_modes = [None, "classic", "futuristic"]
                cur = _tab_modes.index(self.rankings_filter_mode)
                self.rankings_filter_mode = _tab_modes[(cur + 1) % len(_tab_modes)]
            return

        if self.state == "game_over":
            if event.key in {pygame.K_LEFT, pygame.K_UP}:
                self.game_over_selected_index = 0
            elif event.key in {pygame.K_RIGHT, pygame.K_DOWN}:
                self.game_over_selected_index = 1
            elif event.key == pygame.K_RETURN:
                if self.game_over_selected_index == 0:
                    self._play_again()
                else:
                    self._go_to_menu()
            elif event.key == pygame.K_ESCAPE:
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
        if current_option == "game_mode" and event.key == pygame.K_LEFT:
            self._cycle_game_mode(step=-1)
            return

        if current_option == "game_mode" and event.key == pygame.K_RIGHT:
            self._cycle_game_mode(step=1)
            return

        if event.key == pygame.K_RETURN:
            self._activate_menu_option(self.menu_option_order[self.menu_selected_index])

    def _cycle_game_mode(self, step: int) -> None:
        self.selected_game_mode_index = (self.selected_game_mode_index + step) % len(
            self.game_mode_options
        )
        _, mode_label = self.game_mode_options[self.selected_game_mode_index]
        self.last_message = f"Modo seleccionado: {mode_label}"

    def _activate_menu_option(self, option_id: str) -> None:
        if option_id == "play":
            self.active_game_mode_id = self.game_mode_options[
                self.selected_game_mode_index
            ][0]
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

        if option_id == "game_mode":
            self._cycle_game_mode(step=1)
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
        return

    def _on_instructions_click(self, mouse_pos: tuple[int, int]) -> None:
        if self.instructions_back_rect.collidepoint(mouse_pos):
            self._go_to_menu()

    def _on_rankings_click(self, mouse_pos: tuple[int, int]) -> None:
        if self.rankings_back_rect.collidepoint(mouse_pos):
            self.state = "menu"
            return
        for idx, rect in enumerate(self.rankings_tab_rects):
            if rect.collidepoint(mouse_pos):
                # Tabs: 0=Todos, 1=Clásico, 2=Futurista
                self.rankings_filter_mode = (None, "classic", "futuristic")[idx]
                return

    def _on_map_selector_keydown(self, event: pygame.event.Event) -> None:
        del event
        return

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
        self.map_selector_phase = "spinning"
        self.map_selector_phase_elapsed_ms = 0
        self.map_selector_started_game = False

        context = {
            "version": 1,
            "session_nonce": len(self.pending_player_name),
            "round": 0,
            "map_index": self.selected_map_index,
            "mode": 2,
        }
        self.map_selector_rng.set_seeds(self.pending_seed_a, self.pending_seed_b)
        self.map_selector_rng.derive_seed_c(context)
        # Use LCG PRNG for truly random map selection
        self.selected_map_index = self.map_selector_lcg.randint(
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

        # Use LCG PRNG for roulette animation variation
        self.map_carousel_target_index = self.map_selector_lcg.randint(
            0, total_maps - 1
        )
        extra_loops = self.map_selector_lcg.randint(3, 5)

        start_pos = self.map_carousel_position
        start_mod = start_pos % total_maps
        delta_to_target = (self.map_carousel_target_index - start_mod) % total_maps
        total_delta = (extra_loops * total_maps) + delta_to_target

        self.map_carousel_start_pos = start_pos
        self.map_carousel_end_pos = start_pos + total_delta
        self.map_carousel_elapsed_ms = 0
        # Use LCG PRNG for timing variation
        self.map_carousel_duration_ms = self.map_selector_lcg.randint(4600, 6200)
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
            self.state = "name_entry"
            return

        # Set game mode on session so it gets saved with the ranking
        self.session.menu.current_game_mode = self.active_game_mode_id
        self.total_kills = 0
        self.boss_anim_state = "idle"
        self.pending_spawn_type = None
        self.extra_creatures = []
        self.score_popups = []

        self.state = "playing"
        if self.active_game_mode_id == "futuristic":
            self.vision_cursor_pos = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
            try:
                started = self.vision_controller.start()
            except Exception:
                started = False
            if not started:
                # Auto-fallback: no camera detected, switch to classic
                self.active_game_mode_id = "classic"
                self.session.menu.current_game_mode = "classic"
                self.last_message = "No se detecto camara; cambiado a Clasico"
                self.vision_controller.stop()
            self.vision_status_message = self.vision_controller.status
        else:
            self.vision_controller.stop()
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
                if self.boss_anim_state != "idle":
                    # Boss is on screen — defer the spawn until it finishes
                    self.pending_spawn_type = creature_type
                else:
                    self._spawn_creature_set(creature_type)
                if creature_type in {"duck", "seagull", "zombie_duck"}:
                    self._play_sfx("duck_quack")
                else:
                    if not self._play_sfx("duck_flap"):
                        self._play_sfx("duck_quack")
                shots_left = self.session.game.shots_remaining
                self.last_message = f"Target: {creature_type} | Shots: {shots_left}"

            elif event_type == "action_resolved":
                action = payload.get("action")
                result = payload.get("result")
                if action == "hit":
                    points = int(payload.get("points", 0))
                    self.hit_flash = 0.12
                    self._play_sfx("dog_score")
                    self.last_message = f"Hit! +{points}"
                    self.audio.play_sound("score", 0.8)
                    # Score popup at creature position, then clear it immediately
                    if self.current_creature is not None:
                        cx = int(
                            self.current_creature.x + self.current_creature.width / 2
                        )
                        cy = int(self.current_creature.y)
                        self._add_score_popup(points, (cx, cy))
                    # Remove the killed main creature from view right away
                    self.current_creature = None
                    self.total_kills += 1
                    if self.total_kills % 3 == 0 and self.boss_anim_state == "idle":
                        self._start_boss_animation(self.hud_creature_kind)
                elif action == "miss":
                    self.miss_flash = 0.12
                    self.audio.play_sound("quack", 0.7)
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
                self.audio.play_sound("score", 0.9)

            elif event_type == "game_over":
                self.state = "game_over"
                self.game_over_selected_index = 0
                self.current_creature = None
                self.extra_creatures = []
                self.score_popups = []
                self.pending_spawn_type = None
                self.banner_text = "GAME OVER"
                self.banner_timer = 3.0
                self.last_message = ""
                self.vision_controller.stop()
                pygame.mouse.set_visible(True)

    def _spawn_creature(self, creature_type: str) -> None:
        spec = self.config.creature_types.get(creature_type)
        if spec is None:
            spec = self.config.creature_types["duck"]
            creature_type = "duck"

        # Pick spawn side: 50% bottom, 25% left, 25% right
        spawn_side = self.session.rng.randint(0, 3)  # 0,1 = bottom; 2 = left; 3 = right
        speed_factor = max(0.75, float(self.session.game.duck_speed) / 4.0)
        base_speed = (115.0 + (spec.base_speed * 25.0)) * speed_factor
        phase = self.session.rng.next_float() * math.tau

        if spawn_side <= 1:  # bottom
            move_right = bool(self.session.rng.randint(0, 1))
            x = float(self.session.rng.randint(42, WINDOW_WIDTH - spec.width - 42))
            y = float(WINDOW_HEIGHT + spec.height + self.session.rng.randint(20, 140))
            vx = base_speed if move_right else -base_speed
            vy = -float(self.session.rng.randint(150, 255)) * speed_factor
            entering_from_bottom = True
        elif spawn_side == 2:  # left
            x = float(-spec.width - 20)
            y = float(
                self.session.rng.randint(
                    TOP_MARGIN + 30, WINDOW_HEIGHT - BOTTOM_MARGIN - spec.height - 30
                )
            )
            vx = base_speed
            vy = float(self.session.rng.randint(-80, 80)) * speed_factor
            entering_from_bottom = False
        else:  # right
            x = float(WINDOW_WIDTH + 20)
            y = float(
                self.session.rng.randint(
                    TOP_MARGIN + 30, WINDOW_HEIGHT - BOTTOM_MARGIN - spec.height - 30
                )
            )
            vx = -base_speed
            vy = float(self.session.rng.randint(-80, 80)) * speed_factor
            entering_from_bottom = False

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
            entering_from_bottom=entering_from_bottom,
        )
        self.hud_creature_kind = creature_type

    def _spawn_creature_set(self, creature_type: str) -> None:
        """Spawn main creature + extras based on current round."""
        self.extra_creatures = []
        self._spawn_creature(creature_type)
        round_num = self.session.game.current_round
        extra_count = 0
        if round_num >= 10:
            extra_count = 2
        elif round_num >= 5:
            extra_count = 1
        for _ in range(extra_count):
            self._spawn_extra_creature(creature_type)

    def _spawn_extra_creature(self, creature_type: str) -> None:
        """Spawn a bonus creature (not tracked by game_state) into extra_creatures."""
        import random as _rnd

        spec = self.config.creature_types.get(creature_type)
        if spec is None:
            spec = self.config.creature_types["duck"]
            creature_type = "duck"
        speed_factor = max(0.75, float(self.session.game.duck_speed) / 4.0)
        base_speed = (115.0 + (spec.base_speed * 25.0)) * speed_factor
        phase = _rnd.random() * math.tau
        side = _rnd.randint(0, 3)
        if side <= 1:  # bottom
            move_right = bool(_rnd.randint(0, 1))
            x = float(_rnd.randint(42, WINDOW_WIDTH - spec.width - 42))
            y = float(WINDOW_HEIGHT + spec.height + _rnd.randint(20, 140))
            vx = base_speed if move_right else -base_speed
            vy = -float(_rnd.randint(150, 255)) * speed_factor
            entering_from_bottom = True
        elif side == 2:  # left
            x = float(-spec.width - 20)
            y = float(
                _rnd.randint(
                    TOP_MARGIN + 30, WINDOW_HEIGHT - BOTTOM_MARGIN - spec.height - 30
                )
            )
            vx = base_speed
            vy = float(_rnd.randint(-80, 80)) * speed_factor
            entering_from_bottom = False
        else:  # right
            x = float(WINDOW_WIDTH + 20)
            y = float(
                _rnd.randint(
                    TOP_MARGIN + 30, WINDOW_HEIGHT - BOTTOM_MARGIN - spec.height - 30
                )
            )
            vx = -base_speed
            vy = float(_rnd.randint(-80, 80)) * speed_factor
            entering_from_bottom = False
        self.extra_creatures.append(
            CreatureSprite(
                kind=creature_type,
                movement_type=spec.movement_type,
                width=spec.width,
                height=spec.height,
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                phase=phase,
                entering_from_bottom=entering_from_bottom,
            )
        )

    def _add_score_popup(self, points: int, pos: tuple[int, int]) -> None:
        """Queue a score popup that floats upward and fades."""
        self.score_popups.append(
            {
                "text": f"+{points}",
                "x": float(pos[0]),
                "y": float(pos[1]),
                "timer": 1.4,
                "max_timer": 1.4,
            }
        )

    def _spawn_blood_effect(self, x: float, y: float) -> None:
        """Create a blood effect at the given position."""
        if not self.blood_effect_surfaces:
            return
        effect = BloodEffect(x=x, y=y)
        self.blood_effects.append(effect)

    def _shoot_at(self, mouse_pos: tuple[int, int]) -> None:
        self._play_sfx("duck_shot")
        self.audio.play_sound("shoot", 0.85)

        # Check bonus (extra) creatures first — they award points without game_state shots
        for extra in list(self.extra_creatures):
            if extra.rect().collidepoint(mouse_pos):
                self.extra_creatures.remove(extra)
                self._spawn_blood_effect(float(mouse_pos[0]), float(mouse_pos[1]))
                bonus_pts = 75
                self.session.game.total_score += bonus_pts
                self._add_score_popup(bonus_pts, mouse_pos)
                self.hit_flash = 0.10
                self.total_kills += 1
                if self.total_kills % 3 == 0 and self.boss_anim_state == "idle":
                    self._start_boss_animation(self.hud_creature_kind)
                return

        if self.current_creature is None:
            return

        hit = self.current_creature.rect().collidepoint(mouse_pos)
        action = "hit" if hit else "miss"

        try:
            events = self.runtime.perform_action(action)
        except Exception as exc:
            self.last_message = f"Action error: {exc}"
            return

        # Create blood effect at hit location
        if hit:
            self._spawn_blood_effect(float(mouse_pos[0]), float(mouse_pos[1]))

        if not hit and self.current_creature is not None:
            # Keep moving target if the creature survives the miss.
            if self.session.game.creature_active:
                self.current_creature.vy *= 1.08

        self._process_runtime_events(events)

    def _play_again(self) -> None:
        """Restart from map selector keeping name and seeds."""
        self.state = "menu"  # brief reset to allow _enter_map_selector
        self.current_creature = None
        self.banner_text = ""
        self.blood_effects = []
        self.total_kills = 0
        self.boss_anim_state = "idle"
        self.pending_spawn_type = None
        self.extra_creatures = []
        self.score_popups = []
        self._enter_map_selector()

    def _start_boss_animation(self, creature_kind: str) -> None:
        """Trigger the boss/assassin pop-up animation from the bottom of the screen."""
        self.boss_anim_kind = creature_kind
        self.boss_anim_state = "rising"
        self.boss_anim_timer = 0.0
        self.boss_anim_y = float(WINDOW_HEIGHT + 20)
        # Clear any leftover creatures so nothing remains visible during boss sequence
        self.extra_creatures = []
        self.current_creature = None

    _BOSS_RISE_TARGET = WINDOW_HEIGHT - 390  # visible peek-y position (above HUD)
    _BOSS_RISE_SPEED = 480.0  # px/s going up
    _BOSS_HOLD_TIME = 1.3  # seconds on screen
    _BOSS_FALL_SPEED = 520.0  # px/s going down

    def _update_boss_animation(self, dt: float) -> None:
        if self.boss_anim_state == "rising":
            self.boss_anim_y -= self._BOSS_RISE_SPEED * dt
            if self.boss_anim_y <= self._BOSS_RISE_TARGET:
                self.boss_anim_y = float(self._BOSS_RISE_TARGET)
                self.boss_anim_state = "holding"
                self.boss_anim_timer = 0.0
        elif self.boss_anim_state == "holding":
            self.boss_anim_timer += dt
            if self.boss_anim_timer >= self._BOSS_HOLD_TIME:
                self.boss_anim_state = "falling"
        elif self.boss_anim_state == "falling":
            self.boss_anim_y += self._BOSS_FALL_SPEED * dt
            if self.boss_anim_y >= WINDOW_HEIGHT + 20:
                # Boss fully hidden — enter post-boss pause before re-spawning
                self.boss_anim_state = "post_delay"
                self.boss_anim_timer = 0.0
        elif self.boss_anim_state == "post_delay":
            self.boss_anim_timer += dt
            if self.boss_anim_timer >= 2.5:
                self.boss_anim_state = "idle"
                # Flush any creature spawn that was deferred while boss was active
                if self.pending_spawn_type is not None:
                    pending = self.pending_spawn_type
                    self.pending_spawn_type = None
                    self._spawn_creature_set(pending)

    def _toggle_fullscreen(self) -> None:
        self.is_fullscreen = not self.is_fullscreen
        flags = pygame.FULLSCREEN if self.is_fullscreen else 0
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)

    def _go_to_menu(self, message: str | None = None) -> None:
        self.state = "menu"
        self.current_creature = None
        self.banner_text = ""
        self.banner_timer = 0.0
        self.last_message = message or ""
        self.blood_effects = []
        self.vision_controller.stop()
        pygame.mouse.set_visible(True)
        # Keep music playing in menu
        if not self.audio.music_playing:
            self.audio.play_music()

        if self.session.game.game_active:
            self.session.stop_game_and_return_to_menu()

    def _update(self, dt: float, dt_ms: int) -> None:
        self.menu_pulse += dt
        self._ensure_music()

        if self.state == "intro":
            self.intro_timer = max(0.0, self.intro_timer - dt)
            if self.intro_timer <= 0.0:
                self.state = "menu"
            return

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
                self.map_selector_phase = "locked"
                self.map_selector_phase_elapsed_ms = 0

        if self.state == "map_selector" and self.map_selector_phase == "locked":
            self.map_selector_phase_elapsed_ms += dt_ms
            if (
                not self.map_selector_started_game
                and self.map_selector_phase_elapsed_ms >= self.map_selector_hold_ms
            ):
                self.map_selector_started_game = True
                self._start_game_from_map_selector()

        if self.banner_timer > 0.0:
            self.banner_timer = max(0.0, self.banner_timer - dt)

        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        if self.miss_flash > 0.0:
            self.miss_flash = max(0.0, self.miss_flash - dt)

        # Update blood effects
        updated_effects: list[BloodEffect] = []
        for effect in self.blood_effects:
            effect.age += dt
            if effect.age < effect.lifetime:
                updated_effects.append(effect)
        self.blood_effects = updated_effects

        if self.state == "playing" and self.active_game_mode_id == "futuristic":
            sample = self.vision_controller.update()
            self.vision_cursor_pos = sample.cursor_pos
            self.vision_status_message = sample.status
            if sample.shoot:
                self._shoot_at(self.vision_cursor_pos)

        # Boss animation update (runs in playing state)
        if self.state == "playing" and self.boss_anim_state != "idle":
            self._update_boss_animation(dt)

        if self.state != "playing":
            return

        self.runtime.advance_time(dt_ms)

        if self.current_creature is not None and self.session.game.creature_active:
            self.current_creature.update(dt, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Update extra (bonus) creatures and prune off-screen ones
        alive_extras = []
        for extra in self.extra_creatures:
            extra.update(dt, WINDOW_WIDTH, WINDOW_HEIGHT)
            cx, cy = extra.x, extra.y
            if (-300 < cx < WINDOW_WIDTH + 300) and (-300 < cy < WINDOW_HEIGHT + 300):
                alive_extras.append(extra)
        self.extra_creatures = alive_extras

        # Decay score popups
        updated_popups = []
        for popup in self.score_popups:
            popup["timer"] -= dt
            popup["y"] -= 38.0 * dt  # float upward
            if popup["timer"] > 0.0:
                updated_popups.append(popup)
        self.score_popups = updated_popups

    def _render(self) -> None:
        if self.state == "intro":
            self._draw_intro()
        elif self.state == "menu":
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

    def _draw_intro(self) -> None:
        if self.intro_surface is not None:
            self.screen.blit(self.intro_surface, (0, 0))
        else:
            self.screen.fill((8, 8, 12))
        self.screen.blit(self.scanline_overlay, (0, 0))

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
                "game_mode",
                "Modo de juego: "
                f"{self.game_mode_options[self.selected_game_mode_index][1]}",
                (32, WINDOW_HEIGHT - 34),
            ),
        ]

        for index, (option_id, label, position) in enumerate(options):
            selected = self.menu_selected_index == index
            color = (255, 229, 167) if selected else (226, 213, 194)
            option_font = (
                self.small_font if option_id == "game_mode" else self.body_font
            )
            text = option_font.render(label, True, color)
            shadow = option_font.render(label, True, (36, 9, 8))

            if selected:
                scale = 1.24 if option_id == "game_mode" else 1.18
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

            if option_id == "game_mode":
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
        text_center_x, text_center_y = self.name_entry_text_center
        shadow_offset_x, shadow_offset_y = self.name_entry_shadow_offset
        name_rect = name_surface.get_rect(center=(text_center_x, text_center_y))
        shadow_rect = name_shadow.get_rect(
            center=(text_center_x + shadow_offset_x, text_center_y + shadow_offset_y)
        )
        self.screen.blit(name_shadow, shadow_rect)
        self.screen.blit(name_surface, name_rect)

        hint = self.small_font.render(
            "ENTER para continuar | ESC para volver", True, (222, 223, 214)
        )
        self.screen.blit(hint, hint.get_rect(center=self.name_entry_hint_center))
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
        overlay.fill((6, 8, 12, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("RULETA DE ZONAS", True, (226, 214, 190))
        title_shadow = self.title_font.render("RULETA DE ZONAS", True, (23, 18, 16))
        self.screen.blit(title_shadow, title_shadow.get_rect(center=(642, 134)))
        self.screen.blit(title, title.get_rect(center=(640, 132)))

        center_x = WINDOW_WIDTH // 2
        center_y = 364
        spacing = 250
        base_index = int(math.floor(self.map_carousel_position))
        frac = self.map_carousel_position - base_index

        # Clip carousel rendering to avoid visual overflow without a visible frame.
        viewport = pygame.Rect(120, 212, 1040, 330)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(viewport)

        for slot in range(-4, 5):
            virtual_index = base_index + slot
            map_idx = virtual_index % map_count
            rel = slot - frac
            dist = abs(rel)
            if dist > 4.6:
                continue

            scale = max(0.52, 1.0 - (dist * 0.15))
            if dist < 0.35:
                scale += 0.14 * (1.0 - (dist / 0.35))

            alpha = max(58, 255 - int(dist * 92))
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

            border_color = (212, 58, 52) if dist < 0.5 else (96, 100, 112)
            border_width = 3 if dist < 0.5 else 1
            pygame.draw.rect(
                self.screen, border_color, card_rect, border_width, border_radius=10
            )

        self.screen.set_clip(previous_clip)

        arrow = [
            (center_x, 190),
            (center_x - 18, 158),
            (center_x + 18, 158),
        ]
        pygame.draw.polygon(self.screen, (216, 69, 61), arrow)
        pygame.draw.polygon(self.screen, (78, 22, 20), arrow, 2)

        map_surface = self.body_font.render(selected_map.name, True, (240, 225, 201))
        self.screen.blit(map_surface, map_surface.get_rect(center=(640, 544)))

        if self.map_selector_phase == "locked":
            flash = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            flash_alpha = max(0, 145 - int(self.map_selector_phase_elapsed_ms * 0.22))
            flash.fill((224, 48, 43, flash_alpha))
            self.screen.blit(flash, (0, 0))

            lock_msg = self.body_font.render("MAPA CONFIRMADO", True, (255, 195, 179))
            self.screen.blit(lock_msg, lock_msg.get_rect(center=(640, 602)))

        self.screen.blit(self.scanline_overlay, (0, 0))

    def _draw_instructions(self) -> None:
        self._draw_dog_hunter_backdrop(variant="instructions")

        self._draw_title_block("INSTRUCCIONES")

        lines = [
            "1. Dispara con click izquierdo.",
            "2. Cada objetivo tiene 3 disparos maximo.",
            "3. Si se acaban los disparos, termina la partida.",
            "4. Selecciona tu modo de juego favorito.",
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

        # Mode filter tabs
        tab_labels = [
            ("Todos", None),
            ("Clasico", "classic"),
            ("Futurista", "futuristic"),
        ]
        self.rankings_tab_rects = []
        tab_w, tab_h = 160, 32
        tab_y = 130
        tab_start_x = (
            WINDOW_WIDTH // 2
            - (len(tab_labels) * tab_w + (len(tab_labels) - 1) * 8) // 2
        )
        for t_idx, (label, mode) in enumerate(tab_labels):
            rect = pygame.Rect(tab_start_x + t_idx * (tab_w + 8), tab_y, tab_w, tab_h)
            self.rankings_tab_rects.append(rect)
            is_active = self.rankings_filter_mode == mode
            bg_col = (178, 70, 60) if is_active else (40, 20, 20)
            pygame.draw.rect(self.screen, bg_col, rect, border_radius=6)
            pygame.draw.rect(self.screen, (200, 120, 110), rect, 1, border_radius=6)
            lbl_surf = self.small_font.render(
                label, True, (255, 240, 220) if is_active else (180, 160, 155)
            )
            self.screen.blit(lbl_surf, lbl_surf.get_rect(center=rect.center))

        rows = self.session.menu.get_rankings_view(
            limit=10, game_mode=self.rankings_filter_mode
        )
        panel = pygame.Rect(130, 176, 1020, 470)
        pygame.draw.rect(self.screen, (20, 10, 12), panel, border_radius=12)
        pygame.draw.rect(self.screen, (178, 70, 60), panel, 3, border_radius=12)

        show_mode_col = self.rankings_filter_mode is None
        col_x = {
            "pos": 182,
            "name": 256,
            "pts": 490,
            "round": 598,
            "map": 706 if show_mode_col else 742,
            "modo": 904,
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
        if show_mode_col:
            self.screen.blit(
                self.small_font.render("MODO", True, header_style), (col_x["modo"], 206)
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
                if show_mode_col:
                    mode_label = {"classic": "CL", "futuristic": "FUT"}.get(
                        getattr(row, "game_mode", "classic"), "---"
                    )
                    self.screen.blit(
                        self.body_font.render(mode_label, True, row_style),
                        (col_x["modo"], y),
                    )

        hint = self.small_font.render("Regresar", True, (255, 207, 182))
        self.rankings_back_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, 656))
        self.screen.blit(hint, self.rankings_back_rect)
        self.screen.blit(self.scanline_overlay, (0, 0))

    def _draw_playing(self) -> None:
        self._draw_map_background()
        self._draw_hud()

        if self.current_creature is not None:
            self._draw_creature(self.current_creature)

        # Draw extra (bonus) creatures
        for extra in self.extra_creatures:
            self._draw_creature(extra)

        # Draw blood effects
        self._draw_blood_effects()

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

        # Score popups: float upward, white, fade out
        for popup in self.score_popups:
            ratio = popup["timer"] / popup["max_timer"]
            alpha = int(255 * min(1.0, ratio * 2))
            surf = self.hud_font.render(popup["text"], True, (255, 255, 255))
            surf.set_alpha(alpha)
            rx = int(popup["x"]) - surf.get_width() // 2
            ry = int(popup["y"]) - surf.get_height() // 2
            # Subtle shadow for readability
            shadow = self.hud_font.render(popup["text"], True, (30, 30, 30))
            shadow.set_alpha(alpha)
            self.screen.blit(shadow, (rx + 2, ry + 2))
            self.screen.blit(surf, (rx, ry))

        # Boss animation (drawn on top of scanline, below crosshair)
        # post_delay = boss already hidden, just waiting; don't draw
        if self.boss_anim_state not in ("idle", "post_delay"):
            self._draw_boss_animation()

        if self.active_game_mode_id == "futuristic":
            crosshair_pos = self.vision_cursor_pos
        else:
            crosshair_pos = pygame.mouse.get_pos()

        self._draw_crosshair(crosshair_pos)

    def _is_high_score(self) -> bool:
        """Check if current game score is a high score (top 5) for the active mode."""
        status = self.runtime.status()
        current_score = int(status.get("score", 0))

        rows = self.session.menu.get_rankings_view(
            limit=5, game_mode=self.active_game_mode_id
        )

        if not rows:
            return True

        lowest_top_score = rows[-1].score if rows else 0
        return current_score >= lowest_top_score

    def _draw_game_over(self) -> None:
        self._draw_map_background()
        self._draw_hud()

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        # Choose dog based on score: happy for high scores, sad for low scores
        is_high_score = self._is_high_score()
        dog_surface = self.dog_hunter_surface if is_high_score else self.dog_sad_surface

        # Draw the hunting dog (happy if high score, sad if not)
        if dog_surface is not None:
            dog_scale = (460, 350)
            dog = pygame.transform.smoothscale(dog_surface, dog_scale)
            dog = pygame.transform.flip(dog, True, False)
            dog_pos = (WINDOW_WIDTH - 490, 260)
            dog_shadow = dog.copy()
            dog_shadow.fill((0, 0, 0, 180), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(dog_shadow, (dog_pos[0] + 14, dog_pos[1] + 14))
            self.screen.blit(dog, dog_pos)

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

        # Show special message if high score
        if is_high_score:
            high_score_msg = self.body_font.render("HIGH SCORE!", True, (255, 215, 0))
            self.screen.blit(
                high_score_msg,
                (WINDOW_WIDTH // 2 - high_score_msg.get_width() // 2, 270),
            )

        rows = self.session.menu.get_rankings_view(
            limit=5, game_mode=self.active_game_mode_id
        )
        top_label = self.body_font.render("Top Rankings", True, (255, 223, 144))
        self.screen.blit(top_label, (60, 286))

        for idx, row in enumerate(rows):
            line = f"{row.rank}. {row.player_name} - {row.score}"
            surf = self.small_font.render(line, True, (223, 237, 255))
            self.screen.blit(surf, (60, 328 + (idx * 28)))

        # Buttons: Jugar otra vez / Salir — white style, keyboard selectable
        btn_y = 600
        btn_w, btn_h = 230, 46
        play_rect = pygame.Rect(WINDOW_WIDTH // 2 - btn_w - 16, btn_y, btn_w, btn_h)
        exit_rect = pygame.Rect(WINDOW_WIDTH // 2 + 16, btn_y, btn_w, btn_h)
        self.game_over_play_rect = play_rect
        self.game_over_exit_rect = exit_rect

        for i, (rect, label) in enumerate(
            [(play_rect, "Jugar otra vez"), (exit_rect, "Salir al menu")]
        ):
            selected = self.game_over_selected_index == i
            pulse = abs(math.sin(self.menu_pulse * 3.0))
            bg_alpha = int(80 + pulse * 50) if selected else 50
            bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            bg_surf.fill((255, 255, 255, bg_alpha))
            self.screen.blit(bg_surf, rect.topleft)
            border_w = 3 if selected else 1
            border_col = (255, 255, 255) if selected else (160, 160, 160)
            pygame.draw.rect(self.screen, border_col, rect, border_w, border_radius=8)
            text_col = (255, 255, 255) if selected else (190, 190, 190)
            lbl = self.body_font.render(label, True, text_col)
            if selected:
                shadow = self.body_font.render(label, True, (0, 0, 0))
                self.screen.blit(
                    shadow, shadow.get_rect(center=(rect.centerx + 1, rect.centery + 1))
                )
            self.screen.blit(lbl, lbl.get_rect(center=rect.center))
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

    def _draw_metal_frame(self, rect: pygame.Rect) -> None:
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel.fill((28, 31, 36, 226))
        self.screen.blit(panel, rect.topleft)

        pygame.draw.rect(self.screen, (122, 129, 139), rect, 3, border_radius=12)
        inner = rect.inflate(-12, -12)
        pygame.draw.rect(self.screen, (66, 72, 81), inner, 2, border_radius=10)

        rivets = [
            (rect.x + 16, rect.y + 16),
            (rect.right - 16, rect.y + 16),
            (rect.x + 16, rect.bottom - 16),
            (rect.right - 16, rect.bottom - 16),
        ]
        for x, y in rivets:
            pygame.draw.circle(self.screen, (156, 162, 172), (x, y), 5)
            pygame.draw.circle(self.screen, (65, 69, 77), (x, y), 2)

    def _draw_hud_creature_icon(
        self, x: int, y: int, w: int, h: int, *, killed: bool
    ) -> None:
        """Draw a small creature silhouette for the HUD objectives panel."""
        kind = self.hud_creature_kind
        sprite_set = self.creature_frames.get(kind)
        if sprite_set:
            frames = sprite_set.get("right") or sprite_set.get("left") or []
            if frames:
                scaled = pygame.transform.smoothscale(frames[0], (w, h))
                if killed:
                    # Killed → black silhouette
                    silhouette = scaled.copy()
                    silhouette.fill(
                        (0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT
                    )
                    self.screen.blit(silhouette, (x, y))
                else:
                    # Alive → full color
                    self.screen.blit(scaled, (x, y))
                return
        # Fallback simple bird polygon
        color = (96, 188, 86) if not killed else (20, 20, 20)
        cx, cy = x + w // 2, y + h // 2
        body = pygame.Rect(x + 4, y + 4, w - 8, h - 8)
        pygame.draw.ellipse(self.screen, color, body)
        wing = [(x, cy), (cx, y), (cx, cy + 4)]
        pygame.draw.polygon(self.screen, color, wing)

    def _draw_shell_icon(self, x: int, y: int, active: bool) -> None:
        body_color = (208, 67, 57) if active else (84, 53, 52)
        cap_color = (236, 181, 125) if active else (113, 95, 92)
        outline = (28, 18, 18)

        body = pygame.Rect(x, y, 16, 30)
        pygame.draw.rect(self.screen, body_color, body, border_radius=3)
        pygame.draw.rect(self.screen, outline, body, 1, border_radius=3)

        cap = pygame.Rect(x + 1, y + 22, 14, 8)
        pygame.draw.rect(self.screen, cap_color, cap, border_radius=2)
        pygame.draw.rect(self.screen, outline, cap, 1, border_radius=2)

    def _draw_hud(self) -> None:
        status = self.runtime.status()

        left_panel = pygame.Rect(18, WINDOW_HEIGHT - 114, 302, 96)
        center_panel = pygame.Rect(489, WINDOW_HEIGHT - 114, 302, 96)
        right_panel = pygame.Rect(WINDOW_WIDTH - 320, WINDOW_HEIGHT - 114, 302, 96)

        for panel in [left_panel, center_panel, right_panel]:
            panel_surface = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
            panel_surface.fill((18, 12, 14, 204))
            self.screen.blit(panel_surface, panel.topleft)
            pygame.draw.rect(self.screen, (116, 74, 71), panel, 2, border_radius=8)
            pygame.draw.rect(
                self.screen,
                (60, 33, 33),
                panel.inflate(-8, -8),
                1,
                border_radius=7,
            )

        label_color = (188, 82, 78)
        digit_color = (235, 76, 64)
        digit_shadow = (32, 8, 7)

        round_label = self.small_font.render("RONDA", True, label_color)
        self.screen.blit(round_label, (left_panel.x + 16, left_panel.y + 12))

        round_text = f"{int(status['round']):02d}"
        round_shadow = self.hud_font.render(round_text, True, digit_shadow)
        round_surface = self.hud_font.render(round_text, True, digit_color)
        self.screen.blit(round_shadow, (left_panel.x + 18, left_panel.y + 38))
        self.screen.blit(round_surface, (left_panel.x + 16, left_panel.y + 36))

        bullets_label = self.small_font.render("BALAS", True, label_color)
        self.screen.blit(bullets_label, (left_panel.x + 126, left_panel.y + 12))

        max_shells = int(self.config.shots_per_duck)
        shots_left = max(0, min(max_shells, int(status["shots_remaining"])))
        shell_x = left_panel.x + 124
        shell_y = left_panel.y + 46
        for idx in range(max_shells):
            self._draw_shell_icon(shell_x + (idx * 22), shell_y, idx < shots_left)

        objectives_label = self.small_font.render("OBJETIVOS", True, label_color)
        self.screen.blit(objectives_label, (center_panel.x + 16, center_panel.y + 12))

        objectives_done = max(
            0, min(int(self.config.ducks_per_round), int(status["ducks_caught"]))
        )
        objectives_total = int(self.config.ducks_per_round)
        icon_w, icon_h = 28, 22
        icon_spacing = icon_w + 5
        total_icons_w = objectives_total * icon_spacing - 5
        icon_start_x = center_panel.x + (center_panel.width - total_icons_w) // 2
        icon_y = center_panel.y + 44
        for i in range(objectives_total):
            self._draw_hud_creature_icon(
                icon_start_x + i * icon_spacing,
                icon_y,
                icon_w,
                icon_h,
                killed=(i < objectives_done),
            )

        score_label = self.small_font.render("SCORE", True, label_color)
        self.screen.blit(score_label, (right_panel.x + 16, right_panel.y + 12))

        score_text = f"{int(status['score']):05d}"
        score_shadow = self.hud_font.render(score_text, True, digit_shadow)
        score_surface = self.hud_font.render(score_text, True, digit_color)
        self.screen.blit(score_shadow, (right_panel.x + 18, right_panel.y + 44))
        self.screen.blit(score_surface, (right_panel.x + 16, right_panel.y + 42))

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

    def _draw_blood_effects(self) -> None:
        """Render all active blood effects."""
        for effect in self.blood_effects:
            if not self.blood_effect_surfaces:
                continue

            # Progress from 0 to 1
            progress = effect.age / effect.lifetime
            # Fade out effect
            alpha = int(255 * (1.0 - progress))

            # Select a blood surface (cycle through available)
            surface_idx = int(effect.age * 5) % len(self.blood_effect_surfaces)
            base_surface = self.blood_effect_surfaces[surface_idx]

            # Scale effect: start at 1.0, grow to 1.5, then fade
            scale = 1.0 + (progress * 0.5)
            scaled_size = int(80 * scale)
            scaled_surface = pygame.transform.smoothscale(
                base_surface, (scaled_size, scaled_size)
            )

            # Set alpha
            scaled_surface.set_alpha(alpha)

            # Draw centered on effect position
            rect = scaled_surface.get_rect(center=(int(effect.x), int(effect.y)))
            self.screen.blit(scaled_surface, rect)

    def _draw_boss_animation(self) -> None:
        """Draw the assassin/boss popping up from the bottom of the screen."""
        surface = self.boss_surfaces.get(self.boss_anim_kind)
        if surface is None:
            return
        boss_w, boss_h = 280, 240
        scaled = pygame.transform.smoothscale(surface, (boss_w, boss_h))
        x = WINDOW_WIDTH // 2 - boss_w // 2
        y = int(self.boss_anim_y)
        # Shadow
        shadow = scaled.copy()
        shadow.fill((0, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(shadow, (x + 10, y + 10))
        self.screen.blit(scaled, (x, y))

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
    try:
        app.run()
    finally:
        app.vision_controller.stop()


if __name__ == "__main__":
    main()
