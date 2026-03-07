import tkinter as tk
import platform
import logging

from ui.theme import BG_GLOBAL, BG_PANEL, BORDER, ACCENT_NODE
from ui.widgets.market_panel import MarketPanel
from ui.widgets.placeholder_panel import PlaceholderPanel
from ui.widgets.news_panel import NewsPanel
from ui.widgets.clock_weather_panel import ClockWeatherPanel

logger = logging.getLogger(__name__)


class App(tk.Tk):
    """Ventana principal: grid 3+1 (3 cajones arriba + noticias abajo), fullscreen cross-platform."""

    def __init__(self, config, cmc_service, market_service, weather_service, rss_service):
        super().__init__()
        self._cfg = config
        display   = config.get('display', {})
        fullscreen  = display.get('fullscreen', True)
        hide_cursor = display.get('hide_cursor', True)

        self.title("Crypto Wall Dashboard")
        self.configure(bg=BG_GLOBAL)
        self.resizable(False, False)

        if fullscreen:
            self._set_fullscreen()
        else:
            # Modo ventana (desarrollo): centrar en pantalla con tamaño real
            self.update_idletasks()
            w = self.winfo_screenwidth()
            h = self.winfo_screenheight()
            logger.info(f"Pantalla detectada: {w}x{h}")
            self.geometry(f"{w}x{h}+0+0")

        if hide_cursor:
            self.config(cursor='none')

        # Grid 3+1: fila superior 3 columnas iguales, fila inferior ancho completo
        self.grid_columnconfigure(0, weight=1, uniform='col')
        self.grid_columnconfigure(1, weight=1, uniform='col')
        self.grid_columnconfigure(2, weight=1, uniform='col')
        self.grid_rowconfigure(0, weight=2)
        self.grid_rowconfigure(1, weight=1)

        # --- Cajon 1: Reloj + Tiempo (arriba-izquierda) ---
        self.clock_panel = ClockWeatherPanel(
            self, weather_service,
            bg=BG_PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.clock_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 1), pady=(0, 1))

        # --- Cajon 2: Mercados / Cryptos (arriba-centro) ---
        self.market_panel = MarketPanel(
            self, cmc_service, market_service,
            bg=BG_PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.market_panel.grid(row=0, column=1, sticky='nsew', padx=(1, 1), pady=(0, 1))

        # --- Cajon 3: DePIN placeholder (arriba-derecha) ---
        self.depin_panel = PlaceholderPanel(
            self,
            title="NODO DePIN",
            accent=ACCENT_NODE,
            lines=["Capacidad de almacenamiento", "Tokens ganados", "Uptime del nodo"],
            bg=BG_PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.depin_panel.grid(row=0, column=2, sticky='nsew', padx=(1, 0), pady=(0, 1))

        # --- Cajon 4: Noticias RSS (abajo, ancho completo) ---
        self.news_panel = NewsPanel(
            self, rss_service,
            bg=BG_PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.news_panel.grid(row=1, column=0, columnspan=3, sticky='nsew', pady=(1, 0))

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
