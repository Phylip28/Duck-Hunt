"""Pygame gameplay UI for the Duck Hunt Python migration."""

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
        self.creature_frames = self._load_creature_frames()
        self.target_surface = self._load_target_surface()
        self.scanline_overlay = self._build_scanline_overlay()

        self.title_font = self._load_font(54)
        self.hud_font = self._load_font(28)
        self.body_font = self._load_font(22)
        self.small_font = self._load_font(18)

        self.state = "menu"
        self.last_message = "Press ENTER to start"
        self.banner_text = ""
        self.banner_timer = 0.0

        self.current_creature: CreatureSprite | None = None
        self.hit_flash = 0.0
        self.miss_flash = 0.0

        self.input_fields = {
            "name": "Player",
            "seed_a": "123456789",
            "seed_b": "362436069",
        }
        self.input_order = ["name", "seed_a", "seed_b"]
        self.active_input = 0
        self.menu_pulse = 0.0

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

    def _load_creature_frames(self) -> dict[str, dict[str, pygame.Surface]]:
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
            return "TOP SCORE: 00000"
        top = rows[0]
        return f"TOP SCORE: {top.score:05d} - {top.player_name}"

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
                if self.state == "playing":
                    self._shoot_at(event.pos)

    def _on_keydown(self, event: pygame.event.Event) -> None:
        if self.state == "menu":
            self._on_menu_keydown(event)
            return

        if self.state == "playing":
            if event.key == pygame.K_ESCAPE:
                self._go_to_menu("Returned to menu")
            return

        if self.state in {"rankings", "game_over"}:
            if event.key in {pygame.K_RETURN, pygame.K_ESCAPE}:
                self._go_to_menu("Main menu")
            return

    def _on_menu_keydown(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            self.running = False
            return

        if event.key == pygame.K_RETURN:
            self._start_game_from_menu()
            return

        if event.key == pygame.K_r:
            self.state = "rankings"
            self.last_message = "Rankings"
            return

        if event.key == pygame.K_TAB:
            self.active_input = (self.active_input + 1) % len(self.input_order)
            return

        if event.key == pygame.K_UP:
            self.active_input = (self.active_input - 1) % len(self.input_order)
            return

        if event.key == pygame.K_DOWN:
            self.active_input = (self.active_input + 1) % len(self.input_order)
            return

        active_field = self.input_order[self.active_input]
        current = self.input_fields[active_field]

        if event.key == pygame.K_BACKSPACE:
            self.input_fields[active_field] = current[:-1]
            return

        char = event.unicode
        if not char or not char.isprintable():
            return

        if active_field == "name":
            if len(current) < 14:
                self.input_fields[active_field] += char
            return

        if char.isdigit() and len(current) < 10:
            self.input_fields[active_field] += char

    def _start_game_from_menu(self) -> None:
        player_name = self.input_fields["name"].strip() or "Player"
        try:
            seed_a = int(self.input_fields["seed_a"])
            seed_b = int(self.input_fields["seed_b"])
        except ValueError:
            self.last_message = "Seed A and Seed B must be integers"
            return

        context = {
            "version": 1,
            "session_nonce": 0,
            "round": 1,
            "map_index": 0,
            "mode": 1,
        }

        try:
            events = self.runtime.start(
                player_name=player_name,
                seed_a=seed_a,
                seed_b=seed_b,
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

    def _go_to_menu(self, message: str) -> None:
        self.state = "menu"
        self.current_creature = None
        self.banner_text = ""
        self.banner_timer = 0.0
        self.last_message = message
        pygame.mouse.set_visible(True)

        if self.session.game.game_active:
            self.session.stop_game_and_return_to_menu()

    def _update(self, dt: float, dt_ms: int) -> None:
        self.menu_pulse += dt

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
        elif self.state == "rankings":
            self._draw_rankings()
        elif self.state == "playing":
            self._draw_playing()
        else:
            self._draw_game_over()

        pygame.display.flip()

    def _draw_menu(self) -> None:
        if self.menu_background is not None:
            self.screen.blit(self.menu_background, (0, 0))
            veil = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            veil.fill((8, 12, 18, 132))
            self.screen.blit(veil, (0, 0))
        else:
            self.screen.fill((12, 20, 30))

        glow_alpha = int(75 + (math.sin(self.menu_pulse * 2.8) * 25))
        glow = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        glow.fill((255, 194, 78, max(0, glow_alpha)))
        self.screen.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self._draw_title_block("DUCK HUNT", "Python Migration - Pygame Edition")

        top_score_surface = self.small_font.render(
            self._top_score_text(),
            True,
            (248, 232, 164),
        )
        self.screen.blit(top_score_surface, (132, 174))

        box = pygame.Rect(130, 220, 1020, 360)
        pygame.draw.rect(self.screen, (20, 33, 47), box, border_radius=12)
        pygame.draw.rect(self.screen, (220, 183, 91), box, 4, border_radius=12)

        self._draw_input_field("Player", "name", 260)
        self._draw_input_field("Seed A", "seed_a", 330)
        self._draw_input_field("Seed B", "seed_b", 400)

        lines = [
            "ENTER: Start game",
            "TAB: Next field",
            "R: Rankings",
            "ESC: Exit",
        ]
        for index, line in enumerate(lines):
            label = self.small_font.render(line, True, (188, 214, 244))
            self.screen.blit(label, (170, 486 + (index * 24)))

        msg = self.small_font.render(self.last_message, True, (255, 230, 144))
        self.screen.blit(msg, (170, 596))
        self.screen.blit(self.scanline_overlay, (0, 0))

    def _draw_input_field(self, label: str, key: str, top: int) -> None:
        selected = self.input_order[self.active_input] == key
        text_color = (255, 240, 170) if selected else (199, 217, 233)
        border_color = (255, 191, 77) if selected else (87, 122, 148)

        label_surface = self.body_font.render(label, True, text_color)
        self.screen.blit(label_surface, (170, top))

        field_rect = pygame.Rect(360, top - 4, 600, 44)
        pygame.draw.rect(self.screen, (8, 13, 24), field_rect, border_radius=6)
        pygame.draw.rect(self.screen, border_color, field_rect, 2, border_radius=6)

        value = self.input_fields[key] or ""
        value_surface = self.body_font.render(value, True, text_color)
        self.screen.blit(value_surface, (378, top + 4))

    def _draw_rankings(self) -> None:
        self.screen.fill((9, 16, 28))
        self._draw_title_block("RANKINGS", "Top hunters")

        rows = self.session.menu.get_rankings_view(limit=10)
        panel = pygame.Rect(150, 180, 980, 470)
        pygame.draw.rect(self.screen, (16, 26, 43), panel, border_radius=12)
        pygame.draw.rect(self.screen, (187, 164, 105), panel, 3, border_radius=12)

        if not rows:
            empty = self.body_font.render("No scores yet", True, (222, 226, 233))
            self.screen.blit(empty, (190, 240))
        else:
            for idx, row in enumerate(rows):
                line = (
                    f"{row.rank:>2}. {row.player_name:<12} "
                    f"{row.score:>5} pts | R{row.round:<2} | {row.map_name}"
                )
                surface = self.body_font.render(line, True, (214, 230, 245))
                self.screen.blit(surface, (190, 220 + (idx * 38)))

        hint = self.small_font.render("ENTER or ESC: Back", True, (188, 214, 244))
        self.screen.blit(hint, (190, 610))
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

    def _draw_title_block(self, title: str, subtitle: str) -> None:
        title_surface = self.title_font.render(title, True, (244, 209, 117))
        subtitle_surface = self.small_font.render(subtitle, True, (187, 211, 236))
        self.screen.blit(title_surface, (128, 70))
        self.screen.blit(subtitle_surface, (132, 142))


def main() -> None:
    app = DuckHuntTkApp()
    app.run()


if __name__ == "__main__":
    main()
