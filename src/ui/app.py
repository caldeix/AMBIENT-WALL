import tkinter as tk
import platform
import logging

from ui.theme import BG_GLOBAL, BG_PANEL, BORDER
from ui.widgets.market_panel import MarketPanel
from ui.widgets.news_panel import NewsPanel
from ui.widgets.clock_weather_panel import ClockWeatherPanel

logger = logging.getLogger(__name__)


class App(tk.Tk):
    """Ventana principal: grid 2+1 (2 cajones arriba + noticias abajo), fullscreen cross-platform."""

    def __init__(self, config, cmc_service, market_service, weather_service, rss_service):
        super().__init__()
        self._cfg = config
        display   = config.get('display', {})
        fullscreen  = display.get('fullscreen', True)
        hide_cursor = display.get('hide_cursor', True)

        self.title("Crypto Wall Dashboard")
        self.configure(bg=BG_GLOBAL)
        self.resizable(False, False)

        # Resolución simulada (para desarrollo cross-platform)
        sim_res = display.get('sim_resolution')  # e.g. "1024x600"
        if sim_res:
            sim_w, sim_h = (int(x) for x in sim_res.split('x'))
        else:
            sim_w, sim_h = None, None

        if fullscreen:
            self._set_fullscreen()
        else:
            # Modo ventana (desarrollo): usar resolución simulada si está definida
            w = sim_w or self.winfo_screenwidth()
            h = sim_h or self.winfo_screenheight()
            logger.info(f"Ventana desarrollo: {w}x{h}")
            self.geometry(f"{w}x{h}+0+0")

        if hide_cursor:
            self.config(cursor='none')

        # Forzar layout con minsize en píxeles para que funcione igual en Linux y Windows
        # weight solo distribuye espacio "extra"; minsize garantiza la proporción real
        self.update_idletasks()
        sw = sim_w or self.winfo_screenwidth()
        sh = sim_h or self.winfo_screenheight()
        logger.info(f"Resolución efectiva para layout: {sw}x{sh}")

        # Grid 2+1: col 0 (tiempo) 75%, col 1 (crypto) 25%
        self.grid_columnconfigure(0, weight=3, minsize=int(sw * 0.65))
        self.grid_columnconfigure(1, weight=1, minsize=int(sw * 0.35))
        # Filas: arriba 88%, noticias 12%
        self.grid_rowconfigure(0, weight=8, minsize=int(sh * 0.80))
        self.grid_rowconfigure(1, weight=1, minsize=int(sh * 0.20))

        # --- Cajon 1: Reloj + Tiempo (arriba-izquierda) ---
        self.clock_panel = ClockWeatherPanel(
            self, weather_service,
            bg=BG_PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.clock_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 1), pady=(0, 1))

        # --- Cajon 2: Mercados / Cryptos (arriba-derecha) ---
        self.market_panel = MarketPanel(
            self, cmc_service, market_service,
            bg=BG_PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.market_panel.grid(row=0, column=1, sticky='nsew', padx=(1, 0), pady=(0, 1))

        # --- Cajon 3: Noticias RSS (abajo, ancho completo) ---
        self.news_panel = NewsPanel(
            self, rss_service,
            bg=BG_PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.news_panel.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=(1, 0))

        # Teclas de debug (solo desarrollo)
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<F11>', self._toggle_fullscreen)

        logger.info(f"UI inicializada (fullscreen={fullscreen})")

    def _set_fullscreen(self):
        """Fullscreen kiosk cross-platform."""
        system = platform.system().lower()

        if system == "linux":
            try:
                self.attributes("-fullscreen", True)
                self.wm_attributes('-type', 'splash')
            except tk.TclError:
                self.state('zoomed')

        elif system == "windows":
            try:
                self.overrideredirect(True)
            except tk.TclError:
                pass
            self.state('zoomed')

        else:
            try:
                self.overrideredirect(True)
                self.attributes("-fullscreen", True)
            except tk.TclError:
                try:
                    self.state('zoomed')
                except Exception:
                    pass

        logger.info(f"fullscreen kiosk activado (sistema: {system})")

    def _toggle_fullscreen(self, event=None):
        """F11 alterna fullscreen."""
        current = bool(self.attributes('-fullscreen'))
        if current:
            self.attributes('-fullscreen', False)
        else:
            self._set_fullscreen()
