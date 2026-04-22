import threading
import cv2
import time
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from screens.base_screen import BaseScreen
from engine.video_overlay import VideoOverlayEngine
from camera_manager import CameraManager
from config import BG, ACCENT, TEXT_WHITE

class LoadingScreen(BaseScreen):
    """Pantalla de transición ULTRA-RÁPIDA que aprovecha el Warm-up."""

    def __init__(self, app, players, **kwargs):
        super().__init__(app, **kwargs)
        self._players = players
        self._active = True
        self._build_ui()
        
        # Iniciar validación inmediata
        self._run_logic()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(80, 0, 80, 0)

        self._title = QLabel("PREPARANDO JUGADORES...")
        self._title.setFont(QFont("Arial Black", 48, QFont.Bold))
        self._title.setStyleSheet(f"color: {ACCENT};")
        self._title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title)
        
        self.setLayout(layout)

    def _run_logic(self):
        try:
            # Obtener cámara (Ya debería estar abierta por el Main)
            cap = CameraManager.get_cap()
            
            # Resetear y preparar motor (Instantáneo porque ya hubo Warm-up)
            VideoOverlayEngine.start_experience(self._players, 720, 1280, paused=False)
            
            # Salto inmediato: Menos de 50ms para que sea imperceptible
            QTimer.singleShot(50, lambda: self._do_transition(cap))
            
        except Exception as e:
            print(f"[Loading] Immediate init error: {e}")
            from camera_manager import CameraManager
            QTimer.singleShot(0, lambda: self._do_transition(CameraManager.get_cap()))

    def _do_transition(self, cap):
        if self._active:
            self._active = False
            self.app.show_camera(self._players, cap)

    def on_destroy(self):
        self._active = False
