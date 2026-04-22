import threading
import time as _t
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QWidget,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont

from screens.base_screen import BaseScreen
from config import BG, ACCENT, TEXT_WHITE, TEXT_DIM, SIMULATION_MS, PHOTOS_DIR, REF_W, REF_H, OUTPUT_DIR
from network_client import NetworkClient

from segmentation_engine import SegmentationEngine

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

            # 3. Superponer Jugadores (ORDEN DE CAPA: 0, 2 atrás -> 1, 3 adelante)
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
            
            if success:
                print("[Network] QR received successfully")
                self.finished.emit(final_path, qr_data)
            else:
                print(f"[Network] Upload failed: {net_err}")
                # Si falla el internet, mostramos la foto sin QR
                self.finished.emit(final_path, "")

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
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setContentsMargins(40, 0, 40, 0)

        title = QLabel("¡SALIENDO\nAL CAMPO!")
        title.setFont(QFont("Arial Black", 80, QFont.Bold))
        title.setStyleSheet(f"color: {ACCENT}; background-color: transparent;")
        title.setAlignment(Qt.AlignCenter)
        center_layout.addSpacing(100)
        center_layout.addWidget(title)

        subtitle = QLabel("Tus ídolos están saltando al césped…")
        subtitle.setFont(QFont("Arial", 28))
        subtitle.setStyleSheet(f"color: {TEXT_WHITE}; background-color: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        center_layout.addSpacing(40)
        center_layout.addWidget(subtitle)

        center_layout.addSpacing(40)
        self._progress = QProgressBar()
        self._progress.setMaximum(100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(12)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background-color: {TEXT_DIM}; border: none; border-radius: 6px; }}
            QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 6px; }}
        """)
        center_layout.addWidget(self._progress)
        layout.addWidget(center_widget)

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

    def _on_finished(self, result_path, qr_base64):
        self._progress.setValue(100)
        QTimer.singleShot(500, lambda: self.app.show_final(result_path, qr_base64))

    def _on_error(self, err_msg):
        print(f"Error en procesamiento: {err_msg}")
        self.app.show_welcome()

    def on_destroy(self):
        """Limpieza de hilos antes de cerrar la pantalla."""
        if hasattr(self, "_thread") and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000) # Esperar hasta 2 segundos
