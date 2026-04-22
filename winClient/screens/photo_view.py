"""
Photo view screen for PyQt5 - Display captured photo with retry/send options
"""
from PIL import Image
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QPixmap, QCursor

from screens.base_screen import BaseScreen
from config import BG, TEXT_WHITE, ACCENT, BTN_DARK, WIN_W, WIN_H, AUTO_SEND_MS


class PhotoViewScreen(BaseScreen):
    """Displays captured photo with retry/send buttons and 5-second countdown."""

    def __init__(self, app, photo_path: str, players, **kwargs):
        super().__init__(app, **kwargs)
        self._photo_path = photo_path
        self._players = players
        self._timer = None
        self._seconds_left = AUTO_SEND_MS // 1000

        self._build_ui()
        self._load_photo()
        self._start_timer()

    def _build_ui(self):
        """Build the UI: centered photo + buttons with countdown."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Photo display (centrado vertical) ──────────────────────────────
        self._lbl_photo = QLabel()
        self._lbl_photo.setAlignment(Qt.AlignCenter)
        self._lbl_photo.setStyleSheet("background-color: #000; border: none;")
        self._lbl_photo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        main_layout.addSpacing(100) # Spacing superior
        main_layout.addWidget(self._lbl_photo, 1)
        main_layout.addSpacing(40)

        # ── Buttons layout (bottom, centered) ──────────────────────────────
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 32)
        buttons_layout.setSpacing(16)
        buttons_layout.addStretch()

        # REINTENTAR button (left)
        btn_retake = QPushButton("REINTENTAR")
        btn_retake.setFont(QFont("Arial Black", 14))
        btn_retake.setFixedSize(220, 70)
        btn_retake.setStyleSheet(f"""
            QPushButton {{
                background-color: {BTN_DARK};
                color: {TEXT_WHITE};
                border: none;
                border-radius: 35px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #666666; }}
        """)
        btn_retake.setCursor(QCursor(Qt.PointingHandCursor))
        btn_retake.clicked.connect(self._on_retake)
        buttons_layout.addWidget(btn_retake)

        # ENVIAR button (right) with countdown
        self._btn_send = QPushButton(f"ENVIAR ({self._seconds_left}s)")
        self._btn_send.setFont(QFont("Arial Black", 14))
        self._btn_send.setFixedSize(220, 70)
        self._btn_send.setStyleSheet(f"""
            QPushButton {{
                background-color: #1976D2;
                color: {TEXT_WHITE};
                border: none;
                border-radius: 35px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #1565C0; }}
        """)
        self._btn_send.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_send.clicked.connect(self._on_send)
        buttons_layout.addWidget(self._btn_send)

        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def _load_photo(self):
        """Load and display the captured photo."""
        try:
            pixmap = QPixmap(self._photo_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self._lbl_photo.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error loading photo: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._load_photo()

    def _start_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _tick(self):
        if self._seconds_left > 0:
            self._seconds_left -= 1
            self._btn_send.setText(f"ENVIAR ({self._seconds_left}s)")
        else:
            self._on_send()

    def _stop_timer(self):
        if self._timer:
            self._timer.stop()
            self._timer = None

    def _on_retake(self):
        self._stop_timer()
        self.app.show_camera(self._players)

    def _on_send(self):
        self._stop_timer()
        self.app.show_simulation(self._photo_path, self._players)

    def on_destroy(self):
        self._stop_timer()
