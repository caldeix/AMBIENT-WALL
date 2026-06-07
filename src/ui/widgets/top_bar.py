import tkinter as tk
import datetime

from ui.theme import (
    TOPBAR_BG, TOPBAR_CLOCK, TOPBAR_DATE, TOPBAR_WEATHER,
    SEP_BRIGHT, SEP_DARK,
    FONT_TOPBAR_CLOCK, FONT_TOPBAR_DATE, FONT_TOPBAR_WEATHER,
)

DIAS_ES = [
    'Lunes', 'Martes', 'Miercoles', 'Jueves',
    'Viernes', 'Sabado', 'Domingo',
]
MESES_ES = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]


class TopBar(tk.Frame):
    """Barra superior con hora, fecha y resumen del tiempo — 3 secciones."""

    def __init__(self, parent, weather_service, **kwargs):
        kwargs.setdefault('bg', TOPBAR_BG)
        super().__init__(parent, **kwargs)
        self._weather = weather_service
        bg = TOPBAR_BG

        self._clock_lbl = tk.Label(
            self, text='', bg=bg,
            fg=TOPBAR_CLOCK, font=FONT_TOPBAR_CLOCK, anchor='w',
        )
        self._clock_lbl.pack(side='left', padx=(16, 0))

        self._date_lbl = tk.Label(
            self, text='', bg=bg,
            fg=TOPBAR_DATE, font=FONT_TOPBAR_DATE, anchor='w',
        )
        self._date_lbl.pack(side='left', padx=(20, 0))

        self._weather_lbl = tk.Label(
            self, text='', bg=bg,
            fg=TOPBAR_WEATHER, font=FONT_TOPBAR_WEATHER, anchor='e',
        )
        self._weather_lbl.pack(side='right', padx=(0, 16))

        # Separador doble: línea brillante sobre línea oscura → efecto "glow edge"
        tk.Frame(self, bg=SEP_BRIGHT, height=1).pack(side='bottom', fill='x')
        tk.Frame(self, bg=SEP_DARK,   height=1).pack(side='bottom', fill='x')

        self._tick()

    def _tick(self):
        now = datetime.datetime.now()
        hora = now.strftime('%H:%M:%S')
        dia_semana = DIAS_ES[now.weekday()]
        dia_num = now.day
        mes = MESES_ES[now.month]
        anio = now.year

        self._clock_lbl.config(text=hora)
        self._date_lbl.config(text=f"{dia_semana} {dia_num} de {mes} de {anio}")

        w = self._weather.get_data()
        temp = w.get('temp_c')
        desc = w.get('description')
        city = getattr(self._weather, 'city', '')
        if temp is not None and desc:
            tiempo = f"{city}  {temp}°  {desc}"
        elif temp is not None:
            tiempo = f"{city}  {temp}°"
        else:
            tiempo = f"{city}  --"
        self._weather_lbl.config(text=tiempo)

        self.after(1000, self._tick)
