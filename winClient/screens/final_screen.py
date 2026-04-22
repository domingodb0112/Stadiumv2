"""
Final screen — Design System C (Editorial Claro)
Photo fills top, bottom panel has QR + button.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import (
    QPixmap, QFont, QPainter, QColor, QLinearGradient, QPen, QBrush,
)

try:
    from qr_service import QRService
    _HAS_QR = True
except ImportError:
    _HAS_QR = False

from theme import (
    FONT_SANS, BG_PRIMARY, BG_CARD, INK_900, INK_400,
    GREEN_500, GREEN_600, BORDER, BG_MUTED,
    btn_primary,
)
from ui_components import GradientBar


class FinalScreen(QWidget):
    """Photo (top portion) + bottom panel with green dot, QR code, 'Volver al inicio' button."""

    # Fraction of window height occupied by bottom panel
    _PANEL_RATIO = 0.28

    def __init__(self, main_window, photo_path=None):
        super().__init__()
        self.main_window = main_window
        self.photo_path  = photo_path
        self._bg_pixmap  = None
        self._qr_pixmap  = None
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")
        self._init_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _init_ui(self):
        # The photo is drawn in paintEvent; overlay sits on top.
        self._overlay = QWidget(self)
        self._overlay.setStyleSheet("background: transparent;")

        root = QVBoxLayout(self._overlay)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Close button (top-right, floating) ────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 16, 16, 0)
        btn_row.addStretch()
        self._btn_close = QPushButton("✕")
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.clicked.connect(self._on_restart)
        btn_row.addWidget(self._btn_close)
        root.addLayout(btn_row)

        root.addStretch(1)   # pushes panel to bottom

        # ── Bottom panel ──────────────────────────────────────────────────────
        self._panel = QWidget()
        self._panel.setStyleSheet(
            f"background-color: {BG_PRIMARY}; "
            f"border-top: 1px solid rgba(0,0,0,30);"
        )
        panel_l = QVBoxLayout(self._panel)
        panel_l.setAlignment(Qt.AlignCenter)

        # "Tu foto está lista" row
        ready_row = QHBoxLayout()
        ready_row.setSpacing(10)
        ready_row.setAlignment(Qt.AlignCenter)

        self._dot = QLabel()
        self._dot.setStyleSheet(
            f"background-color: {GREEN_500}; border-radius: 4px;"
        )
        ready_row.addWidget(self._dot)

        self._lbl_ready = QLabel("Tu foto está lista")
        self._lbl_ready.setFont(QFont(FONT_SANS, 15, QFont.DemiBold))
        self._lbl_ready.setStyleSheet(
            f"color: {INK_900}; background: transparent; border: none;"
        )
        ready_row.addWidget(self._lbl_ready)
        panel_l.addLayout(ready_row)

        # QR + description row
        qr_row = QHBoxLayout()
        qr_row.setSpacing(16)
        qr_row.setAlignment(Qt.AlignCenter)

        self._qr_wrapper = QWidget()
        self._qr_wrapper.setStyleSheet(f"""
            background-color: {BG_CARD};
            border: 1px solid rgba(0,0,0,20);
            border-radius: 10px;
        """)
        qr_inner = QVBoxLayout(self._qr_wrapper)
        qr_inner.setContentsMargins(8, 8, 8, 8)
        self._qr_label = QLabel()
        self._qr_label.setAlignment(Qt.AlignCenter)
        self._qr_label.setStyleSheet("background: transparent; border: none;")
        qr_inner.addWidget(self._qr_label)
        qr_row.addWidget(self._qr_wrapper)

        desc_w = QWidget()
        desc_w.setStyleSheet("background: transparent;")
        desc_l = QVBoxLayout(desc_w)
        desc_l.setContentsMargins(0, 0, 0, 0)
        desc_l.setSpacing(4)

        self._lbl_scan = QLabel("Escanea con tu cámara")
        self._lbl_scan.setFont(QFont(FONT_SANS, 13, QFont.DemiBold))
        self._lbl_scan.setStyleSheet(
            f"color: {INK_900}; background: transparent; border: none;"
        )
        desc_l.addWidget(self._lbl_scan)

        self._lbl_desc = QLabel("Descarga tu foto al instante\ndesde tu teléfono.")
        self._lbl_desc.setFont(QFont(FONT_SANS, 12))
        self._lbl_desc.setStyleSheet(
            f"color: {INK_400}; background: transparent; border: none;"
        )
        self._lbl_desc.setWordWrap(True)
        desc_l.addWidget(self._lbl_desc)
        qr_row.addWidget(desc_w, 1)

        panel_l.addLayout(qr_row)

        # "Volver al inicio" button
        self._btn = QPushButton("Volver al inicio  →")
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(self._on_restart)
        panel_l.addWidget(self._btn)

        root.addWidget(self._panel)
        root.addWidget(GradientBar(height=4))

    # ── Qt events ─────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._overlay.setGeometry(0, 0, w, h)

        panel_h = max(180, int(h * self._PANEL_RATIO))
        self._panel.setFixedHeight(panel_h)

        # Close button
        close_sz = max(28, int(h * 0.026))
        close_r  = max(6,  int(h * 0.007))
        self._btn_close.setFixedSize(close_sz, close_sz)
        self._btn_close.setFont(QFont(FONT_SANS, max(10, int(h * 0.009))))
        self._btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0,0,0,100);
                color: white;
                border: none;
                border-radius: {close_r}px;
            }}
            QPushButton:hover {{ background-color: rgba(0,0,0,150); }}
        """)

        # Green dot
        dot_sz = max(6, int(h * 0.006))
        self._dot.setFixedSize(dot_sz, dot_sz)
        self._dot.setStyleSheet(
            f"background-color: {GREEN_500}; border-radius: {dot_sz // 2}px;"
        )

        # QR
        qr_sz = max(60, int(panel_h * 0.42))
        self._qr_label.setFixedSize(qr_sz, qr_sz)
        if self._qr_pixmap and not self._qr_pixmap.isNull():
            self._qr_label.setPixmap(
                self._qr_pixmap.scaled(
                    QSize(qr_sz, qr_sz), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )

        # Fonts
        ready_pt = max(12, int(h * 0.010))
        scan_pt  = max(10, int(h * 0.009))
        desc_pt  = max(9,  int(h * 0.008))
        btn_pt   = max(12, int(h * 0.011))
        btn_h    = max(44, int(panel_h * 0.26))
        btn_r    = max(10, int(h * 0.013))

        self._lbl_ready.setFont(QFont(FONT_SANS, ready_pt, QFont.DemiBold))
        self._lbl_scan.setFont(QFont(FONT_SANS, scan_pt, QFont.DemiBold))
        self._lbl_desc.setFont(QFont(FONT_SANS, desc_pt))

        self._btn.setFont(QFont(FONT_SANS, btn_pt, QFont.DemiBold))
        self._btn.setFixedHeight(btn_h)
        self._btn.setStyleSheet(btn_primary(radius=btn_r, font_size=btn_pt))

        # Panel inner margins
        self._panel.layout().setContentsMargins(
            max(16, int(w * 0.04)), max(12, int(panel_h * 0.08)),
            max(16, int(w * 0.04)), max(16, int(panel_h * 0.12)),
        )
        self._panel.layout().setSpacing(max(10, int(panel_h * 0.08)))

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        panel_h = self._panel.height() + 4  # + gradient bar
        photo_area_h = self.height() - panel_h

        # Dark background behind photo letterbox
        painter.fillRect(0, 0, self.width(), photo_area_h, QColor("#1a1f1c"))

        if self._bg_pixmap and not self._bg_pixmap.isNull():
            available = self.size()
            available.setHeight(photo_area_h)
            scaled = self._bg_pixmap.scaled(
                available, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (photo_area_h - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_final_image(self, image_path: str, qr_base64: str) -> None:
        self.photo_path = image_path

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self._bg_pixmap = pixmap
            self.update()

        if _HAS_QR and qr_base64:
            raw = QRService.base64_to_pixmap(qr_base64, max_size=512)
            if raw:
                self._qr_pixmap = raw
                self.resizeEvent(None)

    # ── Callback ──────────────────────────────────────────────────────────────

    def _on_restart(self):
        if hasattr(self.main_window, "show_welcome"):
            self.main_window.show_welcome()
