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
    """Maneja la reproducción de frames pre-decodificados en RAM."""

    def __init__(self):
        self.current_fg_pre: np.ndarray | None = None
        self.current_inv_alpha: np.ndarray | None = None
        self.lock          = threading.Lock()
        self.running       = False
        self.ready         = False
        self.finished      = False
        self.looping       = False
        self.paused        = False
        self._thread: threading.Thread | None = None
        self.config        = (0, 0, 540, 960)
        self.idx           = 0

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
            self.current_fg_pre = None
            self.current_inv_alpha = None
            self.ready = False

    def _loop(self, path: str):
        if path in VideoOverlayEngine._video_cache:
            frames_data, fps = VideoOverlayEngine._video_cache[path]
        else:
            # Fallback a decodificación normal si no está en cache
            print(f"[!] Warning: {path} not in RAM cache.")
            frames_meta, fps = parse_mov(path)
            frames_data = []
            with open(path, 'rb') as f:
                for offset, size in frames_meta:
                    f.seek(offset)
                    buf = f.read(size)
                    arr = np.frombuffer(buf, dtype=np.uint8)
                    img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
                    if img is not None: frames_data.append(img)
        
        if not frames_data:
            self.running = False
            return

        frame_dur = 1.0 / fps
        self.idx = 0
        
        while self.running:
            if self.paused and self.ready:
                time.sleep(0.05)
                continue

            t0 = time.perf_counter()

            # OBTENER FRAME DE LA RAM (VELOCIDAD RAYO)
            if self.idx < len(frames_data):
                decoded = frames_data[self.idx]
                
                # Pre-resize si es necesario
                x, y, w, h = self.config
                if w > 0 and h > 0 and (decoded.shape[1] != w or decoded.shape[0] != h):
                    decoded = cv2.resize(decoded, (w, h), interpolation=cv2.INTER_LINEAR)
                
                # Optimización de mezcla
                alpha  = decoded[:, :, 3:4].astype(np.uint16)
                fg_rgb = decoded[:, :, :3].astype(np.uint16)
                fg_pre    = fg_rgb * alpha
                inv_alpha = 255 - alpha
                
                with self.lock:
                    self.current_fg_pre    = fg_pre
                    self.current_inv_alpha = inv_alpha
                    self.ready = True

            self.idx += 1
            if self.idx >= len(frames_data):
                if self.looping:
                    self.idx = 0
                else:
                    self.finished = True
                    while self.running and self.finished:
                        time.sleep(0.1)
                        if not self.finished: break
                    if not self.running: break

            elapsed = time.perf_counter() - t0
            sleep_t = frame_dur - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)

    def _set_placeholder_frame(self):
        placeholder = np.ones((480, 640, 4), dtype=np.uint8) * 100
        with self.lock:
            self.ready = True


class VideoOverlayEngine:
    """Maneja la caché agresiva en RAM para los videos."""

    _players: list[VideoPlayer] = [VideoPlayer() for _ in range(4)]
    _video_cache: dict[str, tuple] = {} # Path -> (list[np.ndarray], fps)
    _active_slots: list[int] = []

    @classmethod
    def preload_all_videos(cls, player_data_list):
        """Decodifica todos los videos a la RAM al inicio."""
        import os
        for p in player_data_list:
            path = f"assets/videos/{p['video_name']}"
            if path not in cls._video_cache and os.path.exists(path):
                print(f"[Engine] Decoding {path} to RAM cache...")
                frames_meta, fps = parse_mov(path)
                decoded_frames = []
                with open(path, 'rb') as f:
                    for offset, size in frames_meta:
                        f.seek(offset)
                        buf = f.read(size)
                        arr = np.frombuffer(buf, dtype=np.uint8)
                        img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
                        if img is not None:
                            decoded_frames.append(img)
                cls._video_cache[path] = (decoded_frames, fps)
                print(f"[Engine] {path} cached: {len(decoded_frames)} frames.")

    @classmethod
    def set_paused(cls, paused: bool):
        for vp in cls._players:
            vp.paused = paused

    @classmethod
    def warm_up(cls, player_data_list, screen_w, screen_h):
        cls.preload_all_videos(player_data_list)
        for p_data in player_data_list:
            slot = p_data.get("slot", 0)
            vp = cls._players[slot]
            from config import REF_W, REF_H
            x = int(p_data['x'] * screen_w / REF_W)
            y = int(p_data['y'] * screen_h / REF_H)
            w = int(p_data['w'] * screen_w / REF_W)
            h = int(p_data['h'] * screen_h / REF_H)
            vp.config = (x, y, w, h)
            vp.paused = True
            path = f"assets/videos/{p_data['video_name']}"
            vp.start(path, looping=False)

    @classmethod
    def start_experience(cls, player_list, screen_w, screen_h, paused=False):
        cls._active_slots = [p.slot for p in player_list]
        for slot in cls._active_slots:
            vp = cls._players[slot]
            vp.idx = 0
            vp.finished = False
            vp.paused = paused

    @classmethod
    def apply_all(cls, frame_bgr: np.ndarray) -> np.ndarray:
        for slot in [0, 2, 1, 3]:
            if slot not in cls._active_slots: continue
            vp = cls._players[slot]
            if not vp.ready: continue
            with vp.lock:
                fg_pre = vp.current_fg_pre
                inv_alpha_mask = vp.current_inv_alpha
            if fg_pre is None or inv_alpha_mask is None: continue
            x, y, w, h = vp.config
            fh, fw = frame_bgr.shape[:2]
            x1, y1 = max(x, 0), max(y, 0)
            x2, y2 = min(x + w, fw), min(y + h, fh)
            if x1 >= x2 or y1 >= y2: continue
            try:
                ox1, oy1 = x1 - x, y1 - y
                ox2, oy2 = x2 - x, y2 - y
                f_roi = fg_pre[oy1:oy2, ox1:ox2]
                i_roi = inv_alpha_mask[oy1:oy2, ox1:ox2]
                b_roi = frame_bgr[y1:y2, x1:x2]
                tmp = b_roi.astype(np.uint32) * i_roi + f_roi
                frame_bgr[y1:y2, x1:x2] = (tmp // 255).astype(np.uint8)
            except: pass
        return frame_bgr

    @classmethod
    def stop_all(cls):
        for vp in cls._players: vp.stop()

    @classmethod
    def all_finished(cls) -> bool:
        return all(vp.finished or not vp.running for vp in cls._players)
