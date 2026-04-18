import customtkinter as ctk
from config import BG


class BaseScreen(ctk.CTkFrame):
    """Frame base para todas las pantallas. Provee acceso al app y cleanup."""

    def __init__(self, app, **kwargs):
        super().__init__(app, fg_color=BG, corner_radius=0, **kwargs)
        self.app = app

    def on_destroy(self):
        """Sobrescribir para liberar recursos (cámara, hilos, etc.)."""
        pass

    def destroy(self):
        self.on_destroy()
        super().destroy()
