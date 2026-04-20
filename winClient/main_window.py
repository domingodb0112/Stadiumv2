from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from pathlib import Path

# Importar pantallas (delegadas a módulos independientes)
from screens.welcome_screen import WelcomeScreen
from screens.selection_screen import SelectionScreen
from screens.camera_screen import CameraScreen
from screens.final_screen import FinalScreen


class MainWindow(QMainWindow):
    """Orquestador principal de pantallas."""

    def __init__(self, config_manager, width=540, height=960):
        super().__init__()
        self.config_manager = config_manager
        self.captured_photo_path = None
        self.qr_base64 = None

        # Configurar ventana
        self.setWindowTitle("StadiumV3 - AR Photo Booth")
        self.setFixedSize(width, height)

        # Widget central con QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Inicializar pantallas
        self._init_screens()
        self._connect_signals()

        # Mostrar primer pantalla
        self.show_welcome()

    def _init_screens(self) -> None:
        """Inicializa todas las pantallas."""
        self.welcome_screen = WelcomeScreen(self.config_manager)
        self.selection_screen = SelectionScreen(self.config_manager)
        self.camera_screen = CameraScreen(self.config_manager)
        self.final_screen = FinalScreen(self.config_manager)

        self.stacked_widget.addWidget(self.welcome_screen)    # 0
        self.stacked_widget.addWidget(self.selection_screen)  # 1
        self.stacked_widget.addWidget(self.camera_screen)     # 2
        self.stacked_widget.addWidget(self.final_screen)      # 3

    def _connect_signals(self) -> None:
        """Conecta señales entre pantallas."""
        self.welcome_screen.start_pressed.connect(self.show_selection)
        self.selection_screen.confirmed.connect(self.show_camera)
        self.camera_screen.photo_captured.connect(self._on_photo_captured)
        self.final_screen.restart_pressed.connect(self.show_welcome)

    def _on_photo_captured(self, photo_path: str) -> None:
        """Callback cuando se captura una foto."""
        self.captured_photo_path = photo_path
        self.camera_screen.process_photo(photo_path, self.final_screen)

    def show_welcome(self) -> None:
        """Navega a pantalla de bienvenida."""
        self.stacked_widget.setCurrentWidget(self.welcome_screen)

    def show_selection(self) -> None:
        """Navega a pantalla de selección."""
        self.stacked_widget.setCurrentWidget(self.selection_screen)

    def show_camera(self) -> None:
        """Navega a pantalla de cámara."""
        selected_overlays = self.selection_screen.get_selected_overlays()
        self.camera_screen.set_overlays(selected_overlays)
        self.stacked_widget.setCurrentWidget(self.camera_screen)

    def show_final(self, final_image_path: str, qr_base64: str) -> None:
        """Navega a pantalla final."""
        self.qr_base64 = qr_base64
        self.final_screen.set_final_image(final_image_path, qr_base64)
        self.stacked_widget.setCurrentWidget(self.final_screen)

    def closeEvent(self, event) -> None:
        """Libera recursos al cerrar."""
        self.camera_screen.release_camera()
        event.accept()
