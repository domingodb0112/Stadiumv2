"""
Welcome screen for PyQt5
"""
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QWidget
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor
from screens.base_screen import BaseScreen
from config import TEXT_WHITE, TEXT_DIM, ACCENT, BG, PRIMARY
from theme import BTN_PRIMARY, BG_PRIMARY


class WelcomeScreen(BaseScreen):
    """Pantalla de bienvenida — 'STADIUM AR' + botón COMENZAR."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._build_ui()

    def _build_ui(self):
        # Centro: título + subtítulo + botón
        center_layout = QVBoxLayout()
        center_layout.setSpacing(12)
        center_layout.setAlignment(Qt.AlignCenter)

        # Título
        title = QLabel("STADIUM AR")
        title.setFont(QFont("Arial Black", 38, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_WHITE};")
        title.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(title)

        # Subtítulo
        subtitle = QLabel("Vive la experiencia con tus ídolos")
        subtitle.setFont(QFont("Arial", 15))
        subtitle.setStyleSheet(f"color: {TEXT_DIM};")
        subtitle.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(subtitle)

        center_layout.addSpacing(48)

        # Botón (AutoZone Brand)
        btn = QPushButton("TOCA PARA COMENZAR")
        btn.setStyleSheet(BTN_PRIMARY)
        btn.clicked.connect(self.app.show_player_selection)
        center_layout.addWidget(btn, alignment=Qt.AlignCenter)

        # Widget central
        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(center_widget, alignment=Qt.AlignCenter)
        self.setLayout(main_layout)
