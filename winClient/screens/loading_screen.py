import threading
import cv2
import time
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from screens.base_screen import BaseScreen
from engine.video_overlay import VideoOverlayEngine
from camera_manager import CameraManager
from theme import BG_PRIMARY, INK_900, GREEN_500, FONT_SANS, INK_400


class LoadingScreen(BaseScreen):
    """Pantalla de transición ULTRA-RÁPIDA con estética Design System C."""

    def __init__(self, app, players, **kwargs):
        super().__init__(app, **kwargs)
        self._players = players
        self._active = True
        self._build_ui()
        self._run_logic()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(20)

        # Small accent label
        self._pre_title = QLabel("STADIUM")
        self._pre_title.setFont(QFont(FONT_SANS, 12, QFont.Bold))
        self._pre_title.setStyleSheet(f"color: {INK_400}; letter-spacing: 2px;")
        self._pre_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._pre_title)

        # Main loading text
        self._title = QLabel("PREPARANDO\nLA CANCHA")
        self._title.setFont(QFont(FONT_SANS, 42, QFont.Black))
        self._title.setStyleSheet(f"color: {INK_900};")
        self._title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title)

        # Simple green dot pulse or static dot for now to match brand
        self._dot = QWidget()
        self._dot.setFixedSize(12, 12)
        self._dot.setStyleSheet(f"background-color: {GREEN_500}; border-radius: 6px;")
        layout.addWidget(self._dot, alignment=Qt.AlignCenter)

    def _run_logic(self):
        try:
            # Obtener cámara (Ya debería estar abierta por el Main)
            cap = CameraManager.get_cap()
            
            # Resetear y preparar motor (Instantáneo porque ya hubo Warm-up)
            VideoOverlayEngine.start_experience(self._players, 720, 1280, paused=False)
            
            # Salto inmediato: Menos de 50ms para que sea imperceptible
            # (Aumentamos un poco a 100ms para que el usuario vea el nuevo diseño un instante)
            QTimer.singleShot(100, lambda: self._do_transition(cap))
            
        except Exception as e:
            print(f"[Loading] Immediate init error: {e}")
            QTimer.singleShot(0, lambda: self._do_transition(CameraManager.get_cap()))

    def _do_transition(self, cap):
        if self._active:
            self._active = False
            self.app.show_camera(self._players, cap)

    def on_destroy(self):
        self._active = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        h = self.height()
        # Scale fonts
        self._title.setFont(QFont(FONT_SANS, max(24, int(h * 0.040)), QFont.Black))
        self._pre_title.setFont(QFont(FONT_SANS, max(10, int(h * 0.010)), QFont.Bold))
