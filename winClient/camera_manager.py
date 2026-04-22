import cv2
import threading

class CameraManager:
    """Administrador único de hardware para evitar reinicios de cámara."""
    _cap = None
    _lock = threading.Lock()

    @classmethod
    def get_cap(cls):
        """Obtiene la instancia única de la cámara, abriéndola si es necesario."""
        with cls._lock:
            if cls._cap is None or not cls._cap.isOpened():
                print("[CameraManager] Powering on hardware (Lite mode)...")
                # Solo abrimos el canal, no forzamos resolución aquí para evitar bloqueos
                cls._cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            return cls._cap

    @classmethod
    def release(cls):
        """Libera el hardware al cerrar la app."""
        with cls._lock:
            if cls._cap:
                cls._cap.release()
                cls._cap = None
