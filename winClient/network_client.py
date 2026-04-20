import requests
from typing import Optional, Tuple
from pathlib import Path

_UPLOAD_URL = "http://img.mirasintind.org/subir-foto"
_TIMEOUT    = 30


class NetworkClient:
    """Cliente HTTP para upload de fotos y recepción de QR."""

    @staticmethod
    def upload_photo(image_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        POST multipart/form-data a /subir-foto.

        Returns:
            (success, qr_base64, error_msg)
        """
        path = Path(image_path)
        if not path.exists():
            return False, None, f"Archivo no encontrado: {image_path}"

        try:
            with path.open("rb") as fh:
                response = requests.post(
                    _UPLOAD_URL,
                    files={"file": (path.name, fh, "image/jpeg")},
                    timeout=_TIMEOUT,
                )
            response.raise_for_status()

            data = response.json()
            qr_base64 = data.get("qr_base64") or data.get("qr")

            if not qr_base64:
                return False, None, f"Campo QR ausente en respuesta: {list(data.keys())}"

            return True, qr_base64, None

        except requests.exceptions.ConnectionError:
            return False, None, "Sin conexión al servidor"
        except requests.exceptions.Timeout:
            return False, None, f"Timeout tras {_TIMEOUT}s"
        except requests.exceptions.HTTPError as e:
            return False, None, f"HTTP {e.response.status_code}: {e.response.text[:120]}"
        except ValueError as e:
            return False, None, f"JSON inválido: {e}"
        except Exception as e:
            return False, None, f"Error inesperado: {e}"
