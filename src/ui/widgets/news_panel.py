import tkinter as tk

from ui.theme import (
    BG_PANEL, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_NEWS, ERROR,
    FONT_TITLE, FONT_LABEL, FONT_TIMESTAMP,
)
from utils.formatting import time_ago, freshness_color

ITEMS_VISIBLE = 4
ROTATE_MS     = 6_000   # ms entre rotaciones


class NewsPanel(tk.Frame):
    """Cajon 3 — Noticias cripto via RSS (Cointelegraph + CoinDesk).

    Muestra ITEMS_VISIBLE noticias a la vez. Rota automaticamente cada
    ROTATE_MS ms avanzando un item. Sin interaccion (pantalla no tactil).
    """

    def __init__(self, parent, rss_service, **kwargs):
        kwargs.setdefault('bg', BG_PANEL)
        super().__init__(parent, **kwargs)
        self._rss  = rss_service
        self._bg   = self.cget('bg')
        self._idx  = 0
        self._slots = []
        self._build_ui()
        self._poll()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        bg = self._bg

        # --- Header ---
        header = tk.Frame(self, bg=bg, height=32)
        header.pack(fill='x', padx=10, pady=(8, 4))
        header.pack_propagate(False)

        tk.Label(
            header, text="NOTICIAS CRIPTO",
            font=FONT_TITLE, fg=ACCENT_NEWS, bg=bg,
        ).pack(side='left', pady=4)

        self._fresh_dot = tk.Label(
            header, text="●", font=('Courier', 10),
            fg=TEXT_SECONDARY, bg=bg,
        )
        self._fresh_dot.pack(side='right', padx=(0, 6))

        self._fresh_label = tk.Label(
            header, text="", font=FONT_TIMESTAMP,
            fg=TEXT_SECONDARY, bg=bg,
        )
        self._fresh_label.pack(side='right')

        # --- Separador ---
        tk.Frame(self, bg=BORDER, height=1).pack(fill='x', padx=8)

        # --- Slots de noticias ---
        for i in range(ITEMS_VISIBLE):
            slot = tk.Frame(self, bg=bg)
            slot.pack(fill='x', padx=10, pady=(5, 1))

            # Fila meta: fuente a la izquierda, tiempo a la derecha
            meta = tk.Frame(slot, bg=bg)
            meta.pack(fill='x')

            source_lbl = tk.Label(
                meta, text="",
                font=('Courier', 9, 'bold'), fg=ACCENT_NEWS, bg=bg, anchor='w',
            )
            source_lbl.pack(side='left')

            time_lbl = tk.Label(
                meta, text="",
                font=FONT_TIMESTAMP, fg=TEXT_SECONDARY, bg=bg,
            )
            time_lbl.pack(side='right')

            # Titulo: hasta 2 lineas con wraplength
            title_lbl = tk.Label(
                slot, text="",
                font=FONT_LABEL, fg=TEXT_PRIMARY, bg=bg,
                wraplength=460, justify='left', anchor='w',
            )
            title_lbl.pack(fill='x')

            self._slots.append({
                'source': source_lbl,
                'time':   time_lbl,
                'title':  title_lbl,
            })

            # Separador entre items (no despues del ultimo)
            if i < ITEMS_VISIBLE - 1:
                tk.Frame(self, bg=BORDER, height=1).pack(fill='x', padx=8, pady=(4, 0))

    # ------------------------------------------------------------------
    # Polling + rotacion
    # ------------------------------------------------------------------

    def _poll(self):
        data  = self._rss.get_data()
        items = data.get('items', [])
        ts    = data.get('timestamp')

        # Indicador de frescura
        self._fresh_dot.config(fg=freshness_color(ts, 1800))
        self._fresh_label.config(text=f"hace {time_ago(ts)}" if ts else "")

        if not items:
            # Sin datos todavia: mostrar mensaje en primer slot, limpiar el resto
            msg = "Cargando..." if data.get('error') is None else "Sin conexion"
            for i, slot in enumerate(self._slots):
                slot['source'].config(text="")
                slot['time'].config(text="")
                if i == 0:
                    slot['title'].config(text=msg, fg=TEXT_SECONDARY)
                else:
                    slot['title'].config(text="")
            # Reintentar cada 5s hasta obtener datos
            self.after(5_000, self._poll)
            return

        # Rellenar slots con items a partir de self._idx
        n = len(items)
        for i, slot in enumerate(self._slots):
            item = items[(self._idx + i) % n]
            slot['source'].config(text=item['source'])
            slot['time'].config(text=f"hace {time_ago(item['published'])}")
            slot['title'].config(text=item['title'], fg=TEXT_PRIMARY)

        # Avanzar al siguiente item para la proxima rotacion
        self._idx = (self._idx + 1) % n
        self.after(ROTATE_MS, self._poll)
