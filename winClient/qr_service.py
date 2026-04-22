import base64
from io import BytesIO
from PyQt5.QtGui import QPixmap, QImage
from typing import Optional


class QRService:
    """Servicio para decodificar y convertir QR en Base64 a QPixmap."""

    @staticmethod
    def base64_to_pixmap(base64_string: str, max_size: int = 400) -> Optional[QPixmap]:
        """
        Convierte string Base64 a QPixmap de PyQt5.

        Args:
            base64_string: String en Base64 (usualmente PNG).
            max_size: Tamaño máximo en píxeles para escalar el QR.

        Returns:
            QPixmap o None si hay error.
        """
        try:
            # Limpiar Base64 (remover prefijo data:image/...;base64, si existe)
            if "," in base64_string:
                base64_clean = base64_string.split(",")[1].strip()
            else:
                base64_clean = base64_string.strip()

            # Decodificar Base64 a bytes
            image_bytes = base64.b64decode(base64_clean)

            # Convertir bytes a QImage
            qimage = QImage()
            qimage.loadFromData(image_bytes)

            if qimage.isNull():
                return None

            # Convertir QImage a QPixmap
            pixmap = QPixmap.fromImage(qimage)

            # Escalar si es necesario para que quepa en max_size
            if pixmap.width() > max_size or pixmap.height() > max_size:
                pixmap = pixmap.scaled(
                    max_size, max_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

            return pixmap

        except Exception as e:
            print(f"Error decodificando QR: {str(e)}")
            return None

    @staticmethod
    def base64_to_file(
        base64_string: str, output_path: str
    ) -> bool:
        """
        Guarda QR desde Base64 a archivo PNG.

        Args:
            base64_string: String en Base64.
            output_path: Ruta donde guardar el PNG.

        Returns:
            True si se guardó exitosamente.
        """
        try:
            base64_clean = base64_string.strip()
            image_bytes = base64.b64decode(base64_clean)

            with open(output_path, "wb") as f:
                f.write(image_bytes)

            return True

        except Exception as e:
            print(f"Error guardando QR: {str(e)}")
            return False
