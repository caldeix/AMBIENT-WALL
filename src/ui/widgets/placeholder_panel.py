import tkinter as tk
from ui.theme import (
    BG_PANEL, BORDER, TEXT_SECONDARY, ACCENT_NODE, ACCENT_NEWS,
    FONT_TITLE, FONT_LABEL, FONT_TIMESTAMP,
)


class PlaceholderPanel(tk.Frame):
    """Panel de placeholder estatico para cajones sin funcionalidad activa."""

    def __init__(self, parent, title="PROXIMO", accent=ACCENT_NODE,
                 lines=None, **kwargs):
        kwargs.setdefault('bg', BG_PANEL)
        super().__init__(parent, **kwargs)
        self._accent = accent
        self._bg = self.cget('bg')
        self._build(title, lines or [])

    def _build(self, title, lines):
        bg = self._bg

        # --- Header ---
        header = tk.Frame(self, bg=bg, height=32)
        header.pack(fill='x', padx=10, pady=(8, 4))
        header.pack_propagate(False)

        tk.Label(
            header, text=f"[ {title} ]",
            font=FONT_TITLE, fg=self._accent, bg=bg,
        ).pack(side='left', pady=4)

        # --- Separador ---
        tk.Frame(self, bg=BORDER, height=1).pack(fill='x', padx=8)

        # --- Contenido centrado ---
        content = tk.Frame(self, bg=bg)
        content.pack(fill='both', expand=True, padx=16, pady=10)

        tk.Label(
            content,
            text="Proximamente...",
            font=('Helvetica', 15, 'bold'),
            fg=self._accent, bg=bg,
        ).pack(expand=True)

        tk.Label(
            content,
            text="Reservado para futuras metricas",
            font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg,
        ).pack()

        if lines:
            for line in lines:
                tk.Label(
                    content, text=f"  {line}",
                    font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg,
                ).pack(anchor='w')
