from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QFont
import cv2
import numpy as np
from pathlib import Path
from processing_worker import ProcessingWorker
from network_client import NetworkClient
from segmentation_engine import SegmentationEngine, apply_mask


class CameraScreen(QWidget):
    photo_captured = pyqtSignal(str)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.camera = None
        self.overlays = []
        self.processing_worker = None
        self.final_screen = None
        self.engine = None
        self.background = None
        self._init_ui()
        self._init_camera()
        self._init_engine()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setMinimumHeight(400)
        layout.addWidget(self.video_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)

        self.countdown_label = QLabel()
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setFont(QFont("Arial", 48, QFont.Bold))
        self.countdown_label.setStyleSheet("color: red;")
        self.countdown_label.hide()
        layout.addWidget(self.countdown_label)

        capture_btn = QPushButton("CAPTURAR")
        capture_btn.setStyleSheet(
            "background-color: #FF6B35; color: white; font-size: 16px; padding: 15px;"
        )
        capture_btn.clicked.connect(self._start_countdown)
        layout.addWidget(capture_btn)

        self.setLayout(layout)

    def _init_camera(self) -> None:
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    def _init_engine(self) -> None:
        try:
            self.engine = SegmentationEngine()
            bg_path = Path(self.config_manager.get_app_config().get("photos_dir", "assets/photos")) / "cancha.png"
            if bg_path.exists():
                self.background = cv2.imread(str(bg_path))
        except Exception as e:
            print(f"[!] Engine init error: {e}")

    def _update_frame(self) -> None:
        ret, frame = self.camera.read()
        if not ret or self.engine is None:
            return

        frame_resized = cv2.resize(frame, (640, 480))

        mask = self.engine.process(frame_resized)

        if self.background is not None:
            result = apply_mask(frame_resized, self.background, mask, blur_kernel=5)
        else:
            result = frame_resized

        rgb_frame = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image).scaledToWidth(540)
        self.video_label.setPixmap(pixmap)

    def _start_countdown(self) -> None:
        self.countdown = 5
        self.timer.stop()
        self.countdown_label.show()
        self._update_countdown()
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_timer.start(1000)

    def _update_countdown(self) -> None:
        if self.countdown > 0:
            self.countdown_label.setText(str(self.countdown))
            self.countdown -= 1
        else:
            self.countdown_timer.stop()
            self._capture_photo()

    def _capture_photo(self) -> None:
        ret, frame = self.camera.read()
        if ret:
            output_dir = Path(self.config_manager.get_app_config().get("output_dir", "output"))
            output_dir.mkdir(parents=True, exist_ok=True)
            photo_path = output_dir / "captured.jpg"
            cv2.imwrite(str(photo_path), frame)
            self.photo_captured.emit(str(photo_path))
            self.countdown_label.hide()

    def set_overlays(self, overlays: list) -> None:
        self.overlays = overlays
        self.timer.start(30)

    def process_photo(self, photo_path: str, final_screen) -> None:
        self.final_screen = final_screen
        background_path = Path(self.config_manager.get_app_config().get("photos_dir", "assets/photos")) / "cancha.png"

        self.processing_worker = ProcessingWorker(
            photo_path, str(background_path),
            str(Path(self.config_manager.get_app_config().get("output_dir", "output")) / "final.jpg")
        )
        self.processing_worker.finished.connect(self._on_processing_done)
        self.processing_worker.start()

    def _on_processing_done(self, final_path: str) -> None:
        success, qr_base64, error = NetworkClient.upload_photo(final_path)
        if success and self.final_screen:
            self.final_screen.set_final_image(final_path, qr_base64)
        elif error:
            print(f"Error upload: {error}")

    def release_camera(self) -> None:
        if self.camera:
            self.camera.release()
        if self.engine:
            self.engine.release()
