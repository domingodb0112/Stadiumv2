from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont


class WelcomeScreen(QWidget):
    """Pantalla de bienvenida."""

    start_pressed = pyqtSignal()

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self._init_ui()

    def _init_ui(self) -> None:
        """Inicializa la interfaz."""
        layout = QVBoxLayout()

        # Título
        title = QLabel("BIENVENIDO A STADIUM")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Descripción
        desc = QLabel(
            "Captura tu momento en la cancha.\n"
            "¡Llévate una foto épica a casa!"
        )
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Spacer
        layout.addStretch()

        # Botón de inicio
        start_btn = QPushButton("COMENZAR")
        start_btn.setStyleSheet(
            "background-color: #FF6B35; color: white; font-size: 16px; padding: 15px;"
        )
        start_btn.clicked.connect(self.start_pressed.emit)
        layout.addWidget(start_btn)

        self.setLayout(layout)
