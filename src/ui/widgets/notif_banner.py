import tkinter as tk

_LEVELS = [
    (100, '#ff4444', 250, '🚨'),
    (50,  '#ff3333', 250, '🚨'),
    (25,  '#ff5500', 400, '🚨'),
    (20,  '#ff6600', 400, '🚨'),
    (15,  '#ff8800', 700, '⚠'),
    (10,  '#ffaa00', 700, '⚠'),
    (5,   '#ffee00', 1000, '⚡'),
    (3,   '#44aaff', 1000, '⚡'),
]

_BG_INNER = '#0f0f22'
_BG_OUTER = '#1a1a30'
_TEXT     = '#eaeaf5'


def _level_for(pct):
    """Devuelve (color_acento, blink_ms, icon) según magnitud del movimiento."""
    for threshold, color, blink_ms, icon in _LEVELS:
        if abs(pct) >= threshold:
            return color, blink_ms, icon
    return '#44aaff', 1000, '⚡'


class NotifBanner(tk.Frame):
    """Banner flotante de notificación de precio con borde coloreado y parpadeo."""

    def __init__(self, parent, sym, spike_pct, change_24h, price_str,
                 on_dismiss, duration_s=10):
        color, blink_ms, icon = _level_for(spike_pct)
        self._color      = color
        self._blink_ms   = blink_ms
        self._on_dismiss = on_dismiss
        self._blink_on   = True
        self._dismissed  = False

        # Marco exterior coloreado actúa como borde visible (2 px)
        super().__init__(parent, bg=color, padx=2, pady=2)

        inner = tk.Frame(self, bg=_BG_INNER)
        inner.pack(fill='both', expand=True)

        # Franja de acento izquierda (4 px)
        tk.Frame(inner, bg=color, width=4).pack(side='left', fill='y')

        # Icono parpadeante
        self._icon_lbl = tk.Label(inner, text=icon, font=('Helvetica', 16, 'bold'),
                                  fg=color, bg=_BG_INNER, width=2)
        self._icon_lbl.pack(side='left', padx=(6, 2))

        # Símbolo en blanco brillante
        tk.Label(inner, text=sym, font=('Helvetica', 13, 'bold'),
                 fg=_TEXT, bg=_BG_INNER).pack(side='left', padx=(4, 6))

        # Porcentaje en el color de alerta
        sign  = '▲' if spike_pct >= 0 else '▼'
        pct_s = f'{sign}{abs(spike_pct):.1f}%  5min'
        tk.Label(inner, text=pct_s, font=('Helvetica', 11, 'bold'),
                 fg=color, bg=_BG_INNER).pack(side='left')

        # Precio en blanco
        tk.Label(inner, text=f'  {price_str}', font=('Courier', 11, 'bold'),
                 fg=_TEXT, bg=_BG_INNER).pack(side='left')

        # Cambio 24h si disponible
        if change_24h is not None:
            ch_s = f'  24h: {sign}{abs(change_24h):.1f}%'
            tk.Label(inner, text=ch_s, font=('Helvetica', 10),
                     fg=color, bg=_BG_INNER).pack(side='left', padx=(0, 8))

        self.after(duration_s * 1000, self.dismiss)
        self._blink()

    def _blink(self):
        if self._dismissed:
            return
        self._blink_on = not self._blink_on
        fg = self._color if self._blink_on else _BG_INNER
        try:
            self._icon_lbl.config(fg=fg)
            self.after(self._blink_ms, self._blink)
        except tk.TclError:
            pass

    def dismiss(self):
        if self._dismissed:
            return
        self._dismissed = True
        try:
            self.place_forget()
            self.destroy()
        except tk.TclError:
            pass
        self._on_dismiss(self)
