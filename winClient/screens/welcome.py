import customtkinter as ctk
from screens.base_screen import BaseScreen
from config import TEXT_WHITE, TEXT_DIM, ACCENT, BG


class WelcomeScreen(BaseScreen):
    """Pantalla de bienvenida — 'STADIUM AR' + botón COMENZAR."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        center = ctk.CTkFrame(self, fg_color=BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center,
            text="STADIUM AR",
            font=ctk.CTkFont(family="Arial Black", size=38, weight="bold"),
            text_color=TEXT_WHITE,
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            center,
            text="Vive la experiencia con tus ídolos",
            font=ctk.CTkFont(size=15),
            text_color=TEXT_DIM,
        ).pack(pady=(0, 48))

        ctk.CTkButton(
            center,
            text="TOCA PARA COMENZAR",
            font=ctk.CTkFont(family="Arial Black", size=16, weight="bold"),
            fg_color=TEXT_WHITE,
            text_color="#000000",
            hover_color="#DDDDDD",
            width=260,
            height=64,
            corner_radius=32,
            command=self.app.show_player_selection,
        ).pack()
