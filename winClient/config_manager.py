import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConfigManager:
    """Gestor centralizado de configuración desde JSON externo."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: Ruta al archivo config.json.
                        Si es None, busca en la carpeta de la app.
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Carga el archivo config.json."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    def reload(self) -> None:
        """Recarga la configuración desde disco."""
        self.load()

    def get_overlay(self, slot: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de un overlay por slot.

        Args:
            slot: ID del slot (0, 1, 2, ...)

        Returns:
            Dict con {name, video_path, x, y, w, h} o None si no existe.
        """
        overlays = self._config.get("overlays", [])
        if 0 <= slot < len(overlays):
            return overlays[slot]
        return None

    def get_overlays(self) -> List[Dict[str, Any]]:
        """Retorna la lista completa de overlays."""
        return self._config.get("overlays", [])

    def get_app_config(self) -> Dict[str, Any]:
        """Retorna configuración general de la app."""
        return self._config.get("app", {})

    def get_value(self, key: str, default: Any = None) -> Any:
        """Acceso genérico a cualquier clave en config."""
        return self._config.get(key, default)
