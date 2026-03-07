import tkinter as tk
import datetime

from ui.theme import (
    BG_PANEL, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_CLOCK, ERROR,
    FONT_TITLE, FONT_TIMESTAMP,
    FONT_CLOCK, FONT_CLOCK_SEC, FONT_CLOCK_DATE,
    FONT_WEATHER_TEMP, FONT_WEATHER,
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

# Icono Unicode por codigo wttr.in
def _weather_icon(code):
    if code is None:
        return "  "
    if code == 113:
        return "\u2600"   # ☀ Sol
    if code == 116:
        return "\u26c5"   # ⛅ Sol con nubes
    if code in (119, 122):
        return "\u2601"   # ☁ Nublado
    if code in (143, 248, 260):
        return "\U0001f32b"  # 🌫 Niebla
    if code in (200, 386, 389, 392, 395):
        return "\u26c8"   # ⛈ Tormenta
    if code in (227, 230, 320, 323, 326, 329, 332, 335, 338, 368, 371):
        return "\u2744"   # ❄ Nieve
    if code in (179, 182, 317, 362, 365):
        return "\u2603"   # ☃ Aguanieve
    if code in (350, 374, 377):
        return "\u26c6"   # ⛆ Granizo
    return "\u2602"       # ☂ Lluvia

# Flecha de viento: direccion DESDE donde sopla -> apunta hacia donde VA el viento
WIND_ARROWS = {
    'N':   '\u2193',  # ↓
    'NNE': '\u2199',  # ↙
    'NE':  '\u2199',  # ↙
    'ENE': '\u2190',  # ←
    'E':   '\u2190',  # ←
    'ESE': '\u2196',  # ↖
    'SE':  '\u2196',  # ↖
    'SSE': '\u2191',  # ↑
    'S':   '\u2191',  # ↑
    'SSW': '\u2197',  # ↗
    'SW':  '\u2197',  # ↗
    'WSW': '\u2192',  # →
    'W':   '\u2192',  # →
    'WNW': '\u2198',  # ↘
    'NW':  '\u2198',  # ↘
    'NNW': '\u2193',  # ↓
}


class ClockWeatherPanel(tk.Frame):
    """Cajon 4 — Reloj digital + tiempo de Barcelona (wttr.in)."""

    def __init__(self, parent, weather_service, **kwargs):
        kwargs.setdefault('bg', BG_PANEL)
        super().__init__(parent, **kwargs)
        self._weather_service = weather_service
        self._bg = self.cget('bg')
        self._build_ui()
        self._tick()
        self._poll_weather()

    # ------------------------------------------------------------------
    # Construccion del layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        bg = self._bg

        # --- Header ---
        header = tk.Frame(self, bg=bg, height=32)
        header.pack(fill='x', padx=10, pady=(8, 4))
        header.pack_propagate(False)

        tk.Label(
            header, text="HORA & TIEMPO",
            font=FONT_TITLE, fg=ACCENT_CLOCK, bg=bg,
        ).pack(side='left', pady=4)

        self._fresh_dot = tk.Label(
            header, text="\u25cf", font=('Courier', 10),
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

        # --- Reloj (centrado, expandido) ---
        clock_frame = tk.Frame(self, bg=bg)
        clock_frame.pack(fill='both', expand=True, padx=12, pady=(6, 4))

        # Spacer superior
        tk.Frame(clock_frame, bg=bg).pack(expand=True)

        time_row = tk.Frame(clock_frame, bg=bg)
        time_row.pack()

        self._time_label = tk.Label(
            time_row, text="--:--",
            font=FONT_CLOCK, fg=TEXT_PRIMARY, bg=bg,
        )
        self._time_label.pack(side='left')

        self._sec_label = tk.Label(
            time_row, text=":--",
            font=FONT_CLOCK_SEC, fg=TEXT_SECONDARY, bg=bg,
        )
        self._sec_label.pack(side='left', anchor='s', pady=(0, 10))

        self._date_label = tk.Label(
            clock_frame, text="",
            font=FONT_CLOCK_DATE, fg=TEXT_SECONDARY, bg=bg,
        )
        self._date_label.pack(pady=(2, 0))

        # Spacer inferior
        tk.Frame(clock_frame, bg=bg).pack(expand=True)

        # --- Separador ---
        tk.Frame(self, bg=BORDER, height=1).pack(fill='x', padx=8)

        # --- Tiempo (seccion inferior) ---
        weather_frame = tk.Frame(self, bg=bg)
        weather_frame.pack(fill='both', expand=True, padx=16, pady=(8, 10))

        # Fila principal: icono grande + temperatura + sensacion termica
        top_row = tk.Frame(weather_frame, bg=bg)
        top_row.pack(fill='x', pady=(0, 4))

        self._icon_label = tk.Label(
            top_row, text="",
            font=('Courier', 28), fg=ACCENT_CLOCK, bg=bg,
        )
        self._icon_label.pack(side='left', padx=(0, 14))

        temp_col = tk.Frame(top_row, bg=bg)
        temp_col.pack(side='left')

        self._temp_label = tk.Label(
            temp_col, text="--°C",
            font=FONT_WEATHER_TEMP, fg=TEXT_PRIMARY, bg=bg, anchor='w',
        )
        self._temp_label.pack(anchor='w')

        self._feels_label = tk.Label(
            temp_col, text="Sensacion: --°C",
            font=FONT_WEATHER, fg=TEXT_SECONDARY, bg=bg, anchor='w',
        )
        self._feels_label.pack(anchor='w')

        # Descripcion del tiempo
        self._desc_label = tk.Label(
            weather_frame, text="",
            font=FONT_WEATHER, fg=TEXT_SECONDARY, bg=bg, anchor='w',
        )
        self._desc_label.pack(fill='x', pady=(0, 6))

        # Fila viento: flecha + velocidad + direccion
        wind_row = tk.Frame(weather_frame, bg=bg)
        wind_row.pack(fill='x', pady=(0, 4))

        self._wind_arrow = tk.Label(
            wind_row, text="",
            font=('Courier', 18), fg=ACCENT_CLOCK, bg=bg,
        )
        self._wind_arrow.pack(side='left', padx=(0, 6))

        self._wind_label = tk.Label(
            wind_row, text="Viento: -- km/h",
            font=FONT_WEATHER, fg=TEXT_SECONDARY, bg=bg,
        )
        self._wind_label.pack(side='left')

        # Humedad
        self._humidity_label = tk.Label(
            weather_frame, text="Humedad: --%",
            font=FONT_WEATHER, fg=TEXT_SECONDARY, bg=bg, anchor='w',
        )
        self._humidity_label.pack(fill='x')

    # ------------------------------------------------------------------
    # Actualizacion del reloj (cada segundo, hilo principal)
    # ------------------------------------------------------------------

    def _tick(self):
        now = datetime.datetime.now()
        self._time_label.config(text=now.strftime("%H:%M"))
        self._sec_label.config(text=f":{now.strftime('%S')}")

        dia = DIAS_ES[now.weekday()]
        mes = MESES_ES[now.month]
        self._date_label.config(
            text=f"{dia}, {now.day} de {mes} de {now.year}"
        )
        self.after(1000, self._tick)

    # ------------------------------------------------------------------
    # Actualizacion del tiempo (polling cada 60s sobre cache del servicio)
    # ------------------------------------------------------------------

    def _poll_weather(self):
        data = self._weather_service.get_data()
        self._update_weather(data)
        if data['temp_c'] is None:
            self.after(5_000, self._poll_weather)
        else:
            self.after(60_000, self._poll_weather)

    def _update_weather(self, data):
        if data['temp_c'] is None:
            msg = "Cargando..." if data['error'] is None else "Sin datos"
            self._temp_label.config(text="--°C", fg=TEXT_PRIMARY)
            self._icon_label.config(text="")
            self._desc_label.config(text=msg, fg=TEXT_SECONDARY)
            self._feels_label.config(text="Sensacion: --°C")
            self._wind_arrow.config(text="")
            self._wind_label.config(text="Viento: -- km/h")
            self._humidity_label.config(text="Humedad: --%")
            self._fresh_dot.config(fg=ERROR)
            self._fresh_label.config(text="")
            return

        code = data.get('weather_code', 113)
        wind_dir = data.get('wind_dir', '')
        arrow = WIND_ARROWS.get(wind_dir, '')

        self._icon_label.config(text=_weather_icon(code), fg=ACCENT_CLOCK)
        self._temp_label.config(text=f"{data['temp_c']}°C", fg=TEXT_PRIMARY)
        self._feels_label.config(text=f"Sensacion: {data['feels_like_c']}°C")
        self._desc_label.config(text=data['description'] or "")
        self._wind_arrow.config(text=arrow)
        wind_dir_str = f" ({wind_dir})" if wind_dir and wind_dir != '--' else ""
        self._wind_label.config(text=f"Viento: {data['wind_kmh']} km/h{wind_dir_str}")
        self._humidity_label.config(text=f"Humedad: {data['humidity']}%")

        ts = data['timestamp']
        color = freshness_color(ts, 1800)
        self._fresh_dot.config(fg=color)
        self._fresh_label.config(
            text=f"Actualizado hace {time_ago(ts)}" if ts else ""
        )
