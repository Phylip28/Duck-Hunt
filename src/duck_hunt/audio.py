"""Audio manager for Duck Hunt pygame UI."""

from __future__ import annotations

from pathlib import Path

try:
    import pygame
except ModuleNotFoundError:
    pygame = None


class AudioManager:
    """Manages game audio: background music and sound effects."""

    def __init__(self, repo_root: Path) -> None:
        """Initialize audio manager and load sounds."""
        self.repo_root = repo_root
        self.sounds: dict[str, pygame.mixer.Sound | None] = {}
        self.music_playing = False
        self.mute = False

        # Initialize mixer if pygame is available
        if pygame:
            try:
                pygame.mixer.init()
            except pygame.error:
                pass

        # Load sound effects
        self._load_sound("shoot", "assets/audio/sfx/duck-shot.mp3")
        self._load_sound("quack", "assets/audio/sfx/duck-quack.mp3")
        self._load_sound("score", "assets/audio/sfx/dog-score.mp3")

        # Load background music
        self.music_path = repo_root / "assets/audio/music/soundtrack.mp3"

    def _load_sound(self, key: str, relative_path: str) -> None:
        """Load a sound effect from a file."""
        if not pygame:
            return

        path = self.repo_root / relative_path
        if not path.exists():
            return

        try:
            self.sounds[key] = pygame.mixer.Sound(str(path))
        except pygame.error:
            pass

    def play_sound(self, key: str, volume: float = 1.0) -> None:
        """Play a sound effect."""
        if self.mute or not pygame:
            return

        sound = self.sounds.get(key)
        if sound:
            try:
                sound.set_volume(max(0.0, min(1.0, volume)))
                sound.play()
            except pygame.error:
                pass

    def play_music(self, volume: float = 0.7) -> None:
        """Start background music loop."""
        if self.mute or not pygame or not self.music_path.exists():
            return

        if self.music_playing:
            return

        try:
            pygame.mixer.music.load(str(self.music_path))
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            pygame.mixer.music.play(-1)  # -1 = loop indefinitely
            self.music_playing = True
        except pygame.error:
            pass

    def stop_music(self) -> None:
        """Stop background music."""
        if pygame and self.music_playing:
            try:
                pygame.mixer.music.stop()
                self.music_playing = False
            except pygame.error:
                pass

    def toggle_mute(self) -> bool:
        """Toggle mute state and return new state."""
        self.mute = not self.mute
        if self.mute:
            self.stop_music()
        else:
            if self.music_path.exists():
                self.play_music()
        return self.mute

    def set_volume(self, volume: float) -> None:
        """Set master volume (0.0 to 1.0)."""
        if pygame:
            try:
                pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            except pygame.error:
                pass
