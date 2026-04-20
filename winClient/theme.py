"""Soccer Green Brand Theme for StadiumV3"""

# Colors
BG_PRIMARY     = "#000000"   # Black
BG_DARK        = "#1a1a1a"   # Dark gray
TEXT_PRIMARY   = "#FFFFFF"   # White
TEXT_SECONDARY = "#CCCCCC"   # Light gray
ACCENT         = "#10B981"   # Emerald Green
ACCENT_DARK    = "#064E3B"   # Deep Forest Green
ACCENT_MID     = "#059669"   # Mid Green (hover)
ACCENT_PRESS   = "#047857"   # Pressed Green

# Button Style Template
BUTTON_STYLE = """
QPushButton {{
    background-color: {bg_color};
    color: white;
    border: none;
    border-radius: 25px;
    font-family: Arial;
    font-weight: bold;
    font-size: 18px;
    padding: 15px 30px;
    min-width: 300px;
    min-height: 60px;
}}
QPushButton:hover {{
    background-color: {hover_color};
}}
QPushButton:pressed {{
    background-color: {pressed_color};
}}
"""

# Predefined Button Styles
BTN_PRIMARY = BUTTON_STYLE.format(
    bg_color=ACCENT,
    hover_color=ACCENT_MID,
    pressed_color=ACCENT_PRESS,
)

BTN_SECONDARY = BUTTON_STYLE.format(
    bg_color=ACCENT_DARK,
    hover_color="#0A6040",
    pressed_color="#043728",
)

# Label Styles
LABEL_TITLE = """
QLabel {
    color: white;
    font-family: Arial;
    font-weight: bold;
    font-size: 28px;
}
"""

LABEL_SUBTITLE = """
QLabel {
    color: #CCCCCC;
    font-family: Arial;
    font-size: 16px;
}
"""

# Main Window Style
MAIN_WINDOW_STYLE = f"""
QMainWindow {{
    background-color: {BG_PRIMARY};
}}
"""
