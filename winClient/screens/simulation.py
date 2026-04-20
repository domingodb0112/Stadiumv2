import threading
import time as _t
import cv2

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont

from screens.base_screen import BaseScreen
from config import BG, ACCENT, TEXT_WHITE, TEXT_DIM, SIMULATION_MS, PHOTOS_DIR, REF_W, REF_H, OUTPUT_DIR
from network_client import NetworkClient


class ProcessingWorker(QObject):
    """Worker para procesar la foto en background sin bloquear la UI."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, photo_path: str):
        super().__init__()
        self._photo_path = photo_path

    def run(self):
        """Procesa la foto: mezcla cancha (30%) + usuario (70%)."""
        try:
            cancha_path = str(PHOTOS_DIR / "cancha.png")
            user_mat = cv2.imread(self._photo_path)
            cancha_mat = cv2.imread(cancha_path)

            if user_mat is None:
                self.error.emit("No se pudo cargar la foto del usuario")
                return

            # Redimensionar ambas a 1080×1920
            user_mat = cv2.resize(user_mat, (REF_W, REF_H))

            if cancha_mat is not None:
                cancha_mat = cv2.resize(cancha_mat, (REF_W, REF_H))
                # Mezcla: 30% estadio + 70% usuario
                result = cv2.addWeighted(cancha_mat, 0.3, user_mat, 0.7, 0)
            else:
                result = user_mat

            # Guardar resultado
            out_path = str(OUTPUT_DIR / f"final_{int(_t.time())}.jpg")
            cv2.imwrite(out_path, result, [cv2.IMWRITE_JPEG_QUALITY, 95])
            self.finished.emit(out_path)

        except Exception as e:
            self.error.emit(f"Error en procesado: {str(e)}")


class SimulationScreen(BaseScreen):
    """
    Pantalla de carga '¡SALIENDO AL CAMPO!' con barra de progreso.
    Mientras avanza la barra (6 segundos), procesa la foto en background
    (mezcla cancha.png 30% + foto usuario 70%).
    Al terminar, navega a la pantalla final.
    """

    def __init__(self, app, photo_path: str, players, **kwargs):
        super().__init__(app, **kwargs)
        self._photo_path = photo_path
        self._players = players
        self._final_path = photo_path
        self._qr_base64 = None
        self._processing_done = False
        self._animation_done = False

        self._build_ui()
        self._start_animation()
        self._start_processing()

    def _build_ui(self):
        """Construye la interfaz PyQt5."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Frame central - sin background visible
        center_frame = QFrame()
        center_frame.setStyleSheet("background-color: transparent; border: none;")
        center_layout = QVBoxLayout()
        center_layout.setSpacing(20)
        center_layout.setContentsMargins(40, 0, 40, 0)

        # Título: "¡SALIENDO AL CAMPO!"
        title = QLabel("¡SALIENDO AL CAMPO!")
        title_font = QFont("Arial Black", 40, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {ACCENT}; background-color: transparent;")
        title.setAlignment(Qt.AlignCenter)
        center_layout.addSpacing(100)
        center_layout.addWidget(title)

        # Subtítulo
        subtitle = QLabel(
            "Tus ídolos están saltando al césped…\nPreparando el encuentro histórico."
        )
        subtitle_font = QFont("Arial", 14)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet(f"color: {TEXT_WHITE}; background-color: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        center_layout.addSpacing(30)
        center_layout.addWidget(subtitle)

        # Barra de progreso
        center_layout.addSpacing(40)
        self._progress = QProgressBar()
        self._progress.setMaximum(100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(12)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #333333;
                border: none;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
                border-radius: 6px;
            }}
        """)
        center_layout.addWidget(self._progress)

        # Label de estado
        center_layout.addSpacing(12)
        self._status_label = QLabel("6 segundos para la gloria…")
        status_font = QFont("Arial", 11)
        self._status_label.setFont(status_font)
        self._status_label.setStyleSheet(f"color: {TEXT_DIM}; background-color: transparent;")
        self._status_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self._status_label)

        center_layout.addSpacing(100)
        center_frame.setLayout(center_layout)

        main_layout.addWidget(center_frame)
        self.setLayout(main_layout)

    def _start_animation(self):
        """Inicia el temporizador para la animación de progreso (6 segundos)."""
        self._elapsed_ms = 0
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_progress)
        self._animation_timer.start(50)  # Actualizar cada 50ms

    def _update_progress(self):
        """Actualiza la barra de progreso."""
        self._elapsed_ms += 50

        # Calcular progreso (0-100%)
        progress = min(self._elapsed_ms / SIMULATION_MS, 1.0)
        self._progress.setValue(int(progress * 100))

        # Actualizar label
        remaining_s = max(0, (SIMULATION_MS - self._elapsed_ms) / 1000)
        if remaining_s > 0.1:
            self._status_label.setText(f"{remaining_s:.1f} segundos para la gloria…")

        # Si se completó la animación
        if self._elapsed_ms >= SIMULATION_MS:
            self._animation_timer.stop()
            self._animation_done = True
            self._status_label.setText("¡Procesando…!")
            self._check_ready()

    def _check_ready(self):
        """Espera a que procesado + upload terminen, luego navega a pantalla final."""
        if self._processing_done:
            self.app.show_final(self._final_path, self._qr_base64)
        else:
            QTimer.singleShot(100, self._check_ready)

    def _start_processing(self):
        """Inicia procesado de foto y upload en paralelo en threads separados."""
        self._worker = ProcessingWorker(self._photo_path)
        self._worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self._worker_thread.start()

    def _run_worker(self):
        """Procesa la foto y luego la sube al servidor."""
        self._worker.finished.connect(self._on_processing_finished)
        self._worker.error.connect(self._on_processing_error)
        self._worker.run()

    def _on_processing_finished(self, final_path: str):
        """Cuando el procesado termina, sube la foto y obtiene el QR."""
        self._final_path = final_path
        print(f"[SimulationScreen] Foto procesada: {final_path}")
        # Upload en el mismo thread de background para no bloquear UI
        success, qr, error = NetworkClient.upload_photo(final_path)
        if success:
            self._qr_base64 = qr
            print("[SimulationScreen] QR recibido del servidor")
        else:
            print(f"[SimulationScreen] Upload falló: {error}")
        self._processing_done = True

    def _on_processing_error(self, error_msg: str):
        """Si falla el procesado, intenta subir la foto original."""
        print(f"[SimulationScreen] Procesado falló: {error_msg}")
        success, qr, error = NetworkClient.upload_photo(self._photo_path)
        if success:
            self._qr_base64 = qr
        else:
            print(f"[SimulationScreen] Upload falló: {error}")
        self._processing_done = True

    def on_destroy(self):
        """Libera recursos cuando se cierra la pantalla."""
        if hasattr(self, '_animation_timer') and self._animation_timer.isActive():
            self._animation_timer.stop()
        if hasattr(self, '_worker_thread') and self._worker_thread.is_alive():
            # El thread daemon se detiene automáticamente
            pass
