import threading
import cv2
import time
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont

from screens.base_screen import BaseScreen
from engine.video_overlay import VideoOverlayEngine
from config import BG, ACCENT, TEXT_WHITE, WIN_W, WIN_H

class LoadingScreen(BaseScreen):
    """Pantalla de transición que espera a que la cámara real esté lista."""

    def __init__(self, app, players, **kwargs):
        super().__init__(app, **kwargs)
        self._players = players
        self._cap = None
        self._build_ui()
        
        # Iniciar inicialización de cámara
        self._start_camera_init()
        
        # Timeout de seguridad: Si en 5 segundos no hay cámara, forzar entrada
        QTimer.singleShot(5000, self._force_start)

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(80, 0, 80, 0)

        # Título (Actualizado por petición del usuario)
        self._title = QLabel("PREPARANDO JUGADORES...")
        self._title.setFont(QFont("Arial Black", 48, QFont.Bold))
        self._title.setStyleSheet(f"color: {ACCENT};")
        self._title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title)

        # Subtítulo
        self._subtitle = QLabel("Trayendo a las estrellas al campo...")
        self._subtitle.setFont(QFont("Arial", 24))
        self._subtitle.setStyleSheet(f"color: {TEXT_WHITE};")
        self._subtitle.setAlignment(Qt.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(self._subtitle)

        # Barra animada
        layout.addSpacing(60)
        progress = QProgressBar()
        progress.setRange(0, 0) 
        progress.setFixedHeight(15)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #333;
                border: none;
                border-radius: 7px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
                border-radius: 7px;
            }}
        """)
        layout.addWidget(progress)

        self.setLayout(layout)

    def _start_camera_init(self):
        self._active = True
        self._thread = threading.Thread(target=self._run_init_logic, daemon=True)
        self._thread.start()

    def _run_init_logic(self):
        """Tarea de fondo para abrir la cámara sin bloquear la UI."""
        try:
            # 1. Abrir Cámara
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                for _ in range(5): cap.read()
            
            # 2. Cargar Videos (Iniciarlos pausados para que el primer frame se vea)
            VideoOverlayEngine.start_experience(self._players, 720, 1280, paused=True)
            
        except Exception as e:
            print(f"[Loading] Init error: {e}")

        # Si seguimos en esta pantalla, avisar que terminamos
        if self._active:
            # Usar QTimer para volver al hilo principal de forma segura
            QTimer.singleShot(0, lambda: self._on_init_done(cap))

    def _on_init_done(self, cap):
        if not self._active:
            if cap: cap.release()
            return
        
        self._active = False
        self._cap = cap
        self.app.show_camera(self._players, self._cap)

    def _force_start(self):
        """Si el hilo se colgó o tardó demasiado, forzamos el cambio."""
        if self._active:
            print("[Loading] Timeout reached, forcing camera screen...")
            self._active = False
            # Intentar pasar lo que tengamos de la cámara (puede ser None)
            self.app.show_camera(self._players, self._cap)
