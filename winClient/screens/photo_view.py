import customtkinter as ctk
from PIL import Image, ImageTk
from screens.base_screen import BaseScreen
from config import BG, TEXT_WHITE, ACCENT, BTN_DARK, WIN_W, WIN_H, AUTO_SEND_MS


class PhotoViewScreen(BaseScreen):
    """Muestra la foto capturada con opción de reintentar o enviar. Auto-envío en 5s."""

    def __init__(self, app, photo_path: str, players, **kwargs):
        super().__init__(app, **kwargs)
        self._photo_path  = photo_path
        self._players     = players
        self._timer_id    = None
        self._seconds_left = AUTO_SEND_MS // 1000
        self._build_ui()
        self._load_photo()
        self._start_timer()

    def _build_ui(self):
        # Imagen a pantalla completa
        self._lbl_photo = ctk.CTkLabel(self, text="", width=WIN_W, height=WIN_H)
        self._lbl_photo.place(x=0, y=0)

        # Botones en la parte inferior
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.place(relx=0.5, rely=1.0, anchor="s", y=-48)

        ctk.CTkButton(
            btn_frame,
            text="REINTENTAR",
            font=ctk.CTkFont(family="Arial Black", size=16),
            fg_color=BTN_DARK,
            hover_color="#666666",
            text_color=TEXT_WHITE,
            width=180, height=60,
            corner_radius=8,
            command=self._on_retake,
        ).grid(row=0, column=0, padx=8)

        self._btn_send = ctk.CTkButton(
            btn_frame,
            text=f"ENVIAR ({self._seconds_left}s)",
            font=ctk.CTkFont(family="Arial Black", size=16),
            fg_color="#1976D2",
            hover_color="#1565C0",
            text_color=TEXT_WHITE,
            width=180, height=60,
            corner_radius=8,
            command=self._on_send,
        )
        self._btn_send.grid(row=0, column=1, padx=8)

    def _load_photo(self):
        try:
            img   = Image.open(self._photo_path).resize((WIN_W, WIN_H), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._lbl_photo.configure(image=photo)
            self._lbl_photo.image = photo
        except Exception:
            pass

    def _start_timer(self):
        self._tick()

    def _tick(self):
        if self._seconds_left > 0:
            self._btn_send.configure(text=f"ENVIAR ({self._seconds_left}s)")
            self._seconds_left -= 1
            self._timer_id = self.after(1000, self._tick)
        else:
            self._on_send()

    def _on_retake(self):
        if self._timer_id:
            self.after_cancel(self._timer_id)
        self.app.show_camera(self._players)

    def _on_send(self):
        if self._timer_id:
            self.after_cancel(self._timer_id)
        self.app.show_simulation(self._photo_path, self._players)

    def on_destroy(self):
        if self._timer_id:
            self.after_cancel(self._timer_id)
