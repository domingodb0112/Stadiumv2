import time
import threading
import cv2
import numpy as np
from PIL import Image, ImageTk
import customtkinter as ctk

from screens.base_screen import BaseScreen
from engine.video_overlay import VideoOverlayEngine
from config import BG, TEXT_WHITE, ACCENT, WIN_W, WIN_H, COUNTDOWN_SEC, REF_W, REF_H


class CameraPreviewScreen(BaseScreen):
    """
    Cámara en vivo con overlays de jugadores.
    Capas: cámara → overlays → botones de UI
    """

    def __init__(self, app, players, **kwargs):
        super().__init__(app, **kwargs)
        self._players        = players
        self._cap            = None
        self._running        = False
        self._countdown_left = 0
        self._counting       = False
        self._photo_frame    = None   # Mat capturado para guardar

        self._build_ui()
        self._start_camera()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Canvas para el preview
        self._canvas = ctk.CTkLabel(self, text="", width=WIN_W, height=WIN_H)
        self._canvas.place(x=0, y=0)

        # Botón regresar
        self._btn_back = ctk.CTkButton(
            self,
            text="←",
            width=48, height=48,
            fg_color="#333333",
            hover_color="#555555",
            corner_radius=24,
            font=ctk.CTkFont(size=20),
            command=self._on_back,
        )
        self._btn_back.place(x=16, y=16)

        # Cuenta regresiva
        self._lbl_countdown = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="Arial Black", size=120, weight="bold"),
            text_color=TEXT_WHITE,
        )
        self._lbl_countdown.place(relx=0.5, rely=0.5, anchor="center")

        # Botón captura (solo icono, pequeño)
        self._btn_capture = ctk.CTkButton(
            self,
            text="📷",
            width=56, height=56,
            fg_color=TEXT_WHITE,
            hover_color="#DDDDDD",
            text_color="#000000",
            corner_radius=28,
            font=ctk.CTkFont(size=24),
            command=self._start_countdown,
        )
        self._btn_capture.place(relx=0.5, rely=1.0, anchor="s", y=-32)

    # ── Cámara ────────────────────────────────────────────────────────────────

    def _start_camera(self):
        self._cap = cv2.VideoCapture(0)
        if self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1080)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1920)

        # Arrancar overlays de video
        VideoOverlayEngine.start_experience(self._players, WIN_W, WIN_H)

        self._running = True
        threading.Thread(target=self._capture_loop, daemon=True).start()

    def _capture_loop(self):
        while self._running:
            if not self._cap or not self._cap.isOpened():
                time.sleep(0.033)
                continue

            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.033)
                continue

            # Redimensionar a pantalla
            frame = cv2.resize(frame, (WIN_W, WIN_H))

            # Aplicar overlays de jugadores
            frame = VideoOverlayEngine.apply_all(frame)

            # Guardar frame si hay captura pendiente
            if self._photo_frame is None and hasattr(self, '_capture_pending') and self._capture_pending:
                self._capture_pending = False
                # Capturar a resolución completa 1080×1920
                ret2, frame_hd = self._cap.read()
                if ret2:
                    frame_hd = cv2.resize(frame_hd, (WIN_W, WIN_H))
                    frame_hd = VideoOverlayEngine.apply_all(frame_hd)
                    frame_hd = cv2.resize(frame_hd, (REF_W, REF_H))
                    self._photo_frame = frame_hd
                else:
                    big = cv2.resize(frame, (REF_W, REF_H))
                    self._photo_frame = big

            # Convertir BGR → RGB → PhotoImage
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil   = Image.fromarray(rgb)
            photo = ImageTk.PhotoImage(pil)

            # Actualizar UI en hilo principal
            self.after(0, self._update_canvas, photo)
            time.sleep(0.033)

    def _update_canvas(self, photo):
        try:
            self._canvas.configure(image=photo)
            self._canvas.image = photo   # evitar GC
        except Exception:
            pass

    # ── Countdown ─────────────────────────────────────────────────────────────

    def _start_countdown(self):
        if self._counting:
            return
        self._counting       = True
        self._countdown_left = COUNTDOWN_SEC
        self._btn_capture.place_forget()
        self._tick()

    def _tick(self):
        if self._countdown_left > 0:
            self._lbl_countdown.configure(text=str(self._countdown_left))
            self._countdown_left -= 1
            self.after(1000, self._tick)
        else:
            self._lbl_countdown.configure(text="")
            self._counting        = False
            self._capture_pending = True
            self._btn_capture.place(relx=0.5, rely=1.0, anchor="s", y=-40)
            # Esperar a que el hilo guarde el frame y luego navegar
            self.after(100, self._wait_for_photo)

    def _wait_for_photo(self):
        if self._photo_frame is None:
            self.after(100, self._wait_for_photo)
            return
        self._do_save()

    def _do_save(self):
        import time as _time
        from config import OUTPUT_DIR
        path = str(OUTPUT_DIR / f"photo_{int(_time.time())}.jpg")
        cv2.imwrite(path, self._photo_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        self.app.show_photo_view(path, self._players)

    # ── Regresar ──────────────────────────────────────────────────────────────

    def _on_back(self):
        self.app.show_player_selection()

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def on_destroy(self):
        self._running = False
        time.sleep(0.1)
        if self._cap:
            self._cap.release()
        VideoOverlayEngine.stop_all()
