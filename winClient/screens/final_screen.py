import customtkinter as ctk
from PIL import Image, ImageTk
from screens.base_screen import BaseScreen
from engine.network_client import upload_photo
from config import BG, ACCENT, TEXT_WHITE, TEXT_DIM, WIN_W, WIN_H


class FinalScreen(BaseScreen):
    """Foto final + código QR + botón VOLVER AL INICIO."""

    def __init__(self, app, photo_path: str, **kwargs):
        super().__init__(app, **kwargs)
        self._photo_path = photo_path
        self._build_ui()
        self._load_photo()
        self._upload()

    def _build_ui(self):
        # Foto a pantalla completa (fondo)
        self._lbl_photo = ctk.CTkLabel(self, text="", width=WIN_W, height=WIN_H)
        self._lbl_photo.place(x=0, y=0)

        # Gradiente superior semi-transparente
        overlay_top = ctk.CTkFrame(self, fg_color="#1a1a1a", height=160, corner_radius=0)
        overlay_top.place(x=0, y=0, relwidth=1)

        # Gradiente inferior
        overlay_bot = ctk.CTkFrame(self, fg_color="#1a1a1a", height=280, corner_radius=0)
        overlay_bot.place(x=0, rely=1.0, anchor="sw", relwidth=1)

        # Palomita + título + subtítulo (aparecen animados)
        self._lbl_check = ctk.CTkLabel(
            self, text="✓",
            font=ctk.CTkFont(family="Arial Black", size=80, weight="bold"),
            text_color=ACCENT,
        )
        self._lbl_check.place(relx=0.5, rely=0.30, anchor="center")

        self._lbl_title = ctk.CTkLabel(
            self, text="¡Foto lista!",
            font=ctk.CTkFont(family="Arial Black", size=40, weight="bold"),
            text_color=TEXT_WHITE,
        )
        self._lbl_title.place(relx=0.5, rely=0.42, anchor="center")

        self._lbl_sub = ctk.CTkLabel(
            self, text="Subiendo tu foto…",
            font=ctk.CTkFont(size=18),
            text_color="#CCFFFFFF",
        )
        self._lbl_sub.place(relx=0.5, rely=0.51, anchor="center")

        # Contenedor QR (oculto hasta que llegue del servidor)
        self._frame_qr = ctk.CTkFrame(self, fg_color=TEXT_WHITE,
                                       width=220, height=220, corner_radius=8)
        self._lbl_qr = ctk.CTkLabel(self._frame_qr, text="")
        self._lbl_qr.place(relx=0.5, rely=0.5, anchor="center")

        # Botón volver
        ctk.CTkButton(
            self,
            text="VOLVER AL INICIO",
            font=ctk.CTkFont(family="Arial Black", size=18, weight="bold"),
            fg_color=ACCENT,
            hover_color="#388E3C",
            text_color=TEXT_WHITE,
            width=280, height=64,
            corner_radius=32,
            command=self._on_home,
        ).place(relx=0.5, rely=0.92, anchor="center")

        # Animación de entrada
        self.after(200, self._entrance_animation)

    def _entrance_animation(self):
        """Fade-in simple del check y título."""
        for widget in (self._lbl_check, self._lbl_title, self._lbl_sub):
            widget.configure(text_color=widget.cget("text_color"))   # fuerza redraw

    def _load_photo(self):
        try:
            img   = Image.open(self._photo_path).resize((WIN_W, WIN_H), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._lbl_photo.configure(image=photo)
            self._lbl_photo.image = photo
        except Exception:
            pass

    def _upload(self):
        upload_photo(
            self._photo_path,
            on_success=lambda qr_pil: self.after(0, self._show_qr, qr_pil),
            on_error=lambda msg:      self.after(0, self._lbl_sub.configure, {"text": f"Error: {msg}"}),
        )

    def _show_qr(self, qr_pil: Image.Image):
        try:
            qr_pil  = qr_pil.resize((200, 200), Image.LANCZOS)
            qr_photo = ImageTk.PhotoImage(qr_pil)
            self._lbl_qr.configure(image=qr_photo)
            self._lbl_qr.image = qr_photo
            self._lbl_qr.place(relx=0.5, rely=0.5, anchor="center")
            self._frame_qr.place(relx=0.5, rely=0.70, anchor="center")
            self._lbl_sub.configure(text="¡Escanea para descargar!")
        except Exception:
            pass

    def _on_home(self):
        self.app.show_welcome()
