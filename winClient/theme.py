"""Design System C — Editorial Claro · Stadium"""

FONT_SANS = "Segoe UI"  # Clean system font on Windows 10/11, similar weight to DM Sans

# ── Fondos ────────────────────────────────────────────────────────────────────
BG_PRIMARY   = "#f4f5f2"   # App background
BG_CARD      = "#ffffff"   # Surface / card
BG_MUTED     = "#eeefe9"   # Subtle muted fill (rgba 0,0,0 @ 6%)

# ── Texto ─────────────────────────────────────────────────────────────────────
INK_900      = "#0a1a0e"   # Primary text
INK_600      = "#5a7060"   # Secondary text
INK_400      = "#849c87"   # Muted text
INK_200      = "#b8cabb"   # Disabled text

# ── Acento verde ──────────────────────────────────────────────────────────────
GREEN_500    = "#00c45c"   # Accent primary
GREEN_600    = "#00a44e"   # Accent dark
GREEN_BG     = "#e3f9ee"   # Green fill (selection bg)
GREEN_BORDER = "#99e8c2"   # Green border (selected state)

# ── Bordes ────────────────────────────────────────────────────────────────────
BORDER       = "#dedede"   # Subtle border
BORDER_LIGHT = "#f0f0ec"   # Very subtle border


def btn_primary(radius: int = 12, font_size: int = 14) -> str:
    return f"""
        QPushButton {{
            background-color: {INK_900};
            color: #ffffff;
            border: none;
            border-radius: {radius}px;
            font-family: '{FONT_SANS}';
            font-size: {font_size}px;
            font-weight: 600;
        }}
        QPushButton:hover   {{ background-color: #1a2e20; }}
        QPushButton:pressed {{ background-color: #060f08; }}
    """


def btn_secondary(radius: int = 12, font_size: int = 14) -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {INK_900};
            border: 1px solid {BORDER};
            border-radius: {radius}px;
            font-family: '{FONT_SANS}';
            font-size: {font_size}px;
            font-weight: 500;
        }}
        QPushButton:hover   {{ background-color: {BG_MUTED}; }}
        QPushButton:pressed {{ background-color: #e4e5e0; }}
    """


def btn_disabled_style(radius: int = 12, font_size: int = 14) -> str:
    return f"""
        QPushButton {{
            background-color: rgba(0,0,0,25);
            color: {INK_200};
            border: none;
            border-radius: {radius}px;
            font-family: '{FONT_SANS}';
            font-size: {font_size}px;
            font-weight: 600;
        }}
        QPushButton:disabled {{
            background-color: rgba(0,0,0,25);
            color: {INK_200};
        }}
    """


# Backward-compat constants used by existing imports
BTN_PRIMARY = btn_primary()
BTN_SECONDARY = btn_secondary()
LABEL_TITLE = f"QLabel {{ color: {INK_900}; font-family: '{FONT_SANS}'; font-weight: 700; font-size: 28px; }}"
LABEL_SUBTITLE = f"QLabel {{ color: {INK_600}; font-family: '{FONT_SANS}'; font-size: 16px; }}"
MAIN_WINDOW_STYLE = f"QMainWindow {{ background-color: {BG_PRIMARY}; }}"
