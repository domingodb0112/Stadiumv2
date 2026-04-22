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

        # Title
        title_label = QLabel("BIENVENIDO\nAL JUEGO")
        title_label.setFont(QFont("Arial Black", 52, QFont.Bold)) # Aumentado
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("TU HISTORIA COMIENZA AQUÍ")
        subtitle_label.setFont(QFont("Arial", 28)) # Aumentado
        subtitle_label.setStyleSheet("color: #10B981;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        center_layout.addSpacing(20)
        center_layout.addWidget(subtitle_label)

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
