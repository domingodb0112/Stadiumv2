import threading
import cv2
import numpy as np
import customtkinter as ctk

from screens.base_screen import BaseScreen
from config import BG, ACCENT, TEXT_WHITE, TEXT_DIM, SIMULATION_MS, PHOTOS_DIR, REF_W, REF_H, OUTPUT_DIR


class SimulationScreen(BaseScreen):
    """
    Pantalla de carga '¡SALIENDO AL CAMPO!'.
    Mientras avanza la barra, procesa la foto (agrega el fondo de estadio).
    """

    def __init__(self, app, photo_path: str, players, **kwargs):
        super().__init__(app, **kwargs)
        self._photo_path    = photo_path
        self._players       = players
        self._final_path    = photo_path   # se actualiza al terminar el procesado
        self._done          = False
        self._build_ui()
        self._start_processing()
        self._animate(0)

    def _build_ui(self):
        center = ctk.CTkFrame(self, fg_color=BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center,
            text="¡SALIENDO AL CAMPO!",
            font=ctk.CTkFont(family="Arial Black", size=26, weight="bold"),
            text_color=ACCENT,
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            center,
            text="Tus ídolos están saltando al césped…\nPreparando el encuentro histórico.",
            font=ctk.CTkFont(size=16),
            text_color=TEXT_WHITE,
            justify="center",
        ).pack(pady=(0, 40))

        self._progress = ctk.CTkProgressBar(center, width=380, height=10,
                                             progress_color=ACCENT, fg_color="#333333")
        self._progress.set(0)
        self._progress.pack(pady=(0, 12))

        ctk.CTkLabel(
            center,
            text="6 segundos para la gloria…",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM,
        ).pack()

    def _animate(self, elapsed_ms: int):
        progress = min(elapsed_ms / SIMULATION_MS, 1.0)
        self._progress.set(progress)
        if elapsed_ms < SIMULATION_MS:
            self.after(50, self._animate, elapsed_ms + 50)
        else:
            # Esperar a que el procesado termine antes de navegar
            self._check_ready()

    def _check_ready(self):
        if self._done:
            self.app.show_final(self._final_path)
        else:
            self.after(100, self._check_ready)

    # ── Procesado de foto (fondo estadio) ─────────────────────────────────────

    def _start_processing(self):
        threading.Thread(target=self._process, daemon=True).start()

    def _process(self):
        try:
            cancha_path = str(PHOTOS_DIR / "cancha.png")
            user_mat    = cv2.imread(self._photo_path)
            cancha_mat  = cv2.imread(cancha_path)

            if user_mat is None:
                self._done = True
                return

            # Redimensionar ambas a 1080×1920
            user_mat = cv2.resize(user_mat, (REF_W, REF_H))

            if cancha_mat is not None:
                cancha_mat = cv2.resize(cancha_mat, (REF_W, REF_H))
                # Mezcla simple: 30% estadio + 70% usuario (sin segmentación IA)
                result = cv2.addWeighted(cancha_mat, 0.3, user_mat, 0.7, 0)
            else:
                result = user_mat

            import time as _t
            out_path = str(OUTPUT_DIR / f"final_{int(_t.time())}.jpg")
            cv2.imwrite(out_path, result, [cv2.IMWRITE_JPEG_QUALITY, 95])
            self._final_path = out_path
        except Exception as e:
            print(f"[SimulationScreen] Error en procesado: {e}")
        finally:
            self._done = True
