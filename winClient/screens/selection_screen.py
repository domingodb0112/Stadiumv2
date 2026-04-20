from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont


class SelectionScreen(QWidget):
    """Pantalla de selección de overlays."""

    confirmed = pyqtSignal()

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.overlay_checkboxes = []
        self._init_ui()

    def _init_ui(self) -> None:
        """Inicializa la interfaz."""
        layout = QVBoxLayout()

        # Título
        title = QLabel("ELIGE TUS JUGADORES")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Obtener overlays desde config
        overlays = self.config_manager.get_overlays()

        # Crear checkboxes para cada overlay
        for overlay in overlays:
            checkbox = QCheckBox(overlay.get("name", f"Overlay {overlay.get('slot')}"))
            checkbox.setChecked(True)
            self.overlay_checkboxes.append((checkbox, overlay))
            layout.addWidget(checkbox)

        layout.addStretch()

        # Botón confirmar
        confirm_btn = QPushButton("CONFIRMAR")
        confirm_btn.setStyleSheet(
            "background-color: #004E89; color: white; font-size: 16px; padding: 15px;"
        )
        confirm_btn.clicked.connect(self.confirmed.emit)
        layout.addWidget(confirm_btn)

        self.setLayout(layout)

    def get_selected_overlays(self) -> list:
        """Retorna overlays seleccionados."""
        selected = [
            overlay
            for checkbox, overlay in self.overlay_checkboxes
            if checkbox.isChecked()
        ]
        return selected
