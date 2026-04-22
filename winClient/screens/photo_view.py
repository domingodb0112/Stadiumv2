"""
Photo view screen — Design System C (Editorial Claro)
Displays captured photo with retry/send buttons and auto-send countdown.
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QCursor, QPainter, QColor

from screens.base_screen import BaseScreen
from config import AUTO_SEND_MS
from ui_components import TopBar
from theme import (
    FONT_SANS, BG_PRIMARY, INK_900, INK_400, GREEN_500,
    BORDER, BG_MUTED,
    btn_primary, btn_secondary,
)


class PhotoViewScreen(BaseScreen):

    def __init__(self, app, photo_path: str, players, **kwargs):
        super().__init__(app, **kwargs)
        self._photo_path  = photo_path
        self._players     = players
        self._timer       = None
        self._seconds_left = AUTO_SEND_MS // 1000

        self._build_ui()
        self._load_photo()
        self._start_timer()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Top bar ───────────────────────────────────────────────────────────
        self._top_bar = TopBar()
        self._top_bar.set_preview_mode(
            "Vista previa", 
            close_callback=self._on_retake
        )
        outer.addWidget(self._top_bar)

        # ── Photo display ─────────────────────────────────────────────────────
        self._photo_container = QWidget()
        self._photo_container.setStyleSheet(f"background-color: {BG_PRIMARY};")
        ph_l = QVBoxLayout(self._photo_container)
        ph_l.setContentsMargins(0, 0, 0, 0)
        ph_l.setSpacing(0)

        self._lbl_photo = QLabel()
        self._lbl_photo.setAlignment(Qt.AlignCenter)
        self._lbl_photo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._lbl_photo.setStyleSheet(
            "background-color: #1a1f1c; border-radius: 16px; border: none;"
        )
        ph_l.addWidget(self._lbl_photo)

        outer.addWidget(self._photo_container, 1)

        # ── Bottom action bar ─────────────────────────────────────────────────
        self._bottom_bar = QWidget()
        self._bottom_bar.setStyleSheet(
            f"background-color: {BG_PRIMARY}; "
            f"border-top: 1px solid rgba(0,0,0,30);"
        )
        bl = QHBoxLayout(self._bottom_bar)
        bl.setSpacing(12)

        self._btn_retake = QPushButton("Reintentar")
        self._btn_retake.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_retake.clicked.connect(self._on_retake)

        self._btn_send = QPushButton(f"Enviar foto  ({self._seconds_left}s)")
        self._btn_send.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_send.clicked.connect(self._on_send)

        bl.addWidget(self._btn_retake, 1)
        bl.addWidget(self._btn_send, 2)

        outer.addWidget(self._bottom_bar)
        self.setLayout(outer)

        self._scale_ui(self.height() or 1920)

    # ── Scaling ────────────────────────────────────────────────────────────────

    def _scale_ui(self, h: int):
        top_h    = max(48, int(h * 0.038))
        btn_pt   = max(12, int(h * 0.011))
        btn_r    = max(10, int(h * 0.013))
        ph_m     = max(12, int(h * 0.010))  # photo margins

        if hasattr(self, "_top_bar"):
            self._top_bar.scale_to(h)

        self._photo_container.layout().setContentsMargins(ph_m, ph_m, ph_m, ph_m)

        self._bottom_bar.setFixedHeight(max(72, int(h * 0.075)))
        self._bottom_bar.layout().setContentsMargins(16, 0, 16, 0)

        self._btn_retake.setFont(QFont(FONT_SANS, btn_pt, QFont.Medium))
        self._btn_retake.setFixedHeight(max(44, int(h * 0.042)))
        self._btn_retake.setStyleSheet(btn_secondary(radius=btn_r, font_size=btn_pt))

        self._btn_send.setFont(QFont(FONT_SANS, btn_pt, QFont.DemiBold))
        self._btn_send.setFixedHeight(max(44, int(h * 0.042)))
        self._btn_send.setStyleSheet(btn_primary(radius=btn_r, font_size=btn_pt))

    # ── Photo ──────────────────────────────────────────────────────────────────

    def _load_photo(self):
        try:
            pixmap = QPixmap(self._photo_path)
            if not pixmap.isNull():
                # Use container size as reference for scaling
                avail_w = max(100, self._photo_container.width())
                avail_h = max(100, self._photo_container.height())
                
                scaled = pixmap.scaled(
                    avail_w, avail_h,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self._lbl_photo.setPixmap(scaled)
        except Exception as e:
            print(f"[PhotoView] Error loading photo: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_ui(self.height())
        self._load_photo()

    # ── Timer ──────────────────────────────────────────────────────────────────

    def _start_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _tick(self):
        if self._seconds_left > 0:
            self._seconds_left -= 1
            self._btn_send.setText(f"Enviar foto  ({self._seconds_left}s)")
        else:
            self._on_send()

    def _stop_timer(self):
        if self._timer:
            self._timer.stop()
            self._timer = None

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _on_retake(self):
        self._stop_timer()
        self.app.show_camera(self._players)

    def _on_send(self):
        self._stop_timer()
        self.app.show_simulation(self._photo_path, self._players)

    def on_destroy(self):
        self._stop_timer()
