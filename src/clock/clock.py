#!/usr/bin/env python3
"""
Crypto Wall Dashboard — Test v0.1
Reloj fullscreen con hora de Madrid sobre fondo negro.
Diseñado para Raspberry Pi 4 + pantalla 1024×600.
"""

import tkinter as tk
import platform
from datetime import datetime, timezone, timedelta

# Zona horaria Madrid (CET/CEST simplificado)
# Para producción usar pytz o zoneinfo, pero esto funciona sin dependencias extra
def get_madrid_time():
    utc = datetime.now(timezone.utc)
    # Madrid: UTC+1 (invierno) / UTC+2 (verano)
    # Regla simplificada: último domingo marzo → último domingo octubre = verano
    year = utc.year
    # Último domingo de marzo
    mar31 = datetime(year, 3, 31, tzinfo=timezone.utc)
    start_summer = mar31 - timedelta(days=(mar31.weekday() + 1) % 7)
    start_summer = start_summer.replace(hour=1)
    # Último domingo de octubre
    oct31 = datetime(year, 10, 31, tzinfo=timezone.utc)
    end_summer = oct31 - timedelta(days=(oct31.weekday() + 1) % 7)
    end_summer = end_summer.replace(hour=1)

    if start_summer <= utc < end_summer:
        offset = timedelta(hours=2)
    else:
        offset = timedelta(hours=1)

    return utc + offset

class ClockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Crypto Wall Dashboard")
        self.root.configure(bg="#0a0a1a")
        
        # Fullscreen cross-platform
        self.set_fullscreen()
        
        # Salir con Escape (para debug)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        # Ocultar cursor
        self.root.config(cursor="none")

        # Hora grande
        self.time_label = tk.Label(
            self.root,
            text="",
            font=("DejaVu Sans Mono", 72, "bold"),
            fg="#00d4ff",
            bg="#0a0a1a"
        )
        self.time_label.place(relx=0.5, rely=0.45, anchor="center")

        # Fecha debajo
        self.date_label = tk.Label(
            self.root,
            text="",
            font=("DejaVu Sans", 20),
            fg="#8888aa",
            bg="#0a0a1a"
        )
        self.date_label.place(relx=0.5, rely=0.58, anchor="center")

        # Etiqueta zona horaria
        self.tz_label = tk.Label(
            self.root,
            text="Madrid, España",
            font=("DejaVu Sans", 14),
            fg="#555577",
            bg="#0a0a1a"
        )
        self.tz_label.place(relx=0.5, rely=0.66, anchor="center")

        self.update_clock()

    def set_fullscreen(self):
        """Configura fullscreen de forma cross-platform sin decoraciones de ventana"""
        system = platform.system().lower()
        
        if system == "linux":
            # Linux: evitar overrideredirect que causa problemas con window managers
            # Usar -fullscreen attribute directamente
            try:
                self.root.attributes("-fullscreen", True)
                # Ocultar bordes de ventana en Linux
                self.root.wm_attributes('-type', 'splash')
            except tk.TclError:
                # Fallback: maximizar ventana
                self.root.state('zoomed')
        elif system == "windows":
            # Windows: usar overrideredirect + zoomed
            try:
                self.root.overrideredirect(True)
            except tk.TclError:
                pass
            self.root.state('zoomed')
        else:
            # Otros sistemas (macOS, etc.): intentar ambos métodos
            try:
                self.root.overrideredirect(True)
                self.root.attributes("-fullscreen", True)
            except tk.TclError:
                try:
                    self.root.state('zoomed')
                except:
                    pass

    def update_clock(self):
        now = get_madrid_time()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%A %d de %B de %Y"))
        # Actualizar cada 500ms
        self.root.after(500, self.update_clock)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ClockApp()
    app.run()