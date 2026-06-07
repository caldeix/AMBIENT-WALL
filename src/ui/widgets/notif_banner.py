import tkinter as tk

_LEVELS = [
    (100, '#ff0000', 250, '🚨'),
    (50,  '#ee0000', 250, '🚨'),
    (25,  '#cc0000', 400, '🚨'),
    (20,  '#aa0000', 400, '🚨'),
    (15,  '#cc3300', 700, '⚠'),
    (10,  '#cc6600', 700, '⚠'),
    (5,   '#aaaa00', 1000, '⚡'),
    (3,   '#3333aa', 1000, '⚡'),
]

_BG = '#0a0a14'


def _level_for(pct):
    """Devuelve (color, blink_ms, icon) según magnitud del movimiento."""
    for threshold, color, blink_ms, icon in _LEVELS:
        if abs(pct) >= threshold:
            return color, blink_ms, icon
    return '#3333aa', 1000, '⚡'


class NotifBanner(tk.Frame):
    """Banner flotante de notificación de precio con icono parpadeante."""

    def __init__(self, parent, sym, spike_pct, change_24h, price_str,
                 on_dismiss, duration_s=10):
        color, blink_ms, icon = _level_for(spike_pct)
        self._color      = color
        self._blink_ms   = blink_ms
        self._on_dismiss = on_dismiss
        self._blink_on   = True
        self._dismissed  = False

        super().__init__(parent, bg=_BG,
                         highlightbackground=color, highlightthickness=1)

        self._icon_lbl = tk.Label(self, text=icon, font=('Helvetica', 15),
                                  fg=color, bg=_BG, width=2)
        self._icon_lbl.pack(side='left', padx=(8, 2))

        sign   = '▲' if spike_pct >= 0 else '▼'
        pct_s  = f'{sign}{abs(spike_pct):.1f}%'
        ch24_s = f'  24h:{sign}{abs(change_24h):.1f}%' if change_24h is not None else ''
        text   = f'{sym}  {pct_s} (5min)  {price_str}{ch24_s}'

        tk.Label(self, text=text, font=('Helvetica', 11, 'bold'),
                 fg=color, bg=_BG, anchor='w').pack(side='left', padx=(2, 8))

        self.after(duration_s * 1000, self.dismiss)
        self._blink()

    def _blink(self):
        if self._dismissed:
            return
        self._blink_on = not self._blink_on
        fg = self._color if self._blink_on else _BG
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
