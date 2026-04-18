"""
player_roster.py
Catálogo de jugadores — equivalente a PlayerRoster.java + Player.java de Android.

Para ajustar posiciones edita los valores x, y, w, h de cada jugador.
Resolución de referencia: 1080 x 1920 px.

  Player(id, nombre, imagen.png, video.mov, slot, x, y, w, h)
  x=0, y=0, w=1080, h=1920  →  ocupa toda la pantalla
"""
from pathlib import Path
from dataclasses import dataclass

from config import VIDEOS_DIR, PHOTOS_DIR, REF_W, REF_H


@dataclass
class Player:
    id:         int
    name:       str
    image_path: Path    # PNG para la pantalla de selección
    video_path: Path    # .mov con canal alfa
    slot:       int     # canal nativo fijo (0-3)
    x: int              # px desde borde izquierdo (ref 1080×1920)
    y: int              # px desde borde superior
    w: int              # ancho del overlay
    h: int              # alto  del overlay
    selected:   bool = False


#                           id  nombre            imagen                              video                slot   x   y      w     h
ALL: list[Player] = [
    Player(0, "Gilberto Mora",  PHOTOS_DIR / "gilbertoMoraGm.png",  VIDEOS_DIR / "gilbertoMora.mov",  0,  0,  0, 1080, 1920),
    Player(1, "Jorge Sánchez",  PHOTOS_DIR / "jorgeSanchezGm.png",  VIDEOS_DIR / "jorgeSanchez.mov",  1,  0,  0, 1080, 1920),
    Player(2, "Mateo Chávez",   PHOTOS_DIR / "mateoChavezGm.png",   VIDEOS_DIR / "mateoChavez.mov",   2,  0,  0, 1080, 1920),
    Player(3, "Raúl Rangel",    PHOTOS_DIR / "raulRangelGm.png",    VIDEOS_DIR / "raulRangel.mov",    3,  0,  0, 1080, 1920),
]


def find_by_slot(slot: int) -> Player | None:
    return next((p for p in ALL if p.slot == slot), None)


def reset_selection():
    for p in ALL:
        p.selected = False
