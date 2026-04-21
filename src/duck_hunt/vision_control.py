"""Vision-based input control for Futuristic mode.

This module is intentionally isolated so camera/gesture logic stays
separate from game flow and rendering code.

Compatible with mediapipe >= 0.10 (Tasks API).
Falls back to optical-flow motion tracking when the model is unavailable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VisionSample:
    """Single vision update result."""

    cursor_pos: tuple[int, int]
    shoot: bool
    available: bool
    status: str


class HandVisionController:
    """Tracks hand motion and fist gesture for aiming and shooting.

    Uses mediapipe 0.10 HandLandmarker (Tasks API) when available;
    falls back to optical-flow contour tracking otherwise.
    """

    MODEL_ASSET_RELPATH = "assets/hand_landmarker.task"

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        repo_root: Path | None = None,
        camera_index: int = 0,
        smoothing: float = 1.0,
        shot_cooldown_seconds: float = 0.45,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.repo_root = repo_root or Path(__file__).resolve().parents[2]
        self.camera_index = camera_index
        self.smoothing = max(0.0, min(1.0, smoothing))
        self.shot_cooldown_seconds = max(0.05, shot_cooldown_seconds)

        self._cv2: Any | None = None
        self._capture: Any | None = None
        self._landmarker: Any | None = None
        self._frame_ts_ms = 0
        self._started = False

        self._cursor_x = float(screen_width // 2)
        self._cursor_y = float(screen_height // 2)
        self._fist_was_closed = False
        self._fist_frames = 0
        self._last_shot_time = 0.0
        self._status = "Vision desactivada"

        # Relative (mouse-like) tracking state
        self._prev_lm_x: float | None = None
        self._prev_lm_y: float | None = None
        self._prev_wrist_x: float | None = None
        self._prev_wrist_y: float | None = None
        self._hand_speed: float = 0.0
        self.sensitivity: float = 2.0

        # Debug window
        self.show_debug_window = True
        self.debug_window_name = "Duck Hunt Vision Debug"
        self._debug_window_enabled = True

        # Motion-fallback state
        self._prev_gray: Any | None = None
        self._motion_shot_threshold = 16000

    @property
    def status(self) -> str:
        return self._status

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> bool:
        if self._started:
            return True

        try:
            import cv2  # type: ignore
        except ModuleNotFoundError:
            self._status = "Falta OpenCV: instala opencv-python"
            return False

        self._cv2 = cv2

        capture = cv2.VideoCapture(self.camera_index)
        if not capture or not capture.isOpened():
            self._status = "No se pudo abrir la camara"
            return False

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._capture = capture
        self._frame_ts_ms = 0
        self._prev_gray = None
        self._fist_was_closed = False
        self._fist_frames = 0
        self._prev_lm_x = None
        self._prev_lm_y = None
        self._prev_wrist_x = None
        self._prev_wrist_y = None
        self._hand_speed = 0.0

        self._landmarker = self._build_landmarker()
        self._started = True

        if self._landmarker is not None:
            self._status = "Vision activa (mediapipe)"
        else:
            self._status = "Vision activa (fallback movimiento)"
        return True

    def stop(self) -> None:
        if self._landmarker is not None:
            try:
                self._landmarker.close()
            except Exception:
                pass
            self._landmarker = None

        if self._capture is not None:
            try:
                self._capture.release()
            except Exception:
                pass
            self._capture = None

        if self._cv2 is not None and self._debug_window_enabled:
            try:
                self._cv2.destroyWindow(self.debug_window_name)
                self._cv2.waitKey(1)
            except Exception:
                pass

        self._prev_gray = None
        self._started = False

    def _build_landmarker(self) -> Any | None:
        model_path = self.repo_root / self.MODEL_ASSET_RELPATH
        if not model_path.exists():
            self._status = f"Modelo no encontrado: {model_path.name} — usando fallback"
            return None

        try:
            from mediapipe.tasks.python import vision  # type: ignore
            from mediapipe.tasks.python.core import (
                base_options as base_opts,  # type: ignore
            )

            options = vision.HandLandmarkerOptions(
                base_options=base_opts.BaseOptions(model_asset_path=str(model_path)),
                num_hands=1,
                running_mode=vision.RunningMode.VIDEO,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            return vision.HandLandmarker.create_from_options(options)
        except Exception as exc:
            self._status = f"Error al cargar mediapipe: {exc} — usando fallback"
            return None

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------

    def update(self) -> VisionSample:
        if not self._started or self._capture is None:
            return VisionSample(
                cursor_pos=(int(self._cursor_x), int(self._cursor_y)),
                shoot=False,
                available=False,
                status=self._status,
            )

        assert self._cv2 is not None

        ok, frame = self._capture.read()
        if not ok:
            self._status = "Camara sin imagen"
            return VisionSample(
                cursor_pos=(int(self._cursor_x), int(self._cursor_y)),
                shoot=False,
                available=True,
                status=self._status,
            )

        frame = self._cv2.flip(frame, 1)

        if self._landmarker is not None:
            tracked, shoot = self._update_mediapipe(frame)
            mode_label = "mediapipe"
        else:
            tracked, shoot, _ = self._update_motion_fallback(frame)
            mode_label = "fallback-movimiento"

        self._show_debug_preview(frame, mode_label, tracked, shoot)

        return VisionSample(
            cursor_pos=(int(self._cursor_x), int(self._cursor_y)),
            shoot=shoot,
            available=True,
            status=self._status,
        )

    # ------------------------------------------------------------------
    # MediaPipe Tasks detection
    # ------------------------------------------------------------------

    def _update_mediapipe(self, frame: Any) -> tuple[bool, bool]:
        assert self._cv2 is not None
        assert self._landmarker is not None

        try:
            import mediapipe as mp  # type: ignore
        except ModuleNotFoundError:
            return False, False

        self._frame_ts_ms += 33  # ~30 fps virtual timestamp

        frame_rgb = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb,
        )

        try:
            result = self._landmarker.detect_for_video(mp_image, self._frame_ts_ms)
        except Exception as exc:
            self._status = f"Error vision: {exc}"
            return False, False

        if not result.hand_landmarks:
            self._fist_was_closed = False
            self._fist_frames = 0
            self._prev_lm_x = None
            self._prev_lm_y = None
            self._prev_wrist_x = None
            self._prev_wrist_y = None
            self._hand_speed = 0.0
            self._status = "Buscando mano..."
            return False, False

        landmarks = result.hand_landmarks[0]
        wrist = landmarks[0]

        # Cursor: relative movement from wrist — stable point unaffected by finger gestures
        if self._prev_wrist_x is not None:
            dw_x = wrist.x - self._prev_wrist_x
            dw_y = wrist.y - self._prev_wrist_y
            self._hand_speed = (dw_x * dw_x + dw_y * dw_y) ** 0.5
            dx = dw_x * self.screen_width * self.sensitivity
            dy = dw_y * self.screen_height * self.sensitivity
            self._cursor_x = max(
                0.0, min(float(self.screen_width - 1), self._cursor_x + dx)
            )
            self._cursor_y = max(
                0.0, min(float(self.screen_height - 1), self._cursor_y + dy)
            )
        else:
            self._hand_speed = 0.0

        self._prev_lm_x = wrist.x
        self._prev_lm_y = wrist.y
        self._prev_wrist_x = wrist.x
        self._prev_wrist_y = wrist.y

        # Draw bounding ellipse around all hand landmarks
        frame_h, frame_w = frame.shape[:2]
        all_xs = [int(lm.x * frame_w) for lm in landmarks]
        all_ys = [int(lm.y * frame_h) for lm in landmarks]
        cx = (min(all_xs) + max(all_xs)) // 2
        cy = (min(all_ys) + max(all_ys)) // 2
        rx = max(10, (max(all_xs) - min(all_xs)) // 2 + 14)
        ry = max(10, (max(all_ys) - min(all_ys)) // 2 + 14)

        fist_closed = self._is_fist_closed(landmarks)
        ellipse_color = (60, 50, 255) if fist_closed else (0, 230, 110)
        self._cv2.ellipse(frame, (cx, cy), (rx, ry), 0, 0, 360, ellipse_color, 2)

        # Debounce: require 2 consecutive fist frames before firing
        if fist_closed:
            self._fist_frames += 1
        else:
            self._fist_frames = 0

        shoot = False
        now = time.monotonic()
        # Velocity gate: wrist speed in normalized units (0.0–1.0 per frame)
        # 0.025 ≈ 2.5% of frame width per frame — blocks fast repositioning, not fist closure
        hand_is_still = self._hand_speed < 0.025
        if (
            self._fist_frames == 2
            and hand_is_still
            and (now - self._last_shot_time) >= self.shot_cooldown_seconds
        ):
            shoot = True
            self._last_shot_time = now

        self._fist_was_closed = fist_closed
        self._status = "Puno cerrado! DISPARO" if fist_closed else "Mano detectada"
        return True, shoot

    def _is_fist_closed(self, landmarks: Any) -> bool:
        """Return True when all 4 fingers are folded past their MCP knuckle."""
        # Compare fingertip to MCP (knuckle base) — stricter than PIP comparison
        # (tip_id, mcp_id) for index, middle, ring, pinky
        folded = 0
        for tip_id, mcp_id in ((8, 5), (12, 9), (16, 13), (20, 17)):
            if landmarks[tip_id].y > landmarks[mcp_id].y:
                folded += 1

        # Thumb: tip must be close to index MCP (knuckle) when tucked
        thumb_tip = landmarks[4]
        index_mcp = landmarks[5]
        thumb_tucked = (
            abs(thumb_tip.x - index_mcp.x) < 0.10
            and abs(thumb_tip.y - index_mcp.y) < 0.10
        )
        return folded == 4 and thumb_tucked

    # ------------------------------------------------------------------
    # Optical-flow motion fallback
    # ------------------------------------------------------------------

    def _update_motion_fallback(self, frame: Any) -> tuple[bool, bool, int]:
        assert self._cv2 is not None

        gray = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2GRAY)
        gray = self._cv2.GaussianBlur(gray, (9, 9), 0)

        if self._prev_gray is None:
            self._prev_gray = gray
            self._status = "Calibrando camara..."
            return False, False, 0

        delta = self._cv2.absdiff(self._prev_gray, gray)
        _, thresh = self._cv2.threshold(delta, 25, 255, self._cv2.THRESH_BINARY)
        thresh = self._cv2.dilate(thresh, None, iterations=2)
        motion_pixels = int(self._cv2.countNonZero(thresh))

        contours_result = self._cv2.findContours(
            thresh, self._cv2.RETR_EXTERNAL, self._cv2.CHAIN_APPROX_SIMPLE
        )
        contours = (
            contours_result[0] if len(contours_result) == 2 else contours_result[1]
        )

        tracked = False
        if contours:
            contour = max(contours, key=self._cv2.contourArea)
            if float(self._cv2.contourArea(contour)) >= 1200.0:
                moments = self._cv2.moments(contour)
                if moments["m00"] > 0.0:
                    cx = int(moments["m10"] / moments["m00"])
                    cy = int(moments["m01"] / moments["m00"])
                    frame_h, frame_w = frame.shape[:2]
                    target_x = max(
                        0,
                        min(
                            self.screen_width - 1,
                            int((cx / max(1, frame_w)) * self.screen_width),
                        ),
                    )
                    target_y = max(
                        0,
                        min(
                            self.screen_height - 1,
                            int((cy / max(1, frame_h)) * self.screen_height),
                        ),
                    )
                    blend = self.smoothing
                    self._cursor_x = ((1.0 - blend) * self._cursor_x) + (
                        blend * target_x
                    )
                    self._cursor_y = ((1.0 - blend) * self._cursor_y) + (
                        blend * target_y
                    )
                    tracked = True
                    self._cv2.circle(frame, (cx, cy), 14, (0, 255, 255), 2)
                    self._cv2.drawMarker(
                        frame,
                        (cx, cy),
                        (0, 255, 255),
                        markerType=self._cv2.MARKER_CROSS,
                        markerSize=20,
                        thickness=2,
                    )

        shoot = False
        now = time.monotonic()
        if (
            tracked
            and motion_pixels >= self._motion_shot_threshold
            and (now - self._last_shot_time) >= self.shot_cooldown_seconds
        ):
            shoot = True
            self._last_shot_time = now

        self._prev_gray = gray
        self._status = "Movimiento detectado" if tracked else "Sin movimiento visible"
        return tracked, shoot, motion_pixels

    # ------------------------------------------------------------------
    # Debug window
    # ------------------------------------------------------------------

    def _show_debug_preview(
        self,
        frame: Any,
        mode_label: str,
        tracked: bool,
        shoot: bool,
    ) -> None:
        if not self.show_debug_window or not self._debug_window_enabled:
            return
        if self._cv2 is None:
            return

        color = (40, 220, 80) if tracked else (40, 120, 220)
        self._cv2.putText(
            frame,
            f"Mode: {mode_label}",
            (12, 28),
            self._cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color,
            2,
            self._cv2.LINE_AA,
        )
        self._cv2.putText(
            frame,
            f"Cursor: {int(self._cursor_x)}, {int(self._cursor_y)}",
            (12, 56),
            self._cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (225, 225, 225),
            2,
            self._cv2.LINE_AA,
        )
        self._cv2.putText(
            frame,
            f"Shoot: {'YES !!!' if shoot else 'NO'}",
            (12, 84),
            self._cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (60, 50, 255) if shoot else (200, 200, 200),
            2,
            self._cv2.LINE_AA,
        )
        self._cv2.putText(
            frame,
            self._status,
            (12, frame.shape[0] - 14),
            self._cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (200, 200, 80),
            1,
            self._cv2.LINE_AA,
        )

        try:
            self._cv2.imshow(self.debug_window_name, frame)
            self._cv2.waitKey(1)
        except Exception:
            self._debug_window_enabled = False
