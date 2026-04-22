"""
Camera preview screen for PyQt5 — optimized for high speed.
"""
import cv2
import numpy as np
import threading
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QImage, QCursor

from screens.base_screen import BaseScreen
from engine.video_overlay import VideoOverlayEngine
from config import (
    BG, TEXT_WHITE, ACCENT,
    WIN_W, WIN_H, COUNTDOWN_SEC, REF_W, REF_H, OUTPUT_DIR
)


class CameraPreviewScreen(BaseScreen):
    """Pantalla de cámara en vivo con carga asíncrona para evitar lag."""

    def __init__(self, app, players, **kwargs):
        super().__init__(app, **kwargs)
        self._players        = players
        self._cap            = None
        self._running        = False
        self._countdown_left = 0
        self._counting       = False
        self._photo_frame    = None
        self._capture_pending = False

        self._build_ui()
        self._start_camera()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Video canvas
        self._canvas = QLabel()
        self._canvas.setMinimumSize(WIN_W, WIN_H)
        self._canvas.setMaximumSize(WIN_W, WIN_H)
        self._canvas.setAlignment(Qt.AlignCenter)
        self._canvas.setStyleSheet(f"background-color: {BG};")
        main_layout.addWidget(self._canvas)

        # Back button
        self._back_btn = QPushButton("←")
        self._back_btn.setFont(QFont("Arial", 20))
        self._back_btn.setFixedSize(48, 48)
        self._back_btn.setStyleSheet("""
            QPushButton           { background-color:#333; color:white; border:none; border-radius:24px; }
            QPushButton:hover     { background-color:#555; }
        """)
        self._back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._back_btn.clicked.connect(self._on_back)

        # Countdown label
        self._lbl_countdown = QLabel("")
        self._lbl_countdown.setFont(QFont("Arial", 150, QFont.Bold))
        self._lbl_countdown.setStyleSheet(
            "QLabel { color:white; background-color:transparent; }"
        )
        self._lbl_countdown.setAlignment(Qt.AlignCenter)
        self._lbl_countdown.hide()

        # Capture button
        self._btn_capture = QPushButton("📷 CAPTURAR")
        self._btn_capture.setFont(QFont("Arial", 16, QFont.Bold))
        self._btn_capture.setFixedSize(200, 60)
        self._btn_capture.setStyleSheet(f"""
            QPushButton           {{ background-color:{ACCENT}; color:white; border:none; border-radius:30px; font-weight:bold; }}
            QPushButton:hover     {{ background-color:#059669; }}
            QPushButton:pressed   {{ background-color:#047857; }}
        """)
        self._btn_capture.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_capture.clicked.connect(self._start_countdown)

        capture_row = QHBoxLayout()
        capture_row.addStretch()
        capture_row.addWidget(self._btn_capture)
        capture_row.addStretch()
        capture_row.setContentsMargins(0, 32, 0, 32)

        main_layout.addWidget(self._lbl_countdown)
        main_layout.addLayout(capture_row)
        self.setLayout(main_layout)

    # ── Camera loop ───────────────────────────────────────────────────────────

    def _start_camera(self):
        """Inicia la cámara y los videos en un hilo de fondo para evitar congelar la UI."""
        self._running = True
        self._timer = QTimer()
        self._timer.timeout.connect(self._capture_frame)
        self._timer.start(33)   # ~30 FPS

        # Lanzar inicialización pesada en segundo plano
        threading.Thread(target=self._init_hardware_async, daemon=True).start()

    def _init_hardware_async(self):
        """Apertura real de cámara y carga de videos (corre en background)."""
        try:
            # 1. Abrir Cámara
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1080)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1920)
                self._cap = cap
                print("[Camera] Hardware ready")
            
            # 2. Iniciar Overlays
            VideoOverlayEngine.start_experience(self._players, WIN_W, WIN_H)
        except Exception as e:
            print(f"[Camera] Async init error: {e}")

    def _capture_frame(self):
        if not self._running or self._cap is None or not self._cap.isOpened():
            # Si la cámara aún no abre o falló, mostrar fondo negro
            return

        ret, frame = self._cap.read()
        if not ret:
            return

        # 1. Resize para el preview de la ventana (Rápido)
        preview_frame = cv2.resize(frame, (WIN_W, WIN_H))

        if self._capture_pending:
            self._capture_pending = False
            # CAPTURA RAW: Guardamos la foto limpia de la cámara para procesar después
            self._photo_frame = cv2.resize(frame, (REF_W, REF_H))
            preview_frame = VideoOverlayEngine.apply_all(preview_frame)
        else:
            preview_frame = VideoOverlayEngine.apply_all(preview_frame)

        self._update_canvas(preview_frame)

    def _update_canvas(self, frame: np.ndarray):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img  = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self._canvas.setPixmap(QPixmap.fromImage(qt_img))

    # ── Countdown ─────────────────────────────────────────────────────────────

    def _start_countdown(self):
        if self._counting:
            return
        self._counting       = True
        self._countdown_left = COUNTDOWN_SEC
        self._btn_capture.hide()
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
            self._btn_capture.show()
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
        self.app.show_photo_view(path, self._players)

    # ── Navigation / cleanup ──────────────────────────────────────────────────

    def _on_back(self):
        self.app.show_player_selection()

    def on_destroy(self):
        self._running = False
        if hasattr(self, "_timer"):
            self._timer.stop()
        if hasattr(self, "_countdown_timer"):
            self._countdown_timer.stop()
        if self._cap:
            self._cap.release()
        VideoOverlayEngine.stop_all()
