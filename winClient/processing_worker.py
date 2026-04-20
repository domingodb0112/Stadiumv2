import cv2
import numpy as np
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
from segmentation_engine import SegmentationEngine, apply_mask


class ProcessingWorker(QThread):
    """Worker thread para procesamiento de foto en background."""

    finished = pyqtSignal(str)  # Emite ruta de imagen final
    error = pyqtSignal(str)     # Emite mensaje de error

    def __init__(
        self,
        captured_photo_path: str,
        background_path: str,
        output_path: str,
        ref_width: int = 1080,
        ref_height: int = 1920,
    ):
        """
        Args:
            captured_photo_path: Ruta a la foto capturada.
            background_path: Ruta a cancha.png.
            output_path: Ruta donde guardar la imagen final.
            ref_width, ref_height: Resolución de salida (1080x1920).
        """
        super().__init__()
        self.captured_photo_path = captured_photo_path
        self.background_path = background_path
        self.output_path = output_path
        self.ref_width = ref_width
        self.ref_height = ref_height
        self.segmentation_engine = SegmentationEngine(model_selection=0)

    def run(self) -> None:
        """Procesa la imagen en background."""
        try:
            # Cargar imágenes
            captured_img = cv2.imread(self.captured_photo_path)
            background_img = cv2.imread(self.background_path)

            if captured_img is None:
                self.error.emit(f"No se pudo cargar foto: {self.captured_photo_path}")
                return

            if background_img is None:
                self.error.emit(f"No se pudo cargar fondo: {self.background_path}")
                return

            # Redimensionar captura a resolución de referencia
            captured_resized = cv2.resize(
                captured_img, (self.ref_width, self.ref_height)
            )

            # Generar máscara del usuario
            mask = self.segmentation_engine.process(captured_resized)

            # Redimensionar fondo a resolución de referencia si es necesario
            bg_resized = cv2.resize(
                background_img, (self.ref_width, self.ref_height)
            )

            # Aplicar máscara y fusionar
            result_img = apply_mask(
                frame=captured_resized,
                background_img=bg_resized,
                mask=mask,
                blur_kernel=7,
            )

            # Guardar imagen final
            output_dir = Path(self.output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            success = cv2.imwrite(self.output_path, result_img)
            if not success:
                self.error.emit(f"Error al guardar: {self.output_path}")
                return

            # Liberar recursos
            self.segmentation_engine.release()

            # Emitir señal de finalización
            self.finished.emit(self.output_path)

        except Exception as e:
            self.error.emit(f"Error en procesamiento: {str(e)}")
            self.segmentation_engine.release()
