from pathlib import Path

# ── Ventana ───────────────────────────────────────────────────────────────────
WIN_W = 540
WIN_H = 960

# ── Resolución de referencia (igual que Android) ─────────────────────────────
REF_W = 1080
REF_H = 1920

# ── Paleta de colores (idéntica al tema Android) ─────────────────────────────
BG          = "#000000"
PRIMARY     = "#064E3B"   # deep forest green
ACCENT      = "#10B981"   # emerald green
TEXT_WHITE  = "#FFFFFF"
TEXT_DIM    = "#888888"
BTN_DARK    = "#444444"

# ── Rutas ─────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent
ASSETS_DIR = ROOT / "assets"
VIDEOS_DIR = ASSETS_DIR / "videos"
PHOTOS_DIR = ASSETS_DIR / "photos"
OUTPUT_DIR = ROOT / "output"

# Asegurar que existan los directorios
for d in [VIDEOS_DIR, PHOTOS_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Countdown de la cámara (segundos)
COUNTDOWN_SEC = 5

# Duración de la pantalla de simulación (ms)
SIMULATION_MS = 6000

# Auto-envío en PhotoView (ms)
AUTO_SEND_MS = 5000
