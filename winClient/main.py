"""
Stadium Photo Booth — Cliente Windows
Ejecutar: python main.py
Instalar dependencias: pip install -r requirements.txt
"""
import customtkinter as ctk

from config import BG, WIN_W, WIN_H
from screens.welcome          import WelcomeScreen
from screens.player_selection import PlayerSelectionScreen
from screens.camera_preview   import CameraPreviewScreen
from screens.photo_view       import PhotoViewScreen
from screens.simulation       import SimulationScreen
from screens.final_screen     import FinalScreen

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class StadiumApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Stadium Photo Booth")
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self._screen = None
        self.show_welcome()

    # ── Navegación ────────────────────────────────────────────────────────────

    def _go(self, ScreenClass, **kwargs):
        if self._screen:
            self._screen.destroy()
        self._screen = ScreenClass(self, **kwargs)
        self._screen.place(x=0, y=0, relwidth=1, relheight=1)

    def show_welcome(self):
        self._go(WelcomeScreen)

    def show_player_selection(self):
        self._go(PlayerSelectionScreen)

    def show_camera(self, players):
        self._go(CameraPreviewScreen, players=players)

    def show_photo_view(self, photo_path: str, players):
        self._go(PhotoViewScreen, photo_path=photo_path, players=players)

    def show_simulation(self, photo_path: str, players):
        self._go(SimulationScreen, photo_path=photo_path, players=players)

    def show_final(self, photo_path: str):
        self._go(FinalScreen, photo_path=photo_path)


if __name__ == "__main__":
    app = StadiumApp()
    app.mainloop()
