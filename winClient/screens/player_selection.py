"""
player_selection.py (PyQt5)
Pantalla de selección de jugadores en grid 2×2 con tarjetas circulares.
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QWidget, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPen
from PIL import Image, ImageDraw

from screens.base_screen import BaseScreen
from models.player_roster import ALL as PLAYERS, reset_selection
from config import BG, TEXT_WHITE, TEXT_DIM, ACCENT, BTN_DARK, WIN_W, WIN_H

_SPINNER_COLOR = QColor("#10B981")
_SPINNER_WIDTH = 3


# ── Spinner ───────────────────────────────────────────────────────────────────

class SelectionSpinner(QWidget):
    """Indeterminate arc spinner drawn with QPainter, animated via QPropertyAnimation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self._angle = 0

        self._anim = QPropertyAnimation(self, b"angle", self)
        self._anim.setStartValue(0)
        self._anim.setEndValue(360)
        self._anim.setDuration(900)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Linear)

        self.hide()

    # ── pyqtProperty so QPropertyAnimation can drive it ──────────────────

    @pyqtProperty(int)
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value % 360
        self.update()

    # ── Public API ────────────────────────────────────────────────────────

    def start(self):
        self._anim.start()
        self.show()
        self.raise_()

    def stop(self):
        self._anim.stop()
        self.hide()

    # ── Drawing ───────────────────────────────────────────────────────────

    def paintEvent(self, event):
        size = min(self.width(), self.height())
        if size < 6:
            return

        margin = _SPINNER_WIDTH + 1
        rect_size = size - margin * 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(_SPINNER_COLOR, _SPINNER_WIDTH, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        x = (self.width()  - rect_size) // 2
        y = (self.height() - rect_size) // 2

        # Arc: 120° span rotating with _angle. Qt angles are in 1/16°.
        start_angle = (90 - self._angle) * 16   # start at top, rotate CW
        span_angle  = -120 * 16                  # 120° arc, clockwise
        painter.drawArc(x, y, rect_size, rect_size, start_angle, span_angle)
        painter.end()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _circle_image(path, size=110):
    try:
        img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    except Exception:
        img = Image.new("RGBA", (size, size), "#333333")

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, mask=mask)
    return result


def _pil_to_qpixmap(pil_img):
    import io
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    px = QPixmap()
    px.loadFromData(buf.getvalue(), "PNG")
    return px


# ── Card ──────────────────────────────────────────────────────────────────────

_CARD_W        = 340 # Aumentado significativamente
_CARD_H        = 400 # Aumentado significativamente
_IMG_SIZE      = 280 # Aumentado significativamente
_RADIUS        = 24
_SPINNER_GAP   = 4   
_SPINNER_SIZE  = _IMG_SIZE + 2 * (_SPINNER_GAP + _SPINNER_WIDTH)


class PlayerCardFrame(QFrame):
    """Tarjeta de jugador con imagen circular, nombre y spinner de selección."""

    def __init__(self, player, on_toggle, parent=None):
        super().__init__(parent)
        self.player    = player
        self.on_toggle = on_toggle
        self.setFrameStyle(QFrame.NoFrame)
        self.setFixedSize(_CARD_W, _CARD_H)
        self._apply_style(selected=False)
        self.setCursor(__import__("PyQt5.QtGui", fromlist=["QCursor"]).QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        # Portrait
        pil_img = _circle_image(str(player.image_path), size=_IMG_SIZE)
        pixmap  = _pil_to_qpixmap(pil_img)

        self._img_label = QLabel(self)
        self._img_label.setPixmap(pixmap)
        self._img_label.setFixedSize(_IMG_SIZE, _IMG_SIZE)
        self._img_label.setAlignment(Qt.AlignCenter)
        self._img_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._img_label, alignment=Qt.AlignCenter)

        # Name
        self._name_label = QLabel(player.name, self)
        self._name_label.setAlignment(Qt.AlignCenter)
        self._name_label.setFont(QFont("Arial", 18, QFont.Bold)) # Letra más grande
        self._name_label.setWordWrap(True)
        self._name_label.setStyleSheet(
            f"color: {TEXT_WHITE}; background: transparent; border: none;"
        )
        layout.addWidget(self._name_label, alignment=Qt.AlignCenter)

        self.setLayout(layout)

        # Spinner — transparent overlay, positioned after layout resolves
        self._spinner = SelectionSpinner(self)
        QTimer.singleShot(0, self._place_spinner)

    def _place_spinner(self):
        """Size spinner to encircle the portrait and align to its actual geometry."""
        geo = self._img_label.geometry()
        if geo.width() > 0:
            cx, cy = geo.center().x(), geo.center().y()
        else:
            cx = self.width() // 2
            cy = 10 + _IMG_SIZE // 2          # top-margin + half portrait
        s = _SPINNER_SIZE
        self._spinner.setGeometry(cx - s // 2, cy - s // 2, s, s)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_spinner()

    def mousePressEvent(self, event):
        self.on_toggle()

    def _apply_style(self, selected: bool):
        border_color = ACCENT if selected else "#333333"
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1a1a1a;
                border: 3px solid {border_color};
                border-radius: {_RADIUS}px;
            }}
        """)

    def set_selected(self, selected: bool):
        self._apply_style(selected)
        if selected:
            self._spinner.start()
        else:
            self._spinner.stop()


# ── Screen ────────────────────────────────────────────────────────────────────

class PlayerSelectionScreen(BaseScreen):
    """Pantalla de selección de jugadores en grid 2×2."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        reset_selection()
        self._cards = []
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 48, 20, 40)
        main_layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        self._title = QLabel("ELIGE TUS JUGADORES")
        self._title.setFont(QFont("Arial Black", 80, QFont.Bold)) # Aumentado
        self._title.setStyleSheet(f"color: {TEXT_WHITE};")
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        main_layout.addWidget(self._title)

        self._subtitle = QLabel("Selecciona los jugadores que aparecerán en tu foto")
        self._subtitle.setFont(QFont("Arial", 28)) # Aumentado
        self._subtitle.setStyleSheet(f"color: {TEXT_DIM};")
        self._subtitle.setAlignment(Qt.AlignCenter)
        self._subtitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        main_layout.addWidget(self._subtitle)
        main_layout.addSpacing(6)

        self._lbl_count = QLabel("0 seleccionados")
        self._lbl_count.setFont(QFont("Arial", 14))
        self._lbl_count.setStyleSheet(f"color: {ACCENT};")
        self._lbl_count.setAlignment(Qt.AlignCenter)
        self._lbl_count.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        main_layout.addWidget(self._lbl_count)
        main_layout.addSpacing(20)

        # ── Grid 2×2 ──────────────────────────────────────────────────────
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(16)
        grid_layout.setVerticalSpacing(16)
        grid_layout.setAlignment(Qt.AlignCenter)

        for idx, player in enumerate(PLAYERS):
            row, col = divmod(idx, 2)
            card = PlayerCardFrame(player, lambda p=player: self._toggle_player(p))
            self._cards.append(card)
            grid_layout.addWidget(card, row, col)

        grid_widget = QWidget()
        grid_widget.setLayout(grid_layout)
        grid_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(grid_widget, 1, Qt.AlignCenter)
        main_layout.addSpacing(20)

        # ── Continue button ───────────────────────────────────────────────
        self._btn_continue = QPushButton("CONTINUAR")
        self._btn_continue.setFont(QFont("Arial", 36, QFont.Bold)) # Aumentado
        self._btn_continue.setMinimumSize(500, 120) # Más grande
        self._btn_continue.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._btn_continue.setEnabled(False)
        self._btn_continue.clicked.connect(self._on_continue)
        self._update_continue_button(0)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_continue)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        wrapper = QWidget()
        wrapper.setLayout(main_layout)
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        wrapper_layout = QVBoxLayout()
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(wrapper)
        self.setLayout(wrapper_layout)

    # ── Toggle ────────────────────────────────────────────────────────────

    def _toggle_player(self, player):
        player.selected = not player.selected

        idx = PLAYERS.index(player)
        self._cards[idx].set_selected(player.selected)

        count = sum(1 for p in PLAYERS if p.selected)
        self._lbl_count.setText(
            f"{count} {'seleccionado' if count == 1 else 'seleccionados'}"
        )
        self._update_continue_button(count)

    # ── Resize / Typography ───────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        h = self.height()
        fs_title    = max(14, int(h * 0.028))
        fs_subtitle = max(10, int(h * 0.016))
        fs_count    = max(10, int(h * 0.018))
        fs_btn      = max(12, int(h * 0.022))
        btn_h       = max(48, int(h * 0.072))
        btn_radius  = btn_h // 2

        self._title.setFont(QFont("Arial Black", fs_title, QFont.Bold))
        self._subtitle.setFont(QFont("Arial", fs_subtitle))
        self._lbl_count.setFont(QFont("Arial", fs_count))
        self._btn_continue.setMinimumHeight(btn_h)
        self._btn_continue.setFont(QFont("Arial Black", fs_btn, QFont.Bold))
        self._apply_btn_style(btn_radius)

    # ── Button style ──────────────────────────────────────────────────────

    def _apply_btn_style(self, radius: int):
        if self._btn_continue.isEnabled():
            self._btn_continue.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACCENT};
                    color: #FFFFFF;
                    border: none;
                    border-radius: {radius}px;
                    font-weight: bold;
                }}
                QPushButton:hover   {{ background-color: #059669; }}
                QPushButton:pressed {{ background-color: #047857; }}
            """)
        else:
            self._btn_continue.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BTN_DARK};
                    color: #888888;
                    border: none;
                    border-radius: {radius}px;
                    font-weight: bold;
                }}
                QPushButton:disabled {{
                    background-color: {BTN_DARK};
                    color: #888888;
                }}
            """)

    def _update_continue_button(self, count):
        self._btn_continue.setEnabled(count > 0)
        btn_h = self._btn_continue.minimumHeight() or 56
        self._apply_btn_style(btn_h // 2)

    def _on_continue(self):
        selected = [p for p in PLAYERS if p.selected]
        self.app.show_loading(selected)
