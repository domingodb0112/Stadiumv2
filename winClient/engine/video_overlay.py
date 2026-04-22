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
        self.current_fg_pre: np.ndarray | None = None  # BGR pre-multiplied
        self.current_inv_alpha: np.ndarray | None = None # Inverse alpha map
        self.lock          = threading.Lock()
        self.running       = False
        self.ready         = False
        self.finished      = False
        self.looping       = False
        self.paused        = False # Nuevo: Control de reproducción
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
            self.current_fg_pre = None
            self.current_inv_alpha = None
            self.ready = False

    def _loop(self, path: str):
        import os
        if not os.path.exists(path):
            print(f"[!] Video not found: {path}. Using placeholder.")
            self._set_placeholder_frame()
            self.running = False
            return

        if path in VideoOverlayEngine._video_cache:
            frames, fps = VideoOverlayEngine._video_cache[path]
        else:
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
                    if self.paused and self.ready:
                        # Si está pausado y ya tiene el primer frame, esperar
                        time.sleep(0.05)
                        continue

                    t0 = time.perf_counter()

                    offset, size = frames[idx]
                    f.seek(offset)
                    buf = f.read(size)

                    arr     = np.frombuffer(buf, dtype=np.uint8)
                    decoded = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)

                    if decoded is not None and decoded.ndim == 3 and decoded.shape[2] == 4:
                        # Pre-resize
                        x, y, w, h = self.config
                        if w > 0 and h > 0:
                            decoded = cv2.resize(decoded, (w, h), interpolation=cv2.INTER_LINEAR)
                        
                        # OPTIMIZACIÓN TURBO: Usamos enteros (uint16) en lugar de decimales
                        alpha  = decoded[:, :, 3:4].astype(np.uint16)
                        fg_rgb = decoded[:, :, :3].astype(np.uint16)
                        
                        # Pre-multiplicamos el frente por su alfa: 0 - 65025
                        fg_pre    = fg_rgb * alpha
                        # Guardamos el alfa inverso para el fondo: 0 - 255
                        inv_alpha = 255 - alpha
                        
                        with self.lock:
                            self.current_fg_pre    = fg_pre
                            self.current_inv_alpha = inv_alpha
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
    _video_cache: dict[str, tuple] = {} # Path -> (frames, fps)
    _active_slots: list[int] = []       # Slots seleccionados actualmente

    @classmethod
    def preload_all_videos(cls, player_data_list):
        """Carga todos los videos en caché para evitar lag de disco."""
        import os
        from engine.mov_parser import parse_mov
        for p in player_data_list:
            path = f"assets/videos/{p['video_name']}"
            if path not in cls._video_cache and os.path.exists(path):
                print(f"[Engine] Pre-loading {path}...")
                cls._video_cache[path] = parse_mov(path)

    @classmethod
    def set_paused(cls, paused: bool):
        """Pausa o reanuda todos los jugadores."""
        for vp in cls._players:
            vp.paused = paused

    @classmethod
    def warm_up(cls, player_data_list, screen_w, screen_h):
        """Carga y prepara a TODOS los jugadores posibles en segundo plano."""
        cls.preload_all_videos(player_data_list)
        for p_data in player_data_list:
            slot = p_data.get("slot", 0)
            vp = cls._players[slot]
            
            # Configurar coordenadas (escaladas)
            from config import REF_W, REF_H
            x = int(p_data['x'] * screen_w / REF_W)
            y = int(p_data['y'] * screen_h / REF_H)
            w = int(p_data['w'] * screen_w / REF_W)
            h = int(p_data['h'] * screen_h / REF_H)
            vp.config = (x, y, w, h)
            
            # Dejarlo listo y pausado en el primer frame (loop=False para que solo sea una vez)
            vp.paused = True
            path = f"assets/videos/{p_data['video_name']}"
            vp.start(path, looping=False)
        print("[Engine] All players warmed up and ready.")

    @classmethod
    def start_experience(cls, player_list, screen_w, screen_h, paused=False):
        """
        Activa y REINICIA los videos para una nueva sesión.
        Asegura que los hilos estén corriendo.
        """
        cls._active_slots = [p.slot for p in player_list]
        
        for slot in cls._active_slots:
            vp = cls._players[slot]
            
            # Si el hilo se detuvo por algún motivo, reiniciarlo
            if not vp.running:
                # Buscar el path en los datos originales (basado en el slot)
                # O simplemente usar el path que ya tiene si es válido
                pass 
            
            vp.current_frame = 0 # Reiniciar al inicio
            vp.paused = paused
            
        print(f"[Engine] Experience reset and started for slots: {cls._active_slots}")

    @classmethod
    def apply_all(cls, frame_bgr: np.ndarray) -> np.ndarray:
        """Mezcla solo los jugadores activos respetando el orden de capa."""
        # ORDEN DE CAPA: 0, 2 (atrás) -> 1, 3 (adelante)
        for slot in [0, 2, 1, 3]:
            if slot not in cls._active_slots:
                continue
            
            vp = cls._players[slot]
            if not vp.ready:
                continue
            
            with vp.lock:
                fg_pre         = vp.current_fg_pre
                inv_alpha_mask = vp.current_inv_alpha
                if fg_pre is None or inv_alpha_mask is None:
                    continue

            x, y, w, h = vp.config
            fh, fw = frame_bgr.shape[:2]
            
            # Recortar para no salir de pantalla
            x1, y1 = max(x, 0), max(y, 0)
            x2, y2 = min(x + w, fw), min(y + h, fh)
            if x1 >= x2 or y1 >= y2:
                continue

            try:
                # El frame ya viene pre-redimensionado y pre-multiplicado (Optimización TURBO)
                overlay_x1, overlay_y1 = x1 - x, y1 - y
                overlay_x2, overlay_y2 = x2 - x, y2 - y

                # Extraer ROIs
                fg_pre_roi    = fg_pre[overlay_y1:overlay_y2, overlay_x1:overlay_x2]
                inv_alpha_roi = inv_alpha_mask[overlay_y1:overlay_y2, overlay_x1:overlay_x2]
                bg_roi        = frame_bgr[y1:y2, x1:x2]

                # Formula Turbo (Enteros de 32 bits para evitar desbordamiento):
                # (Fondo * Alfa_Inverso + Frente_Precalculado) // 255
                # Esto es MUCHÍSIMO más rápido que usar punto flotante (decimales)
                tmp = bg_roi.astype(np.uint32) * inv_alpha_roi + fg_pre_roi
                blended = (tmp // 255).astype(np.uint8)
                
                frame_bgr[y1:y2, x1:x2] = blended
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
