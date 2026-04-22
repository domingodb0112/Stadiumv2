from PyQt5.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from screens.base_screen import BaseScreen
from config import BG, ACCENT, TEXT_WHITE, TEXT_DIM

class LoadingScreen(BaseScreen):
    """Pantalla de transición rápida entre Selección y Cámara."""

    def __init__(self, app, players, **kwargs):
        super().__init__(app, **kwargs)
        self._players = players
        self._build_ui()
        
        # Temporizador para pasar a la cámara automáticamente
        # Le damos 2.5 segundos para dar la ilusión de carga y permitir que el hardware despierte
        QTimer.singleShot(2500, self._proceed_to_camera)

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 0, 40, 0)

        # Título
        title = QLabel("PREPARANDO CÁMARA...")
        title.setFont(QFont("Arial Black", 52, QFont.Bold)) # Aumentado
        title.setStyleSheet(f"color: {ACCENT};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtítulo
        subtitle = QLabel("Ajustando luces y sombras para tu mejor perfil.")
        subtitle.setFont(QFont("Arial", 26)) # Aumentado
        subtitle.setStyleSheet(f"color: {TEXT_WHITE};")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(subtitle)

        # Barra animada (Indeterminada)
        layout.addSpacing(40)
        progress = QProgressBar()
        progress.setRange(0, 0) # Estilo indeterminado (animación infinita)
        progress.setFixedHeight(10)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #333;
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(progress)

        self.setLayout(layout)
        self.setStyleSheet(f"background-color: {BG};")

    def _proceed_to_camera(self):
        self.app.show_camera(self._players)
