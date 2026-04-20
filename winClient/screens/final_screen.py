"""
Pantalla final: foto a pantalla completa, QR + botón superpuestos y escalados dinámicamente.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor

try:
    from qr_service import QRService
    _HAS_QR = True
except ImportError:
    _HAS_QR = False

_GREEN_DEEP    = "#064E3B"
_GREEN_EMERALD = "#10B981"
_GREEN_MID     = "#059669"
_GREEN_PRESS   = "#047857"


def _fs(height: int, ratio: float) -> int:
    """Font size proportional to window height."""
    return max(8, int(height * ratio))


class FinalScreen(QWidget):
    """Foto a pantalla completa con QR y botón superpuestos adaptativos."""

    def __init__(self, main_window, photo_path=None):
        super().__init__()
        self.main_window = main_window
        self.photo_path  = photo_path
        self._bg_pixmap  = None
        self._qr_pixmap  = None   # raw QR, re-scaled on resize
        self._init_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _init_ui(self):
        self._overlay = QWidget(self)
        self._overlay.setStyleSheet("background: transparent;")
        self._overlay.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root = QVBoxLayout(self._overlay)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addStretch(1)

        # ── QR panel ─────────────────────────────────────────────────────
        self._qr_frame = QFrame()
        self._qr_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qr_inner = QVBoxLayout(self._qr_frame)
        qr_inner.setContentsMargins(16, 16, 16, 12)
        qr_inner.setSpacing(6)

        self._qr_label = QLabel()
        self._qr_label.setAlignment(Qt.AlignCenter)
        self._qr_label.setStyleSheet("background: transparent; border: none;")
        self._qr_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qr_inner.addWidget(self._qr_label, alignment=Qt.AlignCenter)

        self._scan_lbl = QLabel("Escanea para descargar tu foto")
        self._scan_lbl.setAlignment(Qt.AlignCenter)
        self._scan_lbl.setStyleSheet(
            f"color: {_GREEN_DEEP}; background: transparent; border: none;"
        )
        qr_inner.addWidget(self._scan_lbl)

        root.addWidget(self._qr_frame, alignment=Qt.AlignHCenter)
        root.addSpacing(0)   # dynamic via resizeEvent

        # ── Button ───────────────────────────────────────────────────────
        self._btn = QPushButton("VOLVER AL INICIO")
        self._btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(self._on_restart)
        root.addWidget(self._btn, alignment=Qt.AlignHCenter)

        root.addStretch(0)   # bottom padding controlled by resizeEvent margin

    # ── Qt events ─────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()

        self._overlay.setGeometry(0, 0, w, h)

        # Scale QR image
        qr_size = int(h * 0.20)   # 20 % of height
        if self._qr_pixmap and not self._qr_pixmap.isNull():
            scaled = self._qr_pixmap.scaled(
                QSize(qr_size, qr_size), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self._qr_label.setPixmap(scaled)
        self._qr_label.setFixedSize(qr_size, qr_size)

        # QR frame border-radius
        radius = int(qr_size * 0.10)
        self._qr_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 220);
                border: 3px solid {_GREEN_EMERALD};
                border-radius: {radius}px;
            }}
        """)

        # Adaptive fonts
        self._scan_lbl.setFont(QFont("Arial", _fs(h, 0.016), QFont.Bold))

        btn_font_size = _fs(h, 0.022)
        btn_h = int(h * 0.07)
        btn_w = int(w * 0.55)
        btn_radius = btn_h // 2
        self._btn.setMinimumSize(btn_w, btn_h)
        self._btn.setFont(QFont("Arial", btn_font_size, QFont.Bold))
        self._btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_GREEN_EMERALD};
                color: white;
                border: none;
                border-radius: {btn_radius}px;
                font-weight: bold;
                font-size: {btn_font_size}px;
                padding: 0 {int(w * 0.04)}px;
            }}
            QPushButton:hover   {{ background-color: {_GREEN_MID};   }}
            QPushButton:pressed {{ background-color: {_GREEN_PRESS}; }}
        """)

        # Bottom margin = 5 % of height
        layout = self._overlay.layout()
        layout.setContentsMargins(0, 0, 0, int(h * 0.05))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        if self._bg_pixmap and not self._bg_pixmap.isNull():
            scaled = self._bg_pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (self.width()  - scaled.width())  // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0))

    # ── Public API ────────────────────────────────────────────────────────────

    def set_final_image(self, image_path: str, qr_base64: str) -> None:
        """Establece foto de fondo y QR recibido del servidor."""
        self.photo_path = image_path

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self._bg_pixmap = pixmap
            self.update()

        if _HAS_QR and qr_base64:
            raw = QRService.base64_to_pixmap(qr_base64, max_size=512)
            if raw:
                self._qr_pixmap = raw
                # trigger re-scale via resizeEvent logic
                self.resizeEvent(None)

    # ── Callback ──────────────────────────────────────────────────────────────

    def _on_restart(self):
        if hasattr(self.main_window, "show_welcome"):
            self.main_window.show_welcome()
