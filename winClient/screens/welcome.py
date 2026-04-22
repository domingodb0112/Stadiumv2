"""Welcome screen — Design System C (Editorial Claro)"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from screens.base_screen import BaseScreen
from ui_components import GradientBar, TopBar
from theme import (
    FONT_SANS, BG_PRIMARY, INK_900, INK_400, GREEN_500, GREEN_600,
    btn_primary,
)


class WelcomeScreen(BaseScreen):

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {BG_PRIMARY};")

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Top bar ───────────────────────────────────────────────────────────
        self._top_bar = TopBar()
        self._top_bar.set_brand_mode()
        outer.addWidget(self._top_bar)

        # ── Content ───────────────────────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"background-color: {BG_PRIMARY};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 0, 28, 0)
        cl.setSpacing(0)
        cl.addStretch(2)

        # "BIENVENIDO" label
        self._lbl_welcome = QLabel("BIENVENIDO")
        self._lbl_welcome.setFont(QFont(FONT_SANS, 13, QFont.DemiBold))
        self._lbl_welcome.setStyleSheet(
            f"color: {GREEN_600}; letter-spacing: 3px; background: transparent; border: none;"
        )
        cl.addWidget(self._lbl_welcome)
        cl.addSpacing(16)

        # Big title
        self._lbl_title = QLabel("Al\nJuego")
        self._lbl_title.setFont(QFont(FONT_SANS, 58, QFont.Black))
        self._lbl_title.setStyleSheet(
            f"color: {INK_900}; background: transparent; border: none;"
        )
        cl.addWidget(self._lbl_title)
        cl.addSpacing(20)

        # Green underline
        self._underline = QWidget()
        self._underline.setStyleSheet(
            f"background-color: {GREEN_500}; border-radius: 2px;"
        )
        cl.addWidget(self._underline, alignment=Qt.AlignLeft)
        cl.addSpacing(24)

        # Subtitle
        self._lbl_sub = QLabel("Tu historia comienza aquí.\nÚnete a la experiencia.")
        self._lbl_sub.setFont(QFont(FONT_SANS, 14))
        self._lbl_sub.setStyleSheet(
            f"color: {INK_400}; background: transparent; border: none;"
        )
        self._lbl_sub.setWordWrap(True)
        cl.addWidget(self._lbl_sub)
        cl.addStretch(3)

        # CTA button
        self._btn = QPushButton("Comenzar  →")
        self._btn.setFont(QFont(FONT_SANS, 14, QFont.DemiBold))
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(self.app.show_player_selection)
        cl.addWidget(self._btn)
        cl.addSpacing(32)

        outer.addWidget(content, 1)
        outer.addWidget(GradientBar(height=5))
        self.setLayout(outer)

        # Apply initial scale
        self._scale_fonts(self.height() or 1920)

    # ── Scaling ────────────────────────────────────────────────────────────────

    def _scale_fonts(self, h: int):
        title_pt   = max(28, int(h * 0.040))
        welcome_pt = max(10, int(h * 0.011))
        sub_pt     = max(10, int(h * 0.010))
        btn_pt     = max(12, int(h * 0.011))
        btn_h      = max(48, int(h * 0.045))
        radius     = max(10, int(h * 0.013))

        # Scale TopBar
        if hasattr(self, "_top_bar"):
            self._top_bar.scale_to(h)

        self._lbl_title.setFont(QFont(FONT_SANS, title_pt, QFont.Black))
        self._lbl_welcome.setFont(QFont(FONT_SANS, welcome_pt, QFont.DemiBold))
        self._lbl_sub.setFont(QFont(FONT_SANS, sub_pt))

        ul_w = max(32, int(h * 0.030))
        ul_h = max(2, int(h * 0.002))
        self._underline.setFixedSize(ul_w, ul_h)

        self._btn.setFont(QFont(FONT_SANS, btn_pt, QFont.DemiBold))
        self._btn.setFixedHeight(btn_h)
        self._btn.setStyleSheet(btn_primary(radius=radius, font_size=btn_pt))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_fonts(self.height())
