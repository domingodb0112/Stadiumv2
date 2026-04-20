"""
network_client.py
Sube la foto al servidor y retorna la imagen del QR.
"""
import threading
import requests
from PIL import Image
import io


SERVER_URL = "https://img.mirasintind.org/"   # <-- cambia esta URL


def upload_photo(photo_path: str,
                 on_success,   # callback(pil_image_qr)
                 on_error):    # callback(error_msg: str)
    """Sube la foto en un hilo de fondo para no bloquear la UI."""
    def _run():
        try:
            with open(photo_path, 'rb') as f:
                resp = requests.post(
                    SERVER_URL,
                    files={"photo": ("photo.jpg", f, "image/jpeg")},
                    timeout=30
                )
            if resp.status_code == 200:
                qr_img = Image.open(io.BytesIO(resp.content))
                on_success(qr_img)
            else:
                on_error(f"Error: {resp.status_code}")
        except Exception as e:
            on_error(str(e))

    threading.Thread(target=_run, daemon=True).start()
