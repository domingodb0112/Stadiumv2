"""
video_overlay.py - HYPER OPTIMIZED FOR 32GB RAM & LOW CPU
Uses dual-cache (Preview/Final) to eliminate real-time resizing.
"""
import threading
import time
import numpy as np
import cv2
from engine.mov_parser import parse_mov


class VideoPlayer:
    """Maneja la reproducción de frames pre-calculados en DUAL-CACHE (Preview/Final)."""

    def __init__(self):
        # Cache para el Preview (540p)
        self.curr_fg_pre_pv: np.ndarray | None = None
        self.curr_inv_pv: np.ndarray | None = None
        
        # Cache para la Foto Final (1080p)
        self.curr_fg_pre_final: np.ndarray | None = None
        self.curr_inv_final: np.ndarray | None = None

        self.lock          = threading.Lock()
        self.running       = False
        self.ready         = False
        self.finished      = False
        self.looping       = False
        self.paused        = False
        self._thread: threading.Thread | None = None
        self.config_pv     = (0, 0, 0, 0)
        self.config_final  = (0, 0, 0, 0)
        self.idx           = 0
        self.path          = ""

    def start(self, path: str, looping: bool = False):
        self.stop()
        self.path     = path
        self.looping  = looping
        self.finished = False
        self.ready    = False
        self.running  = True
        self._thread  = threading.Thread(target=self._loop, args=(path,), daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._thread = None

    def _loop(self, path: str):
        if path not in VideoOverlayEngine._video_cache:
            self.running = False
            return
            
        dual_cache_data, fps = VideoOverlayEngine._video_cache[path]
        frame_dur = 1.0 / fps
        self.idx = 0
        
        while self.running:
            if self.paused and self.ready:
                time.sleep(0.01)
                continue

            t0 = time.perf_counter()

            if self.idx < len(dual_cache_data):
                # Extraer ambos sets de datos (Preview y Final)
                pv_data, final_data = dual_cache_data[self.idx]
                
                with self.lock:
                    self.curr_fg_pre_pv, self.curr_inv_pv = pv_data
                    self.curr_fg_pre_final, self.curr_inv_final = final_data
                    self.ready = True

            self.idx += 1
            if self.idx >= len(dual_cache_data):
                if self.looping:
                    self.idx = 0
                else:
                    self.finished = True
                    while self.running and self.finished:
                        time.sleep(0.05)
                        if not self.finished: break
                    if not self.running: break

            elapsed = time.perf_counter() - t0
            sleep_t = frame_dur - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)


class VideoOverlayEngine:
    """Motor con Súper-Caché que elimina el uso de Disco y CPU durante la sesión."""

    _players: list[VideoPlayer] = [VideoPlayer() for _ in range(4)]
    _video_cache: dict[str, tuple] = {} 
    _img_cache: dict[str, np.ndarray] = {} # Caché para fondos y logos
    _active_slots: list[int] = []

    @classmethod
    def get_cached_image(cls, path: str):
        """Devuelve una imagen desde la RAM usando rutas normalizadas."""
        import os
        from pathlib import Path
        norm_path = str(Path(path).resolve())
        if norm_path not in cls._img_cache:
            print(f"[Engine] Loading image to RAM: {norm_path}")
            img = cv2.imread(norm_path, cv2.IMREAD_UNCHANGED)
            if img is not None:
                cls._img_cache[norm_path] = img
            else:
                print(f"[!] Engine Error: Could not read image at {norm_path}")
        return cls._img_cache.get(norm_path)

    @classmethod
    def preload_all_videos(cls, player_data_list):
        """Pre-calcula versiones duales para evitar cualquier resize en tiempo real."""
        import os
        from config import REF_W, REF_H
        # Escala para el preview (540p - ULTRA FLUIDO)
        PV_SCALE_W = 540 / REF_W
        PV_SCALE_H = 960 / REF_H

        for p in player_data_list:
            path = f"assets/videos/{p['video_name']}"
            from pathlib import Path
            abs_path = str(Path(path).absolute())
            
            if path not in cls._video_cache and os.path.exists(abs_path):
                print(f"[Engine] HYPER-CACHING (Dual-Scale) from: {abs_path}")
                frames_meta, fps = parse_mov(abs_path)
                
                # Tamaño Final (1080p)
                fw, fh = p['w'], p['h']
                # Tamaño Preview (720p)
                pw, ph = int(fw * PV_SCALE_W), int(fh * PV_SCALE_H)
                
                dual_data = []
                with open(abs_path, 'rb') as f:
                    for offset, size in frames_meta:
                        f.seek(offset)
                        buf = f.read(size)
                        arr = np.frombuffer(buf, dtype=np.uint8)
                        img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
                        
                        if img is not None:
                            # --- PREPARAR VERSIÓN PREVIEW (720p) ---
                            img_pv = cv2.resize(img, (pw, ph), interpolation=cv2.INTER_LINEAR)
                            a_pv  = img_pv[:, :, 3:4].astype(np.uint16)
                            rgb_pv = img_pv[:, :, :3].astype(np.uint16)
                            pv_entry = ((rgb_pv * a_pv).astype(np.uint32), (255 - a_pv).astype(np.uint32))
                            
                            # --- PREPARAR VERSIÓN FINAL (1080p) ---
                            img_final = cv2.resize(img, (fw, fh), interpolation=cv2.INTER_LINEAR)
                            a_f  = img_final[:, :, 3:4].astype(np.uint16)
                            rgb_f = img_final[:, :, :3].astype(np.uint16)
                            f_entry = ((rgb_f * a_f).astype(np.uint32), (255 - a_f).astype(np.uint32))
                            
                            dual_data.append((pv_entry, f_entry))
                
                cls._video_cache[path] = (dual_data, fps)
                print(f"[Engine] {path} dual-cached.")

    @classmethod
    def warm_up(cls, player_data_list, screen_w, screen_h):
        cls.preload_all_videos(player_data_list)
        # Pre-cargar fondos comunes usando ruta robusta
        from config import PHOTOS_DIR
        cls.get_cached_image(str(PHOTOS_DIR / "cancha.png"))
        
        for p_data in player_data_list:
            slot = p_data.get("slot", 0)
            vp = cls._players[slot]
            from config import REF_W, REF_H
            # Configurar ambas escalas
            vp.config_pv = (
                int(p_data['x'] * 540 / REF_W),
                int(p_data['y'] * 960 / REF_H),
                int(p_data['w'] * 540 / REF_W),
                int(p_data['h'] * 960 / REF_H)
            )
            vp.config_final = (p_data['x'], p_data['y'], p_data['w'], p_data['h'])
            
            vp.paused = True
            path = f"assets/videos/{p_data['video_name']}"
            vp.start(path, looping=False)

    @classmethod
    def start_experience(cls, player_list, screen_w, screen_h, paused=False):
        # Soportar tanto diccionarios como objetos para los jugadores
        cls._active_slots = []
        for p in player_list:
            slot = p.get('slot') if isinstance(p, dict) else getattr(p, 'slot', None)
            if slot is not None:
                cls._active_slots.append(slot)
                
        for slot in cls._active_slots:
            vp = cls._players[slot]
            vp.idx = 0
            vp.finished = False
            vp.paused = paused

    @classmethod
    def apply_all(cls, frame_bgr: np.ndarray, is_final=False) -> np.ndarray:
        """Mezcla ultra veloz. En modo Final, usa la RAM directamente sin depender de hilos."""
        fh, fw = frame_bgr.shape[:2]
        
        for slot in [0, 2, 1, 3]:
            if slot not in cls._active_slots: continue
            vp = cls._players[slot]
            
            fg_pre, inv_a = None, None
            x, y, w, h = 0, 0, 0, 0
            
            if is_final:
                # USAR EL ÚLTIMO FRAME (POSE FINAL) PARA LA FOTO
                if vp.path in cls._video_cache:
                    dual_data, _ = cls._video_cache[vp.path]
                    # Tomar el ÚLTIMO frame del cache
                    last_idx = len(dual_data) - 1
                    _, f_entry = dual_data[last_idx]
                    fg_pre, inv_a = f_entry
                    x, y, w, h = vp.config_final
            else:
                # Modo Preview: Usar lo que el hilo tenga listo
                if vp.ready:
                    with vp.lock:
                        fg_pre, inv_a = vp.curr_fg_pre_pv, vp.curr_inv_pv
                        x, y, w, h = vp.config_pv
            
            if fg_pre is None: continue
            
            x1, y1 = max(x, 0), max(y, 0)
            x2, y2 = min(x + w, fw), min(y + h, fh)
            if x1 >= x2 or y1 >= y2: continue

            try:
                ox1, oy1 = x1 - x, y1 - y
                ox2, oy2 = x2 - x, y2 - y
                
                f_roi = fg_pre[oy1:oy2, ox1:ox2]
                i_roi = inv_a[oy1:oy2, ox1:ox2]
                b_roi = frame_bgr[y1:y2, x1:x2]
                
                if f_roi.shape[:2] != b_roi.shape[:2]:
                    f_roi = cv2.resize(f_roi, (b_roi.shape[1], b_roi.shape[0]), interpolation=cv2.INTER_NEAREST)
                    i_roi = cv2.resize(i_roi, (b_roi.shape[1], b_roi.shape[0]), interpolation=cv2.INTER_NEAREST)

                tmp = b_roi.astype(np.uint32) * i_roi + f_roi
                frame_bgr[y1:y2, x1:x2] = (tmp // 255).astype(np.uint8)
            except Exception as e:
                print(f"[Engine] Apply error in slot {slot}: {e}")
                
        return frame_bgr

    @classmethod
    def stop_all(cls):
        for vp in cls._players: vp.stop()

    @classmethod
    def set_paused(cls, paused: bool):
        for vp in cls._players:
            vp.paused = paused

    @classmethod
    def all_finished(cls) -> bool:
        return all(vp.finished or not vp.running for vp in cls._players)
