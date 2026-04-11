import tkinter as tk
import datetime

DIAS_ES = [
    'Lunes', 'Martes', 'Miercoles', 'Jueves',
    'Viernes', 'Sabado', 'Domingo',
]
MESES_ES = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

_BG = '#000000'
_FG = '#e0e0e0'
_FONT = ('Courier', 14, 'bold')


class TopBar(tk.Frame):
    """Barra superior negra con hora, fecha y resumen del tiempo (1 linea)."""

    def __init__(self, parent, weather_service, **kwargs):
        kwargs.setdefault('bg', _BG)
        super().__init__(parent, **kwargs)
        self._weather = weather_service

        self._label = tk.Label(
            self,
            text='',
            bg=_BG,
            fg=_FG,
            font=_FONT,
            anchor='center',
        )
        self._label.pack(expand=True, fill='both')

        self._tick()

    def _tick(self):
        now = datetime.datetime.now()
        hora = now.strftime('%H:%M:%S')
        dia_semana = DIAS_ES[now.weekday()]
        dia_num = now.day
        mes = MESES_ES[now.month]
        anio = now.year
        fecha = f"{dia_semana} {dia_num} de {mes} de {anio}"

        # Tiempo de Barcelona desde cache del servicio
        w = self._weather.get_data()
        temp = w.get('temp_c')
        desc = w.get('description')
        if temp is not None and desc:
            tiempo = f"{self._weather.city}  {temp}°  {desc}"
        elif temp is not None:
            tiempo = f"{self._weather.city}  {temp}°"
        else:
            tiempo = f"{self._weather.city}  --"

        self._label.config(text=f"  {hora}   -   {fecha}   -   {tiempo}  ")
        self.after(1000, self._tick)
