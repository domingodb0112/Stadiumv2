"""
Camera preview screen — Design System C (Editorial Claro)
UI redesigned; all camera/video/segmentation logic is UNCHANGED.
"""
import cv2
import numpy as np
import threading

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QGridLayout, QWidget,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QImage, QCursor, QPainter, QColor, QPen

from config import (
    BG, TEXT_WHITE, ACCENT,
    WIN_W, WIN_H, COUNTDOWN_SEC, REF_W, REF_H, OUTPUT_DIR,
)
from screens.base_screen import BaseScreen
from camera_manager import CameraManager
from engine.video_overlay import VideoOverlayEngine
from ui_components import GradientBar, CaptureButton, TopBar
from theme import (
    FONT_SANS, BG_PRIMARY, INK_900, INK_400, GREEN_500, GREEN_600,
    BORDER, BG_MUTED,
)


# ── Corner-mark overlay widget ────────────────────────────────────────────────

class _CornerMarks(QWidget):
    """Draws green corner brackets over the camera viewport."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        arm = max(14, min(self.width(), self.height()) // 14)
        thick = max(2, arm // 6)
        pen = QPen(QColor(GREEN_500), thick, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        w, h = self.width(), self.height()
        m = thick // 2
        for (cx, cy, dx, dy) in [
            (m, m, 1, 1), (w - m, m, -1, 1),
            (m, h - m, 1, -1), (w - m, h - m, -1, -1),
        ]:
            p.drawLine(cx, cy, cx + dx * arm, cy)
            p.drawLine(cx, cy, cx, cy + dy * arm)


# ── Camera preview screen ─────────────────────────────────────────────────────

class CameraPreviewScreen(BaseScreen):

    def __init__(self, app, players, cap=None, **kwargs):
        super().__init__(app, **kwargs)
        self._players        = players
        self._cap            = cap
        self._running        = False
        self._countdown_left = 0
        self._counting       = False
        self._photo_frame    = None
        self._capture_pending = False

        self._build_ui()
        self._start_camera()
        VideoOverlayEngine.set_paused(False)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Top bar ───────────────────────────────────────────────────────────
        self._top_bar = TopBar()
        self._top_bar.set_title_mode(
            "Posicionate", 
            "FOTO CON JUGADORES", 
            back_callback=self._on_back
        )
        outer.addWidget(self._top_bar)

        # ── Camera viewport (with corner marks) ───────────────────────────────
        self._viewport_wrapper = QWidget()
        self._viewport_wrapper.setStyleSheet("background: transparent;")
        vw_layout = QGridLayout(self._viewport_wrapper)
        vw_layout.setContentsMargins(0, 0, 0, 0)
        vw_layout.setSpacing(0)

        # Camera canvas
        self._canvas = QLabel()
        self._canvas.setAlignment(Qt.AlignCenter)
        self._canvas.setStyleSheet(
            f"background-color: #1a1f1c; border-radius: 16px; border: none;"
        )
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vw_layout.addWidget(self._canvas, 0, 0)

        # Corner marks overlay
        self._corners = _CornerMarks(self._canvas)
        self._corners.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Countdown label overlay
        self._lbl_countdown = QLabel("")
        self._lbl_countdown.setFont(QFont(FONT_SANS, 160, QFont.Black))
        self._lbl_countdown.setStyleSheet(
            "QLabel { color: white; background-color: transparent; }"
        )
        self._lbl_countdown.setAlignment(Qt.AlignCenter)
        self._lbl_countdown.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._lbl_countdown.hide()
        vw_layout.addWidget(self._lbl_countdown, 0, 0)

        outer.addWidget(self._viewport_wrapper, 1)

        # ── Bottom control bar ────────────────────────────────────────────────
        self._bottom_bar = QWidget()
        self._bottom_bar.setStyleSheet(
            f"background-color: {BG_PRIMARY}; "
            f"border-top: 1px solid rgba(0,0,0,30);"
        )
        bottom_layout = QHBoxLayout(self._bottom_bar)
        bottom_layout.setAlignment(Qt.AlignCenter)
        bottom_layout.setSpacing(0)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Eye icon button (left side accessory)
        self._btn_eye = QPushButton()
        self._btn_eye.setCursor(Qt.PointingHandCursor)
        self._btn_eye.setText("◎")

        # Capture button (center)
        self._btn_capture = CaptureButton(size=64)
        self._btn_capture.clicked.connect(self._start_countdown)

        # Camera icon button (right side accessory)
        self._btn_cam_icon = QPushButton()
        self._btn_cam_icon.setCursor(Qt.PointingHandCursor)
        self._btn_cam_icon.setText("⊙")

        bottom_layout.addStretch()
        bottom_layout.addWidget(self._btn_eye)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self._btn_capture)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self._btn_cam_icon)
        bottom_layout.addStretch()

        outer.addWidget(self._bottom_bar)
        self.setLayout(outer)

        self._scale_ui(self.height() or 1920)

    def _scale_ui(self, h: int):
        # Scale TopBar
        if hasattr(self, "_top_bar"):
            self._top_bar.scale_to(h)

        bar_h    = max(80, int(h * 0.090))
        cap_sz   = max(48, int(h * 0.058))
        acc_sz   = max(36, int(h * 0.035))
        acc_r    = max(8,  int(h * 0.010))
        acc_pt   = max(12, int(h * 0.012))
        vw_m     = max(12, int(h * 0.010))  # viewport margin

        self._bottom_bar.setFixedHeight(bar_h)

        self._btn_capture.setFixedSize(cap_sz, cap_sz)

        acc_style = f"""
            QPushButton {{
                background-color: {BG_MUTED};
                color: {INK_900};
                border: none;
                border-radius: {acc_r}px;
                font-size: {acc_pt}px;
            }}
            QPushButton:hover {{ background-color: #e2e3de; }}
        """
        self._btn_eye.setFixedSize(acc_sz, acc_sz)
        self._btn_eye.setStyleSheet(acc_style)
        self._btn_cam_icon.setFixedSize(acc_sz, acc_sz)
        self._btn_cam_icon.setStyleSheet(acc_style)

        cnt_pt = max(60, int(h * 0.110))
        self._lbl_countdown.setFont(QFont(FONT_SANS, cnt_pt, QFont.Black))

    # ── Corner marks follow canvas ─────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_ui(self.height())
        # Place corner-mark overlay to cover the canvas exactly
        QTimer.singleShot(0, self._reposition_corners)

    def _reposition_corners(self):
        self._corners.setGeometry(self._canvas.rect())

    # ── Camera loop (UNCHANGED) ────────────────────────────────────────────────

    def _start_camera(self):
        self._running = True
        self._timer = QTimer()
        self._timer.timeout.connect(self._capture_frame)
        self._timer.start(33)

        if self._cap is None:
            threading.Thread(target=self._init_hardware_async, daemon=True).start()

    def _init_hardware_async(self):
        try:
            if self._cap is None:
                self._cap = cv2.VideoCapture(0)
            VideoOverlayEngine.start_experience(self._players, 720, 1280)
        except Exception as e:
            print(f"[Camera] Async init error: {e}")

    def _capture_frame(self):
        if not self._running or self._cap is None or not self._cap.isOpened():
            return

        ret, frame = self._cap.read()
        if not ret:
            return

        h, w = frame.shape[:2]
        target_aspect = 9 / 16
        current_aspect = w / h

        if current_aspect > target_aspect:
            new_w = int(h * target_aspect)
            x_offset = (w - new_w) // 2
            frame = frame[:, x_offset : x_offset + new_w]
        elif current_aspect < target_aspect:
            new_h = int(w / target_aspect)
            y_offset = (h - new_h) // 2
            frame = frame[y_offset : y_offset + new_h, :]

        PREVIEW_W = 540
        PREVIEW_H = 960

        if not hasattr(self, "_last_res") or self._last_res != (PREVIEW_W, PREVIEW_H):
            VideoOverlayEngine.start_experience(self._players, PREVIEW_W, PREVIEW_H)
            self._last_res = (PREVIEW_W, PREVIEW_H)

        preview_frame = cv2.resize(frame, (PREVIEW_W, PREVIEW_H))

        if self._capture_pending:
            self._capture_pending = False
            self._photo_frame = cv2.resize(frame, (REF_W, REF_H))
            preview_frame = VideoOverlayEngine.apply_all(preview_frame)
        else:
            preview_frame = VideoOverlayEngine.apply_all(preview_frame)

        self._update_canvas(preview_frame)

    def _update_canvas(self, frame: np.ndarray):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        scaled_pixmap = pixmap.scaled(
            self._canvas.size(),
            Qt.KeepAspectRatio,
            Qt.FastTransformation,
        )
        self._canvas.setPixmap(scaled_pixmap)
        # Keep corner marks over canvas
        self._corners.setGeometry(self._canvas.rect())

    # ── Countdown (UNCHANGED logic) ────────────────────────────────────────────

    def _start_countdown(self):
        if self._counting:
            return
        self._counting       = True
        self._countdown_left = COUNTDOWN_SEC
        self._btn_capture.setVisible(False)
        self._lbl_countdown.show()
        self._countdown_timer = QTimer()
        self._countdown_timer.timeout.connect(self._tick)
        self._countdown_timer.start(1000)

    def _tick(self):
        if self._countdown_left > 0:
            self._lbl_countdown.setText(str(self._countdown_left))
            self._countdown_left -= 1
        else:
            self._countdown_timer.stop()
            self._lbl_countdown.hide()
            self._counting        = False
            self._capture_pending = True
            self._btn_capture.setVisible(True)
            QTimer.singleShot(100, self._wait_for_photo)

    def _wait_for_photo(self):
        if self._photo_frame is None:
            QTimer.singleShot(100, self._wait_for_photo)
            return
        self._do_save()

    def _do_save(self):
        import time as _t
        path = str(OUTPUT_DIR / f"photo_{int(_t.time())}.jpg")
        cv2.imwrite(path, self._photo_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

        from screens.simulation import PreProcessingEngine
        PreProcessingEngine.start_segmentation(path)

        self.app.show_photo_view(path, self._players)

    # ── Navigation / cleanup (UNCHANGED) ──────────────────────────────────────

    def _on_back(self):
        self.app.show_player_selection()

    def on_destroy(self):
        self._running = False
        if hasattr(self, "_timer"):
            self._timer.stop()
        if hasattr(self, "_countdown_timer"):
            self._countdown_timer.stop()
