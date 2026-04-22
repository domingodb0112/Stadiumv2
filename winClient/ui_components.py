"""Shared UI components for Design System C — Editorial Claro."""

from PyQt5.QtWidgets import QWidget, QSizePolicy, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, QSize, QRect, QPoint
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QPen, QBrush, QFont

from theme import GREEN_500, GREEN_600, INK_900, BG_PRIMARY, FONT_SANS, BG_MUTED


class GradientBar(QWidget):
    """4-5px horizontal green gradient bar (bottom accent)."""

    def __init__(self, height: int = 5, parent=None):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_StyledBackground, False)

    def paintEvent(self, event):
        p = QPainter(self)
        g = QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0.0, QColor(GREEN_500))
        g.setColorAt(1.0, QColor(GREEN_600))
        p.fillRect(self.rect(), g)


class CaptureButton(QWidget):
    """
    Circular capture button:
      outer ring  — dark ink (#0a1a0e) with semi-transparent green border
      inner circle — green (#00c45c)
    Emits clicked signal when pressed.
    """

    clicked = __import__("PyQt5.QtCore", fromlist=["pyqtSignal"]).pyqtSignal()

    def __init__(self, size: int = 64, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self._pressed = False

    def sizeHint(self) -> QSize:
        return QSize(self._size, self._size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        s = self._size
        border_w = max(3, int(s * 0.063))  # ~4px at 64px
        inner_r = int(s * 0.375)           # ~24px diameter at 64px

        # Outer circle — dark background
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(INK_900)))
        p.drawEllipse(border_w, border_w, s - 2 * border_w, s - 2 * border_w)

        # Border ring — semi-transparent green
        pen = QPen(QColor(0, 196, 92, 77), border_w)  # rgba(0,196,92,0.30)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        offset = border_w // 2
        p.drawEllipse(offset, offset, s - 2 * offset, s - 2 * offset)

        # Inner dot — green
        scale = 0.85 if self._pressed else 1.0
        ir = int(inner_r * scale)
        cx, cy = s // 2, s // 2
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(GREEN_500)))
        p.drawEllipse(cx - ir, cy - ir, ir * 2, ir * 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = False
            self.update()
            if self.rect().contains(event.pos()):
                self.clicked.emit()

    def resizeEvent(self, event):
        self._size = min(self.width(), self.height())
        super().resizeEvent(event)


class CheckBadge(QWidget):
    """Green circle with white checkmark (20×20), used on selected player cards."""

    def __init__(self, size: int = 20, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self.width()

        # Circle
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(GREEN_500)))
        p.drawEllipse(0, 0, s, s)

        # Checkmark
        pen = QPen(QColor("white"), max(1.5, s * 0.08), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        m = s * 0.20
        p.drawLine(
            QPoint(int(m), int(s * 0.50)),
            QPoint(int(s * 0.44), int(s * 0.74)),
        )
        p.drawLine(
            QPoint(int(s * 0.44), int(s * 0.74)),
            QPoint(int(s * 0.80), int(s * 0.30)),
        )


class TopBar(QWidget):
    """
    Reusable Top Bar component for Design System C.
    Can be configured with left/center/right widgets.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)  # Default height, adjusted via _scale_fonts
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(
            f"background-color: {BG_PRIMARY}; "
            f"border-bottom: 1px solid rgba(0,0,0,40);"
        )

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(24, 0, 24, 0)
        self._layout.setSpacing(0)

        # Left slot
        self.left_slot = QWidget()
        self.left_slot.setStyleSheet("background: transparent; border: none;")
        self.left_layout = QHBoxLayout(self.left_slot)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.left_slot)

        self._layout.addStretch()

        # Center slot
        self.center_slot = QWidget()
        self.center_slot.setStyleSheet("background: transparent; border: none;")
        self.center_layout = QVBoxLayout(self.center_slot)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(2)
        self.center_layout.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self.center_slot, 1)

        self._layout.addStretch()

        # Right slot
        self.right_slot = QWidget()
        self.right_slot.setStyleSheet("background: transparent; border: none;")
        self.right_layout = QHBoxLayout(self.right_slot)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.right_slot)

    def set_brand_mode(self):
        """Standard mode: 'STADIUM' on left, Green Dot on right."""
        self.clear_slots()

        brand = QLabel("STADIUM")
        brand.setFont(QFont(FONT_SANS, 13, QFont.Bold))
        brand.setStyleSheet(f"color: {INK_900}; background: transparent; border: none;")
        self.left_layout.addWidget(brand)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background-color: {GREEN_500}; border-radius: 4px;")
        self.right_layout.addWidget(dot)

    def set_title_mode(self, title_text, subtitle_text=None, back_callback=None):
        """Mode for Camera/Preview: Back button on left, Title in center."""
        self.clear_slots()

        if back_callback:
            back_btn = QPushButton("←")
            back_btn.setCursor(Qt.PointingHandCursor)
            back_btn.setFixedSize(36, 36)
            back_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BG_MUTED};
                    color: {INK_900};
                    border: none;
                    border-radius: 18px;
                    font-weight: 600;
                    font-size: 16px;
                }}
                QPushButton:hover   {{ background-color: #e2e3de; }}
            """)
            back_btn.clicked.connect(back_callback)
            self.left_layout.addWidget(back_btn)
        else:
            # Empty spacer to balance
            spacer = QWidget()
            spacer.setFixedSize(36, 36)
            self.left_layout.addWidget(spacer)

        title = QLabel(title_text)
        title.setFont(QFont(FONT_SANS, 14, QFont.DemiBold))
        title.setStyleSheet(f"color: {INK_900}; background: transparent; border: none;")
        title.setAlignment(Qt.AlignCenter)
        self.center_layout.addWidget(title)

        if subtitle_text:
            sub = QLabel(subtitle_text)
            sub.setFont(QFont(FONT_SANS, 10, QFont.Bold))
            sub.setStyleSheet(f"color: {GREEN_600}; letter-spacing: 2px; background: transparent; border: none;")
            sub.setAlignment(Qt.AlignCenter)
            self.center_layout.addWidget(sub)

        # Right spacer to balance back button
        spacer_r = QWidget()
        spacer_r.setFixedSize(36, 36)
        self.right_layout.addWidget(spacer_r)

    def set_preview_mode(self, title_text, close_callback):
        """Mode for Photo View: Title on left, Close button on right."""
        self.clear_slots()

        title = QLabel(title_text)
        title.setFont(QFont(FONT_SANS, 14, QFont.DemiBold))
        title.setStyleSheet(f"color: {INK_900}; background: transparent; border: none;")
        self.left_layout.addWidget(title)

        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_MUTED};
                color: {INK_900};
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #e2e3de; }}
        """)
        close_btn.clicked.connect(close_callback)
        self.right_layout.addWidget(close_btn)

    def clear_slots(self):
        """Remove all widgets from slots."""
        for layout in [self.left_layout, self.center_layout, self.right_layout]:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def scale_to(self, h):
        """Scales heights and fonts based on window height."""
        top_h = max(48, int(h * 0.038))
        self.setFixedHeight(top_h)

        # This would need more detailed font scaling if we want it perfect,
        # but for now we rely on the screen's resizeEvent calling this and
        # potentially updating child styles if needed.
        # Most screens already have their own scale_ui logic that finds children.
