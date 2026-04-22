"""
Stadium Photo Booth - Windows Client (PyQt5)
Main app controller
"""
import sys
import os
import threading

# OPTIMIZACIÓN: Evitar que Windows se quede colgado escaneando la cámara (Media Foundation)
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

import cv2
from pathlib import Path

# Agregar el directorio actual al path para que las importaciones de 'screens' funcionen
# independientemente de desde dónde se ejecute el script.
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QFont, QPainter, QColor, QPen

from config import WIN_W, WIN_H, BG, ACCENT
import json
from engine.video_overlay import VideoOverlayEngine
from screens.welcome import WelcomeScreen
from screens.player_selection import PlayerSelectionScreen
from screens.camera_preview import CameraPreviewScreen
from screens.photo_view import PhotoViewScreen
from screens.simulation import SimulationScreen
from screens.final_screen import FinalScreen
from screens.loading_screen import LoadingScreen
from camera_manager import CameraManager
from theme import BG_PRIMARY

class StadiumApp(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stadium Photo Booth")
        self.setWindowFlags(
            Qt.Window
            | Qt.CustomizeWindowHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        self.setMinimumSize(360, 640)
        self.resize(WIN_W, WIN_H)
        self.showFullScreen()

        # Central widget: stacked widget para cambiar entre pantallas
        self.stacked = QStackedWidget()
        self.stacked.layout().setSizeConstraint(QLayout.SetDefaultConstraint)
        self.setCentralWidget(self.stacked)

        # Estilo
        self.setStyleSheet(f"QMainWindow {{ background-color: {BG_PRIMARY}; }}")

        # Pre-cargar videos y cámara en segundo plano
        threading.Thread(target=self._preload_assets, daemon=True).start()

        # Mostrar pantalla de bienvenida
        self.show_welcome()

    def _preload_assets(self):
        try:
            # 1. Encender cámara en background (asíncrono)
            from camera_manager import CameraManager
            CameraManager.get_cap()
            
            # 2. Los videos ya fueron cargados en main(), aquí solo "calentamos" el preview
            with open("assets/players.json", "r", encoding="utf-8") as f:
                players_data = json.load(f)
                VideoOverlayEngine.warm_up(players_data, 720, 1280)
        except Exception as e:
            print(f"[Main] Preload error: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def _clear_stacked(self):
        """Eliminar todos los widgets del stacked widget."""
        while self.stacked.count() > 0:
            widget = self.stacked.widget(0)
            if hasattr(widget, "on_destroy"):
                widget.on_destroy()
            self.stacked.removeWidget(widget)
            widget.deleteLater()

    def show_welcome(self):
        """Mostrar pantalla de bienvenida."""
        self._clear_stacked()
        screen = WelcomeScreen(self)
        self.stacked.addWidget(screen)
        self.stacked.setCurrentWidget(screen)

    def show_player_selection(self):
        """Mostrar pantalla de selección de jugadores."""
        self._clear_stacked()
        screen = PlayerSelectionScreen(self)
        self.stacked.addWidget(screen)
        self.stacked.setCurrentWidget(screen)

    def show_loading(self, players):
        """Mostrar pantalla de carga/transición antes de la cámara."""
        self._clear_stacked()
        screen = LoadingScreen(self, players)
        self.stacked.addWidget(screen)
        self.stacked.setCurrentWidget(screen)

    def show_camera(self, players, cap=None):
        """Mostrar pantalla de cámara. Opcionalmente acepta un 'cap' ya abierto."""
        self._clear_stacked()
        screen = CameraPreviewScreen(self, players, cap=cap)
        self.stacked.addWidget(screen)
        self.stacked.setCurrentWidget(screen)

    def show_photo_view(self, photo_path, players):
        """Mostrar pantalla de vista de foto."""
        self._clear_stacked()
        screen = PhotoViewScreen(self, photo_path, players)
        self.stacked.addWidget(screen)
        self.stacked.setCurrentWidget(screen)

    def show_simulation(self, photo_path, players):
        """Mostrar pantalla de simulación."""
        self._clear_stacked()
        screen = SimulationScreen(self, photo_path, players)
        self.stacked.addWidget(screen)
        self.stacked.setCurrentWidget(screen)

    def show_final(self, photo_path, qr_base64=None):
        """Mostrar pantalla final."""
        self._clear_stacked()
        screen = FinalScreen(self, photo_path)
        self.stacked.addWidget(screen)
        self.stacked.setCurrentWidget(screen)
        screen.set_final_image(photo_path, qr_base64)


def main():
    app = QApplication(sys.argv)
    
    # Pre-cargar videos a la RAM ANTES de mostrar la interfaz (Requerimiento del usuario)
    import json
    from engine.video_overlay import VideoOverlayEngine
    try:
        with open("assets/players.json", "r", encoding="utf-8") as f:
            players_data = json.load(f)
            VideoOverlayEngine.preload_all_videos(players_data)
    except Exception as e:
        print(f"[Main] Error en pre-carga inicial: {e}")

    # Iniciar App
    window = StadiumApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
