"""
player_selection.py — Design System C (Editorial Claro)
Grid 2-column player cards with check-badge selection state.
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QWidget, QFrame, QSizePolicy, QScrollArea,
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QBrush

from PIL import Image, ImageDraw
import io

from screens.base_screen import BaseScreen
from models.player_roster import ALL as PLAYERS, reset_selection
from ui_components import GradientBar, CheckBadge, TopBar
from theme import (
    FONT_SANS, BG_PRIMARY, BG_CARD, BG_MUTED, INK_900, INK_400, INK_600,
    INK_200, GREEN_500, GREEN_600, GREEN_BG, GREEN_BORDER, BORDER,
    btn_primary, btn_disabled_style,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _circle_image(path, size=80):
    try:
        img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    except Exception:
        img = Image.new("RGBA", (size, size), "#cccccc")

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, mask=mask)
    return result


def _pil_to_qpixmap(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    px = QPixmap()
    px.loadFromData(buf.getvalue(), "PNG")
    return px


# ── Player card ───────────────────────────────────────────────────────────────

class PlayerCardFrame(QFrame):
    """Card with avatar, name, position — selected state has green border + check badge."""

    IMG_SIZE = 80   # logical default; rescaled in _refresh_layout

    def __init__(self, player, on_toggle, parent=None):
        super().__init__(parent)
        self.player    = player
        self.on_toggle = on_toggle
        self._selected = False
        self.setFrameStyle(QFrame.NoFrame)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self):
        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignCenter)
        self._layout.setContentsMargins(12, 16, 12, 12)
        self._layout.setSpacing(8)

        # Avatar (circle)
        self._avatar_lbl = QLabel()
        self._avatar_lbl.setAlignment(Qt.AlignCenter)
        self._avatar_lbl.setStyleSheet("background: transparent; border: none;")
        self._layout.addWidget(self._avatar_lbl, alignment=Qt.AlignCenter)

        # Name
        self._name_lbl = QLabel(self.player.name)
        self._name_lbl.setFont(QFont(FONT_SANS, 13, QFont.Bold))
        self._name_lbl.setAlignment(Qt.AlignCenter)
        self._name_lbl.setWordWrap(True)
        self._name_lbl.setStyleSheet(
            f"color: {INK_900}; background: transparent; border: none;"
        )
        self._layout.addWidget(self._name_lbl)

        # Position label
        pos_text = getattr(self.player, "position", "Jugador")
        self._pos_lbl = QLabel(pos_text)
        self._pos_lbl.setFont(QFont(FONT_SANS, 11))
        self._pos_lbl.setAlignment(Qt.AlignCenter)
        self._pos_lbl.setStyleSheet(
            f"color: {INK_400}; background: transparent; border: none;"
        )
        self._layout.addWidget(self._pos_lbl)

        # Check badge (hidden by default, shown on selection)
        self._badge = CheckBadge(parent=self)
        self._badge.hide()

        self._load_avatar(self.IMG_SIZE)
        self._apply_style()

    def _load_avatar(self, size: int):
        pil = _circle_image(str(self.player.image_path), size=size)
        px  = _pil_to_qpixmap(pil)
        self._avatar_lbl.setPixmap(px)
        self._avatar_lbl.setFixedSize(size, size)

    def _apply_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG_CARD};
                    border: 2px solid {GREEN_500};
                    border-radius: 16px;
                }}
            """)
            self._pos_lbl.setStyleSheet(
                f"color: {GREEN_600}; background: transparent; border: none;"
            )
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG_MUTED};
                    border: 2px solid transparent;
                    border-radius: 16px;
                }}
            """)
            self._pos_lbl.setStyleSheet(
                f"color: {INK_400}; background: transparent; border: none;"
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Place badge at top-right
        bw = self._badge.width()
        bh = self._badge.height()
        self._badge.move(self.width() - bw - 8, 8)

    def mousePressEvent(self, event):
        self.on_toggle()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style()
        if selected:
            self._badge.show()
            self._badge.raise_()
        else:
            self._badge.hide()

    def set_img_size(self, size: int):
        """Rescale avatar when card is resized by parent."""
        if size != self.IMG_SIZE:
            PlayerCardFrame.IMG_SIZE = size
            self._load_avatar(size)


# ── Screen ────────────────────────────────────────────────────────────────────

class PlayerSelectionScreen(BaseScreen):

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        reset_selection()
        self._cards = []
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Top bar ───────────────────────────────────────────────────────────
        self._top_bar = TopBar()
        self._top_bar.set_brand_mode()
        outer.addWidget(self._top_bar)

        # ── Header ────────────────────────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet(f"background-color: {BG_PRIMARY};")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 20, 24, 12)
        hl.setSpacing(0)

        self._lbl_title = QLabel("Elige tus\njugadores")
        self._lbl_title.setFont(QFont(FONT_SANS, 32, QFont.Black))
        self._lbl_title.setStyleSheet(
            f"color: {INK_900}; background: transparent; border: none;"
        )
        hl.addWidget(self._lbl_title)
        hl.addSpacing(12)

        self._underline = QWidget()
        self._underline.setStyleSheet(f"background-color: {GREEN_500}; border-radius: 2px;")
        hl.addWidget(self._underline, alignment=Qt.AlignLeft)
        hl.addSpacing(12)

        self._lbl_sub = QLabel("Selecciona quién aparecerá en tu foto")
        self._lbl_sub.setFont(QFont(FONT_SANS, 13))
        self._lbl_sub.setStyleSheet(
            f"color: {INK_400}; background: transparent; border: none;"
        )
        hl.addWidget(self._lbl_sub)
        hl.addSpacing(8)

        # Counter row
        count_row = QHBoxLayout()
        count_row.setSpacing(6)
        self._dot_count = QLabel()
        self._dot_count.setStyleSheet(
            f"background-color: rgba(0,0,0,51); border-radius: 3px;"
        )
        count_row.addWidget(self._dot_count, alignment=Qt.AlignVCenter)

        self._lbl_count = QLabel("Ninguno seleccionado")
        self._lbl_count.setFont(QFont(FONT_SANS, 13, QFont.DemiBold))
        self._lbl_count.setStyleSheet(
            f"color: {INK_400}; background: transparent; border: none;"
        )
        count_row.addWidget(self._lbl_count)
        count_row.addStretch()
        hl.addLayout(count_row)

        outer.addWidget(header)

        # ── Grid ──────────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {BG_PRIMARY}; border: none;")
        scroll.verticalScrollBar().setStyleSheet(
            "QScrollBar { width: 0px; }"
        )

        grid_container = QWidget()
        grid_container.setStyleSheet(f"background-color: {BG_PRIMARY};")
        self._grid = QGridLayout(grid_container)
        self._grid.setContentsMargins(16, 8, 16, 8)
        self._grid.setHorizontalSpacing(10)
        self._grid.setVerticalSpacing(10)

        for idx, player in enumerate(PLAYERS):
            row, col = divmod(idx, 2)
            card = PlayerCardFrame(player, lambda p=player: self._toggle(p))
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._cards.append(card)
            self._grid.addWidget(card, row, col)

        scroll.setWidget(grid_container)
        outer.addWidget(scroll, 1)

        # ── Bottom CTA ────────────────────────────────────────────────────────
        bottom = QWidget()
        bottom.setStyleSheet(
            f"background-color: {BG_PRIMARY}; "
            f"border-top: 1px solid rgba(0,0,0,30);"
        )
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(16, 12, 16, 12)

        self._btn_continue = QPushButton("Continuar")
        self._btn_continue.setFont(QFont(FONT_SANS, 14, QFont.DemiBold))
        self._btn_continue.setEnabled(False)
        self._btn_continue.setCursor(Qt.PointingHandCursor)
        self._btn_continue.clicked.connect(self._on_continue)
        bl.addWidget(self._btn_continue)

        outer.addWidget(bottom)
        outer.addWidget(GradientBar(height=4))
        self.setLayout(outer)

        self._update_continue(0)
        self._scale_fonts(self.height() or 1920)

    # ── Toggle ────────────────────────────────────────────────────────────────

    def _toggle(self, player):
        player.selected = not player.selected
        idx = PLAYERS.index(player)
        self._cards[idx].set_selected(player.selected)
        count = sum(1 for p in PLAYERS if p.selected)
        self._lbl_count.setText(
            "Ninguno seleccionado" if count == 0
            else f"{count} seleccionado{'s' if count > 1 else ''}"
        )
        dot_color = GREEN_500 if count > 0 else "rgba(0,0,0,51)"
        dot_size = self._dot_count.width()
        self._dot_count.setStyleSheet(
            f"background-color: {dot_color}; border-radius: {dot_size // 2}px;"
        )
        lbl_color = GREEN_600 if count > 0 else INK_400
        self._lbl_count.setStyleSheet(
            f"color: {lbl_color}; background: transparent; border: none;"
        )
        self._update_continue(count)

    def _update_continue(self, count: int):
        self._btn_continue.setEnabled(count > 0)
        h = self._btn_continue.height() or 54
        r = max(10, h // 2 - 2)
        fs = self._btn_continue.font().pointSize() or 14
        if count > 0:
            self._btn_continue.setText("Continuar  →")
            self._btn_continue.setStyleSheet(btn_primary(radius=r, font_size=fs))
        else:
            self._btn_continue.setText("Continuar")
            self._btn_continue.setStyleSheet(btn_disabled_style(radius=r, font_size=fs))

    def _on_continue(self):
        selected = [p for p in PLAYERS if p.selected]
        self.app.show_loading(selected)

    # ── Scaling ───────────────────────────────────────────────────────────────

    def _scale_fonts(self, h: int):
        # Scale TopBar
        if hasattr(self, "_top_bar"):
            self._top_bar.scale_to(h)

        title_pt   = max(18, int(h * 0.04))
        sub_pt     = max(10, int(h * 0.010))
        count_pt   = max(10, int(h * 0.010))
        ul_w       = max(24, int(h * 0.022))
        ul_h       = max(2,  int(h * 0.002))
        btn_h      = max(48, int(h * 0.045))
        btn_pt     = max(12, int(h * 0.011))
        btn_r      = max(10, int(h * 0.013))
        cdot_size  = max(5,  int(h * 0.005))
        badge_size = max(16, int(h * 0.018))
        img_size   = max(56, int(h * 0.066))

        self._lbl_title.setFont(QFont(FONT_SANS, title_pt, QFont.Black))
        self._lbl_sub.setFont(QFont(FONT_SANS, sub_pt))
        self._underline.setFixedSize(ul_w, ul_h)

        self._dot_count.setFixedSize(cdot_size, cdot_size)
        self._lbl_count.setFont(QFont(FONT_SANS, count_pt, QFont.DemiBold))

        self._btn_continue.setFixedHeight(btn_h)
        self._btn_continue.setFont(QFont(FONT_SANS, btn_pt, QFont.DemiBold))

        count = sum(1 for p in PLAYERS if p.selected)
        if count > 0:
            self._btn_continue.setStyleSheet(btn_primary(radius=btn_r, font_size=btn_pt))
        else:
            self._btn_continue.setStyleSheet(btn_disabled_style(radius=btn_r, font_size=btn_pt))

        # Resize cards and their badges
        for i, card in enumerate(self._cards):
            card._name_lbl.setFont(QFont(FONT_SANS, max(10, int(h * 0.010)), QFont.Bold))
            card._pos_lbl.setFont(QFont(FONT_SANS, max(9, int(h * 0.009))))
            # Resize check badge
            card._badge.setFixedSize(badge_size, badge_size)
            card.set_img_size(img_size)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_fonts(self.height())
