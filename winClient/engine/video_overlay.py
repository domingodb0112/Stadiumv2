"""
video_overlay.py
Traducción del C++ VideoPlayer + applyOverlay a Python/NumPy.
Corre un hilo por jugador que decodifica frames del .mov y los almacena.
El hilo de cámara llama a apply_all() para mezclar todos los overlays activos.
"""
import threading
import time
import numpy as np
import cv2
from engine.mov_parser import parse_mov


class VideoPlayer:
    """Decodifica frames de un .mov en un hilo de fondo."""

    def __init__(self):
        self.current_frame: np.ndarray | None = None  # BGRA
        self.lock          = threading.Lock()
        self.running       = False
        self.ready         = False
        self.finished      = False
        self.looping       = False
        self._thread: threading.Thread | None = None
        # (x, y, w, h) en coordenadas de pantalla
        self.config        = (0, 0, 540, 960)

    def start(self, path: str, looping: bool = False):
        self.stop()
        self.looping  = looping
        self.finished = False
        self.ready    = False
        self.running  = True
        self._thread  = threading.Thread(target=self._loop, args=(path,), daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        with self.lock:
            self.current_frame = None
            self.ready = False

    def _loop(self, path: str):
        import os
        if not os.path.exists(path):
            print(f"[!] Video not found: {path}. Using placeholder.")
            self._set_placeholder_frame()
            self.running = False
            return

        frames, fps = parse_mov(path)
        if not frames:
            print(f"[!] Could not parse frames from {path}. Using placeholder.")
            self._set_placeholder_frame()
            self.running = False
            return

        frame_dur = 1.0 / fps
        idx = 0
        try:
            with open(path, 'rb') as f:
                while self.running:
                    t0 = time.perf_counter()

                    offset, size = frames[idx]
                    f.seek(offset)
                    buf = f.read(size)

                    arr     = np.frombuffer(buf, dtype=np.uint8)
                    decoded = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)

                    if decoded is not None and decoded.ndim == 3 and decoded.shape[2] == 4:
                        # cv2.imdecode ya retorna BGRA para PNG con alfa (no necesita conversión)
                        with self.lock:
                            self.current_frame = decoded
                            self.ready = True

                    idx += 1
                    if idx >= len(frames):
                        if self.looping:
                            idx = 0
                        else:
                            self.finished = True
                            # Congelar último frame hasta que nos detengan
                            while self.running and self.finished:
                                time.sleep(0.1)
                            if not self.running:
                                break
                            idx = 0

                    elapsed = time.perf_counter() - t0
                    sleep_t = frame_dur - elapsed
                    if sleep_t > 0:
                        time.sleep(sleep_t)
        except Exception as e:
            print(f"[!] Error reading video file: {e}")
            self._set_placeholder_frame()

        self.running = False

    def _set_placeholder_frame(self):
        """Crea un frame placeholder (gris con transparencia)."""
        placeholder = np.ones((480, 640, 4), dtype=np.uint8) * 100
        with self.lock:
            self.current_frame = placeholder
            self.ready = True


class VideoOverlayEngine:
    """Maneja hasta 4 VideoPlayer (un slot por jugador fijo)."""

    _players: list[VideoPlayer] = [VideoPlayer() for _ in range(4)]

    @classmethod
    def start_experience(cls, player_list, screen_w: int, screen_h: int):
        """
        player_list: lista de objetos Player (models.player_roster)
        screen_w/h : dimensiones reales de la pantalla de renderizado
        """
        for player in player_list:
            slot = player.slot
            vp   = cls._players[slot]

            # Escalar coordenadas de referencia 1080×1920 → pantalla real
            from config import REF_W, REF_H
            x = int(player.x * screen_w / REF_W)
            y = int(player.y * screen_h / REF_H)
            w = int(player.w * screen_w / REF_W)
            h = int(player.h * screen_h / REF_H)
            vp.config = (x, y, w, h)

            video_path = str(player.video_path)
            vp.start(video_path, looping=False)

    @classmethod
    def apply_all(cls, frame_bgr: np.ndarray) -> np.ndarray:
        """Mezcla todos los overlays activos sobre frame_bgr (in-place)."""
        for vp in cls._players:
            if not vp.ready:
                continue
            with vp.lock:
                fg = vp.current_frame
                if fg is None:
                    continue
                fg = fg.copy()

            x, y, w, h = vp.config
            if w <= 0 or h <= 0:
                continue

            fh, fw = frame_bgr.shape[:2]
            # Recortar para no salir de pantalla
            x1, y1 = max(x, 0), max(y, 0)
            x2, y2 = min(x + w, fw), min(y + h, fh)
            if x1 >= x2 or y1 >= y2:
                continue

            try:
                fg_scaled = cv2.resize(fg, (w, h), interpolation=cv2.INTER_LINEAR)

                # Región visible en pantalla
                vis_x1, vis_y1 = x1, y1
                vis_x2, vis_y2 = x2, y2

                # Región correspondiente en el overlay redimensionado (0,0 = punto x,y del overlay)
                overlay_x1 = vis_x1 - x
                overlay_y1 = vis_y1 - y
                overlay_x2 = vis_x2 - x
                overlay_y2 = vis_y2 - y

                # Extraer ROIs del mismo tamaño
                fg_roi = fg_scaled[overlay_y1:overlay_y2, overlay_x1:overlay_x2]
                bg_roi = frame_bgr[vis_y1:vis_y2, vis_x1:vis_x2].astype(np.float32)

                if fg_roi.shape[0] > 0 and fg_roi.shape[1] > 0:
                    alpha    = fg_roi[:, :, 3:4] / 255.0
                    fg_bgr   = fg_roi[:, :, :3].astype(np.float32)
                    blended  = fg_bgr * alpha + bg_roi * (1.0 - alpha)
                    frame_bgr[vis_y1:vis_y2, vis_x1:vis_x2] = np.clip(blended, 0, 255).astype(np.uint8)
            except Exception as e:
                pass

        return frame_bgr

    @classmethod
    def stop_all(cls):
        for vp in cls._players:
            vp.stop()

    @classmethod
    def all_finished(cls) -> bool:
        return all(vp.finished or not vp.running for vp in cls._players)
