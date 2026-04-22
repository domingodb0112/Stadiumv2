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
                print("[CameraManager] Powering on hardware for the first time...")
                cls._cap = cv2.VideoCapture(0)
                if cls._cap.isOpened():
                    cls._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cls._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    # "Calentar" el hardware para evitar el primer frame negro
                    for _ in range(5): cls._cap.read()
            return cls._cap

    @classmethod
    def release(cls):
        """Libera el hardware al cerrar la app."""
        with cls._lock:
            if cls._cap:
                cls._cap.release()
                cls._cap = None
