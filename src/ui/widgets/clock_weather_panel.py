import re
import tkinter as tk
import datetime

from ui.theme import (
    BG_PANEL, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_CLOCK, ERROR,
    FONT_TITLE, FONT_TIMESTAMP,
    FONT_CLOCK, FONT_CLOCK_SEC, FONT_CLOCK_DATE,
)
from utils.formatting import time_ago, freshness_color

DIAS_ES = [
    'Lunes', 'Martes', 'Miercoles', 'Jueves',
    'Viernes', 'Sabado', 'Domingo',
]
MESES_ES = [
    '', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

_ART_FONT   = ('Courier', 6)
_ART_HEIGHT = 28

# ---------------------------------------------------------------------------
# Parser ANSI SGR -> colores tkinter
# ---------------------------------------------------------------------------

_SGR_RE  = re.compile(r'\x1b\[([0-9;]*)m')
_CTRL_RE = re.compile(r'\x1b\[(?![0-9;]*m)[0-9;]*[A-Za-z]')  # no-SGR (eliminar)

# Paleta xterm-256 -> hex
_XTERM_STD = [
    '#1c1c1c', '#af0000', '#00af00', '#afaf00',
    '#0000af', '#af00af', '#00afaf', '#afafaf',
    '#626262', '#ff0000', '#00ff00', '#ffff00',
    '#0000ff', '#ff00ff', '#00ffff', '#ffffff',
]

def _xterm_hex(n):
    if n < 16:
        return _XTERM_STD[n]
    if n < 232:
        n -= 16
        r, g, b = n // 36, (n // 6) % 6, n % 6
        def v(x): return 0 if x == 0 else 55 + x * 40
        return f'#{v(r):02x}{v(g):02x}{v(b):02x}'
    val = 8 + (n - 232) * 10
    return f'#{val:02x}{val:02x}{val:02x}'


def _parse_ansi(text):
    """Yields (segment, fg_hex_or_None, bold) aplicando estados SGR."""
    text = _CTRL_RE.sub('', text)
    pos, fg, bold = 0, None, False

    for m in _SGR_RE.finditer(text):
        if m.start() > pos:
            yield (text[pos:m.start()], fg, bold)

        codes = [int(x) if x else 0 for x in m.group(1).split(';')] if m.group(1) else [0]
        i = 0
        while i < len(codes):
            c = codes[i]
            if c == 0:
                fg, bold = None, False
            elif c == 1:
                bold = True
            elif c in (2, 22):
                bold = False
            elif c == 38 and i + 1 < len(codes):
                if codes[i + 1] == 5 and i + 2 < len(codes):       # 256-color
                    fg = _xterm_hex(codes[i + 2]); i += 2
                elif codes[i + 1] == 2 and i + 4 < len(codes):      # 24-bit RGB
                    fg = f'#{codes[i+2]:02x}{codes[i+3]:02x}{codes[i+4]:02x}'; i += 4
            elif c == 39:
                fg = None
            i += 1
        pos = m.end()

    if pos < len(text):
        yield (text[pos:], fg, bold)


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------

class ClockWeatherPanel(tk.Frame):
    """Cajon 4 — Reloj digital + ASCII art con colores de wttr.in."""

    def __init__(self, parent, weather_service, **kwargs):
        kwargs.setdefault('bg', BG_PANEL)
        super().__init__(parent, **kwargs)
        self._weather_service = weather_service
        self._bg = self.cget('bg')
        self._known_tags = set()
        self._build_ui()
        self._tick()
        self._poll_weather()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        bg = self._bg

        # Header
        header = tk.Frame(self, bg=bg, height=32)
        header.pack(fill='x', padx=10, pady=(8, 4))
        header.pack_propagate(False)

        self._fresh_dot = tk.Label(
            header, text='\u25cf', font=('Courier', 10),
            fg=TEXT_SECONDARY, bg=bg,
        )
        self._fresh_dot.pack(side='right', padx=(0, 6))

        self._fresh_label = tk.Label(
            header, text='', font=FONT_TIMESTAMP,
            fg=TEXT_SECONDARY, bg=bg,
        )
        self._fresh_label.pack(side='right')

        tk.Label(
            header, text='HORA & TIEMPO',
            font=FONT_TITLE, fg=ACCENT_CLOCK, bg=bg, anchor='center',
        ).pack(side='left', fill='x', expand=True)

        # Separador
        tk.Frame(self, bg=BORDER, height=1).pack(fill='x', padx=8)

        # Reloj
        clock_frame = tk.Frame(self, bg=bg)
        clock_frame.pack(fill='both', expand=True, padx=12, pady=(6, 4))

        tk.Frame(clock_frame, bg=bg).pack(expand=True)

        time_row = tk.Frame(clock_frame, bg=bg)
        time_row.pack()

        self._time_label = tk.Label(
            time_row, text='--:--',
            font=FONT_CLOCK, fg=TEXT_PRIMARY, bg=bg,
        )
        self._time_label.pack(side='left')

        self._sec_label = tk.Label(
            time_row, text=':--',
            font=FONT_CLOCK_SEC, fg=TEXT_SECONDARY, bg=bg,
        )
        self._sec_label.pack(side='left', anchor='s', pady=(0, 10))

        self._date_label = tk.Label(
            clock_frame, text='',
            font=FONT_CLOCK_DATE, fg=TEXT_SECONDARY, bg=bg,
        )
        self._date_label.pack(pady=(2, 0))

        tk.Frame(clock_frame, bg=bg).pack(expand=True)

        # Separador
        tk.Frame(self, bg=BORDER, height=1).pack(fill='x', padx=8)

        # Bloque ASCII art wttr.in
        weather_outer = tk.Frame(self, bg=bg)
        weather_outer.pack(fill='both', expand=True, padx=10, pady=(6, 8))

        self._art_text = tk.Text(
            weather_outer,
            bg=bg,
            fg=ACCENT_CLOCK,
            font=_ART_FONT,
            relief='flat',
            bd=0,
            highlightthickness=0,
            cursor='arrow',
            state='disabled',
            height=_ART_HEIGHT,
            wrap='none',
            selectbackground=bg,
        )
        self._art_text.pack(fill='both', expand=True)

        self._art_text.tag_config('loading', foreground=TEXT_SECONDARY, justify='center')
        self._art_text.tag_config('error',   foreground=ERROR,          justify='center')

    # ------------------------------------------------------------------
    # Reloj
    # ------------------------------------------------------------------

    def _tick(self):
        now = datetime.datetime.now()
        self._time_label.config(text=now.strftime('%H:%M'))
        self._sec_label.config(text=f":{now.strftime('%S')}")

        dia = DIAS_ES[now.weekday()]
        mes = MESES_ES[now.month]
        self._date_label.config(
            text=f'{dia}, {now.day} de {mes} de {now.year}'
        )
        self.after(1000, self._tick)

    # ------------------------------------------------------------------
    # Tiempo
    # ------------------------------------------------------------------

    def _get_tag(self, fg, bold):
        """Devuelve (creando si hace falta) un tag con el color/estilo dado."""
        safe = (fg or '').replace('#', '')
        name = f'a_{safe}{"b" if bold else ""}'
        if name not in self._known_tags:
            font = (_ART_FONT[0], _ART_FONT[1], 'bold') if bold else _ART_FONT
            self._art_text.tag_config(name, foreground=fg or ACCENT_CLOCK, font=font)
            self._known_tags.add(name)
        return name

    def _poll_weather(self):
        data = self._weather_service.get_data()
        self._update_weather(data)
        if data['art_text'] is None:
            self.after(5_000, self._poll_weather)
        else:
            self.after(60_000, self._poll_weather)

    def _update_weather(self, data):
        t = self._art_text
        t.config(state='normal')
        t.delete('1.0', 'end')

        art = data.get('art_text')
        if art:
            for segment, fg, bold in _parse_ansi(art):
                t.insert('end', segment, self._get_tag(fg, bold))
            tag = 'body'
        elif data.get('error'):
            t.insert('end', 'Sin datos de tiempo', 'error')
            tag = 'error'
        else:
            t.insert('end', 'Cargando...', 'loading')
            tag = 'loading'

        t.config(state='disabled')

        ts = data.get('timestamp')
        if ts:
            color = freshness_color(ts, 1800)
            self._fresh_dot.config(fg=color)
            self._fresh_label.config(text=f'Actualizado hace {time_ago(ts)}')
        else:
            self._fresh_dot.config(fg=ERROR if tag == 'error' else TEXT_SECONDARY)
            self._fresh_label.config(text='')
