"""
Camera preview screen for PyQt5 — optimized for high speed.
"""
import cv2
import numpy as np
import threading
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QGridLayout, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QImage, QCursor

from config import (
    BG, TEXT_WHITE, ACCENT,
    WIN_W, WIN_H, COUNTDOWN_SEC, REF_W, REF_H, OUTPUT_DIR
)
from screens.base_screen import BaseScreen
from engine.video_overlay import VideoOverlayEngine


class CameraPreviewScreen(BaseScreen):
    """Pantalla de cámara en vivo con carga asíncrona para evitar lag."""

    def __init__(self, app, players, cap=None, **kwargs):
        super().__init__(app, **kwargs)
        self._players        = players
        self._cap            = cap # Usar cámara inyectada si existe
        self._running        = False
        self._countdown_left = 0
        self._counting       = False
        self._photo_frame    = None
        self._capture_pending = False
        # Los jugadores ya están cargados y pausados desde la pantalla de carga.
        # No hace falta activarlos/desactivarlos, solo darles 'Play'.

        self._build_ui()
        self._start_camera()
        
        # Iniciar reproducción tras 2 segundos (Antes eran 3)
        QTimer.singleShot(2000, self._start_playback)
        
    def _start_playback(self):
        VideoOverlayEngine.set_paused(False)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Viewport container (centered with margins)
        self._viewport = QWidget()
        self._viewport.setStyleSheet("background-color: transparent;")
        
        # Grid layout allows stacking widgets on top of each other in the same cell
        self._view_layout = QGridLayout(self._viewport)
        self._view_layout.setContentsMargins(0, 0, 0, 0)
        self._view_layout.setSpacing(0)

        # Video canvas (bottom layer)
        self._canvas = QLabel()
        self._canvas.setAlignment(Qt.AlignCenter)
        self._canvas.setStyleSheet("background-color: #000; border: none;") 
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._view_layout.addWidget(self._canvas, 0, 0)
        
        # Countdown label (overlay layer)
        self._lbl_countdown = QLabel("")
        self._lbl_countdown.setFont(QFont("Arial Black", 180, QFont.Bold))
        self._lbl_countdown.setStyleSheet(
            "QLabel { color:white; background-color:transparent; }"
        )
        self._lbl_countdown.setAlignment(Qt.AlignCenter)
        self._lbl_countdown.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._lbl_countdown.hide()
        self._view_layout.addWidget(self._lbl_countdown, 0, 0)

        # Main layout con espaciado balanceado
        main_layout.addSpacing(100)
        main_layout.addWidget(self._viewport, 1) 
        main_layout.addSpacing(80)

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

        # (Deleted duplicate countdown label creation)

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

        main_layout.addLayout(capture_row)
        self.setLayout(main_layout)

    # ── Camera loop ───────────────────────────────────────────────────────────

    def _start_camera(self):
        """Inicia la cámara y los videos en un hilo de fondo."""
        self._running = True
        self._timer = QTimer()
        self._timer.timeout.connect(self._capture_frame)
        self._timer.start(33)   # ~30 FPS

        if self._cap is None:
            # Solo si no se inyectó, abrimos en segundo plano
            threading.Thread(target=self._init_hardware_async, daemon=True).start()
        else:
            # Si ya tenemos cámara, los videos ya están cargados (por LoadingScreen)
            # Solo nos aseguramos de que el motor sepa que estamos en preview
            pass

    def _init_hardware_async(self):
        """Apertura fallback de cámara."""
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

        # ── CENTER CROP 9:16 (1080x1920) ──────────────────────────────────
        # La cámara suele dar 16:9 (horiz). Recortamos el centro para vertical.
        h, w = frame.shape[:2]
        target_aspect = 9 / 16
        current_aspect = w / h

        if current_aspect > target_aspect:
            # Demasiado ancho (típico), recortamos lados
            new_w = int(h * target_aspect)
            x_offset = (w - new_w) // 2
            frame = frame[:, x_offset : x_offset + new_w]
        elif current_aspect < target_aspect:
            # Demasiado alto, recortamos arriba/abajo
            new_h = int(w / target_aspect)
            y_offset = (h - new_h) // 2
            frame = frame[y_offset : y_offset + new_h, :]

        # Ya tenemos proporción 9:16 real.
        # INTERNAL SCALING a 720x1280 para FPS estables.
        PREVIEW_W = 720
        PREVIEW_H = 1280
        
        # Sincronizar motor de video con la resolución reducida
        if not hasattr(self, "_last_res") or self._last_res != (PREVIEW_W, PREVIEW_H):
            VideoOverlayEngine.start_experience(self._players, PREVIEW_W, PREVIEW_H)
            self._last_res = (PREVIEW_W, PREVIEW_H)

        preview_frame = cv2.resize(frame, (PREVIEW_W, PREVIEW_H))

        if self._capture_pending:
            self._capture_pending = False
            # CAPTURA RAW: Guardamos la foto limpia de la cámara para procesar después
            self._photo_frame = cv2.resize(frame, (REF_W, REF_H))
            preview_frame = VideoOverlayEngine.apply_all(preview_frame)
        else:
            # Aplicar overlays (estarán pausados o en play según el timer)
            preview_frame = VideoOverlayEngine.apply_all(preview_frame)

        self._update_canvas(preview_frame)

    def _update_canvas(self, frame: np.ndarray):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img  = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        # Escalar al tamaño actual del canvas manteniendo aspecto
        scaled_pixmap = pixmap.scaled(
            self._canvas.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self._canvas.setPixmap(scaled_pixmap)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)

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
