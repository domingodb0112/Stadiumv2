"""
player_roster.py
Carga el catálogo de jugadores desde un archivo JSON externo.
"""
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from config import VIDEOS_DIR, PHOTOS_DIR, ASSETS_DIR


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


def _load_players() -> List[Player]:
    json_path = ASSETS_DIR / "players.json"
    if not json_path.exists():
        print(f"[!] players.json not found at {json_path}")
        return []

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        roster = []
        for item in data:
            p = Player(
                id=item["id"],
                name=item["name"],
                image_path=PHOTOS_DIR / item["image_name"],
                video_path=VIDEOS_DIR / item["video_name"],
                slot=item["slot"],
                x=item["x"],
                y=item["y"],
                w=item["w"],
                h=item["h"]
            )
            roster.append(p)
        return roster
    except Exception as e:
        print(f"[!] Error loading players.json: {e}")
        return []


# Carga inicial del catálogo
ALL: List[Player] = _load_players()


def find_by_slot(slot: int) -> Optional[Player]:
    return next((p for p in ALL if p.slot == slot), None)


def reset_selection():
    for p in ALL:
        p.selected = False


def refresh_roster():
    """Recarga el catálogo desde el JSON (útil para actualizaciones en caliente)."""
    global ALL
    ALL = _load_players()
