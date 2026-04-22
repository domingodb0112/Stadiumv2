import threading
import time as _t
import cv2
import numpy as np
import os

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QWidget,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont

from screens.base_screen import BaseScreen
from config import BG, ACCENT, TEXT_WHITE, TEXT_DIM, SIMULATION_MS, PHOTOS_DIR, REF_W, REF_H, OUTPUT_DIR
from network_client import NetworkClient
from segmentation_engine import SegmentationEngine
from theme import BG_PRIMARY, INK_900, GREEN_600, GREEN_500, FONT_SANS, INK_400, BG_CARD
from ui_components import TopBar, GradientBar

class PreProcessingEngine:
    """Caché global para procesar la segmentación en segundo plano."""
    _result_cache = {} # photo_path -> img_segmentada (4 canales)

    @classmethod
    def start_segmentation(cls, photo_path):
        def _task():
            if photo_path in cls._result_cache: return
            try:
                img = cv2.imread(photo_path)
                if img is None: return
                # Redimensionar a referencia para segmentar
                img = cv2.resize(img, (REF_W, REF_H))
                
                engine = SegmentationEngine()
                mask = engine.process(img)
                
                # Crear imagen de 4 canales (cutout con transparencia)
                h, w = img.shape[:2]
                segmented = np.zeros((h, w, 4), dtype=np.uint8)
                segmented[:, :, :3] = img
                segmented[:, :, 3] = mask
                
                cls._result_cache[photo_path] = segmented
                print(f"[PreProcess] Segmentation done for {photo_path}")
            except Exception as e:
                print(f"[PreProcess] Error: {e}")
        
        threading.Thread(target=_task, daemon=True).start()

    @classmethod
    def get_result(cls, photo_path):
        return cls._result_cache.get(photo_path)

def _get_player_last_frame(player):
    """Obtiene el último frame de un video MOV usando el parser interno."""
    from engine.mov_parser import parse_mov
    path = str(player.video_path)
    frames, _ = parse_mov(path)
    if not frames:
        return None
    
    offset, size = frames[-1]
    try:
        with open(path, 'rb') as f:
            f.seek(offset)
            buf = f.read(size)
            arr = np.frombuffer(buf, dtype=np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    except:
        return None

def _overlay_img(bg, fg, x, y, w, h):
    """Mezcla una imagen FG sobre BG en x,y con tamaño w,h (soporta alfa)."""
    if fg is None: return bg
    try:
        fg_scaled = cv2.resize(fg, (w, h))
        fh, fw = bg.shape[:2]
        
        x1, y1 = max(x, 0), max(y, 0)
        x2, y2 = min(x + w, fw), min(y + h, fh)
        if x1 >= x2 or y1 >= y2: return bg

        oy1, oy2 = y1 - y, y2 - y
        ox1, ox2 = x1 - x, x2 - x
        
        fg_roi = fg_scaled[oy1:oy2, ox1:ox2]
        bg_roi = bg[y1:y2, x1:x2].astype(np.float32)

        if fg_roi.shape[2] == 4:
            alpha = fg_roi[:, :, 3:4].astype(np.float32) / 255.0
            fg_rgb = fg_roi[:, :, :3].astype(np.float32)
            blended = (fg_rgb * alpha) + (bg_roi * (1.0 - alpha))
            bg[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)
        else:
            bg[y1:y2, x1:x2] = fg_roi[:, :, :3]
    except:
        pass
    return bg

class ProcessingWorker(QObject):
    finished = pyqtSignal(str, str) # Emite: (path_foto_final, qr_base64)
    error = pyqtSignal(str)

    def __init__(self, photo_path: str, players: list):
        super().__init__()
        self._photo_path = photo_path
        self._players = players

    def run(self):
        try:
            bg = np.zeros((REF_H, REF_W, 3), dtype=np.uint8)
            cancha_path = PHOTOS_DIR / "cancha.png"
            if cancha_path.exists():
                cancha_img = cv2.imread(str(cancha_path))
                if cancha_img is not None:
                    bg = cv2.resize(cancha_img, (REF_W, REF_H))
            else:
                bg[:] = (0, 150, 0)

            # Procesar Usuario (CON OPTIMIZACIÓN DE CACHÉ)
            user_segmented = PreProcessingEngine.get_result(self._photo_path)
            
            if user_segmented is None:
                user_raw = cv2.imread(self._photo_path)
                if user_raw is not None:
                    user_raw = cv2.resize(user_raw, (REF_W, REF_H))
                    engine = SegmentationEngine()
                    mask = engine.process(user_raw)
                    user_segmented = np.zeros((REF_H, REF_W, 4), dtype=np.uint8)
                    user_segmented[:, :, :3] = user_raw
                    user_segmented[:, :, 3] = mask
            
            if user_segmented is not None:
                target_h = 1728
                h_orig, w_orig = user_segmented.shape[:2]
                ratio = target_h / h_orig
                target_w = int(w_orig * ratio)
                user_final = cv2.resize(user_segmented, (target_w, target_h))
                
                x_pos = (REF_W - target_w) // 2
                y_pos = REF_H - target_h
                bg = _overlay_img(bg, user_final, x_pos, y_pos, target_w, target_h)

            # 3. Superponer Jugadores
            slots_order = {0: 0, 2: 1, 1: 2, 3: 3}
            sorted_players = sorted(self._players, key=lambda p: slots_order.get(getattr(p, 'slot', 0), 99))
            
            for player in sorted_players:
                p_img = _get_player_last_frame(player)
                if p_img is not None:
                    bg = _overlay_img(bg, p_img, player.x, player.y, player.w, player.h)

            final_path = str(OUTPUT_DIR / f"result_{int(_t.time())}.jpg")
            cv2.imwrite(final_path, bg, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # 5. SUBIR AL SERVIDOR PARA OBTENER QR
            print(f"[Network] Uploading {final_path} to server...")
            success, qr_data, net_err = NetworkClient.upload_photo(final_path)
            
            self.finished.emit(final_path, qr_data if success else "")

        except Exception as e:
            self.error.emit(str(e))

class SimulationScreen(BaseScreen):
    def __init__(self, app, photo_path, players, **kwargs):
        super().__init__(app, **kwargs)
        self._photo_path = photo_path
        self._players = players
        self._build_ui()
        self._start_processing()

    def _build_ui(self):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top Bar ──────────────────────────────────────────────────────────
        self._top_bar = TopBar()
        self._top_bar.set_brand_mode()
        layout.addWidget(self._top_bar)

        # ── Main Content ──────────────────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 60, 40, 60)
        content_layout.setAlignment(Qt.AlignCenter)

        # Subtitle (Small green text)
        self._subtitle = QLabel("PROCESANDO TU FOTO CON LA IA")
        self._subtitle.setFont(QFont(FONT_SANS, 10, QFont.Bold))
        self._subtitle.setStyleSheet(f"color: {GREEN_600}; letter-spacing: 2px;")
        self._subtitle.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self._subtitle)

        # Main Title
        self._title = QLabel("¡SALIENDO\nAL CAMPO!")
        self._title.setFont(QFont(FONT_SANS, 38, QFont.Black))
        self._title.setStyleSheet(f"color: {INK_900};")
        self._title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self._title)

        content_layout.addSpacing(40)

        # Progress Container
        self._progress_container = QWidget()
        self._progress_container.setFixedWidth(400)
        self._progress_container.setStyleSheet(f"background: {BG_CARD}; border-radius: 20px;")
        prog_layout = QVBoxLayout(self._progress_container)
        prog_layout.setContentsMargins(24, 24, 24, 24)

        self._progress = QProgressBar()
        self._progress.setFixedHeight(8)
        self._progress.setTextVisible(False)
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #E8EAE6;
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {GREEN_500};
                border-radius: 4px;
            }}
        """)
        prog_layout.addWidget(self._progress)

        self._status_lbl = QLabel("0%")
        self._status_lbl.setFont(QFont(FONT_SANS, 11, QFont.Bold))
        self._status_lbl.setStyleSheet(f"color: {INK_900};")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        prog_layout.addWidget(self._status_lbl)

        content_layout.addWidget(self._progress_container, alignment=Qt.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(content)
        layout.addStretch()

        # ── Bottom Gradient ───────────────────────────────────────────────────
        self._gradient_bar = GradientBar()
        layout.addWidget(self._gradient_bar)

    def _start_processing(self):
        self._worker = ProcessingWorker(self._photo_path, self._players)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._thread.start()

        self._progress_val = 0
        self._prog_timer = QTimer()
        self._prog_timer.timeout.connect(self._update_progress)
        self._prog_timer.start(50)

    def _update_progress(self):
        if self._progress_val < 95:
            self._progress_val += 1
            self._progress.setValue(self._progress_val)
            self._status_lbl.setText(f"{self._progress_val}%")

    def _on_finished(self, result_path, qr_base64):
        self._progress.setValue(100)
        self._status_lbl.setText("100%")
        QTimer.singleShot(500, lambda: self.app.show_final(result_path, qr_base64))

    def _on_error(self, err_msg):
        print(f"Error en procesamiento: {err_msg}")
        self.app.show_welcome()

    def on_destroy(self):
        """Limpieza de hilos antes de cerrar la pantalla."""
        if hasattr(self, "_thread") and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        h = self.height()
        w = self.width()

        if hasattr(self, '_top_bar'):
            self._top_bar.scale_to(h)

        self._title.setFont(QFont(FONT_SANS, max(24, int(h * 0.045)), QFont.Black))
        self._subtitle.setFont(QFont(FONT_SANS, max(9, int(h * 0.010)), QFont.Bold))
        self._progress_container.setFixedWidth(min(500, int(w * 0.8)))
