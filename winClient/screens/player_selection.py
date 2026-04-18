import customtkinter as ctk
from PIL import Image, ImageDraw
from screens.base_screen import BaseScreen
from models.player_roster import ALL as PLAYERS, reset_selection
from config import BG, TEXT_WHITE, TEXT_DIM, ACCENT, BTN_DARK


def _circle_image(path, size=110):
    """Carga una imagen y la recorta en círculo."""
    try:
        img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    except Exception:
        img = Image.new("RGBA", (size, size), "#333333")

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, mask=mask)
    return result


class PlayerSelectionScreen(BaseScreen):
    """Pantalla de selección de jugadores en grid 2×2."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        reset_selection()
        self._ctk_images = []   # evitar que el GC destruya las imágenes
        self._build_ui()

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="ELIGE TUS JUGADORES",
            font=ctk.CTkFont(family="Arial Black", size=22, weight="bold"),
            text_color=TEXT_WHITE,
        ).pack(pady=(48, 4))

        ctk.CTkLabel(
            self,
            text="Selecciona los jugadores que aparecerán en tu foto",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_DIM,
        ).pack(pady=(0, 6))

        self._lbl_count = ctk.CTkLabel(
            self,
            text="0 seleccionados",
            font=ctk.CTkFont(size=14),
            text_color=ACCENT,
        )
        self._lbl_count.pack(pady=(0, 20))

        # ── Grid 2×2 ──────────────────────────────────────────────────────
        grid = ctk.CTkFrame(self, fg_color=BG)
        grid.pack(expand=True)

        for idx, player in enumerate(PLAYERS):
            row, col = divmod(idx, 2)
            self._make_card(grid, player, row, col)

        # ── Botón continuar ───────────────────────────────────────────────
        self._btn_continue = ctk.CTkButton(
            self,
            text="CONTINUAR",
            font=ctk.CTkFont(family="Arial Black", size=16, weight="bold"),
            fg_color=ACCENT,
            text_color="#000000",
            hover_color="#388E3C",
            state="disabled",
            width=240,
            height=56,
            corner_radius=28,
            command=self._on_continue,
        )
        self._btn_continue.pack(pady=(20, 40))

    def _make_card(self, parent, player, row, col):
        card = ctk.CTkFrame(parent, fg_color=BG, cursor="hand2", border_width=0,
                           border_color=ACCENT, corner_radius=60)
        card.grid(row=row, column=col, padx=20, pady=16)

        # Imagen circular
        pil_img = _circle_image(player.image_path, size=110)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(110, 110))
        self._ctk_images.append(ctk_img)

        img_lbl = ctk.CTkLabel(card, image=ctk_img, text="")
        img_lbl.pack(padx=8, pady=8)

        name_lbl = ctk.CTkLabel(
            card,
            text=player.name,
            font=ctk.CTkFont(size=13),
            text_color=TEXT_WHITE,
        )
        name_lbl.pack(pady=(4, 12))

        def toggle(event=None, p=player, c=card):
            p.selected = not p.selected
            c.configure(border_width=4 if p.selected else 0)
            count = sum(1 for pl in PLAYERS if pl.selected)
            self._lbl_count.configure(
                text=f"{count} {'seleccionado' if count == 1 else 'seleccionados'}"
            )
            self._btn_continue.configure(
                state="normal" if count > 0 else "disabled",
                fg_color=ACCENT if count > 0 else BTN_DARK,
            )

        for widget in (card, img_lbl, name_lbl):
            widget.bind("<Button-1>", toggle)

    def _on_continue(self):
        selected = [p for p in PLAYERS if p.selected]
        self.app.show_camera(selected)
