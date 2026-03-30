import tkinter as tk
import platform
import logging

from ui.theme import BG_GLOBAL, BG_PANEL, BORDER
from ui.widgets.top_bar import TopBar
from ui.widgets.market_panel import MarketPanel

logger = logging.getLogger(__name__)


class App(tk.Tk):
    """Ventana principal: barra superior + mercados + noticias, fullscreen cross-platform."""

    def __init__(self, config, cmc_service, market_service, weather_service):
        super().__init__()
        self._cfg = config
        display     = config.get('display', {})
        fullscreen  = display.get('fullscreen', True)
        hide_cursor = display.get('hide_cursor', True)

        self.title("Crypto Wall Dashboard")
        self.configure(bg=BG_GLOBAL)
        self.resizable(False, False)

        # Resolución simulada (para desarrollo cross-platform)
        sim_res = display.get('sim_resolution')  # e.g. "1024x768"
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

        # Proporciones del layout sobre la resolución efectiva
        self.update_idletasks()
        sw = sim_w or self.winfo_screenwidth()
        sh = sim_h or self.winfo_screenheight()
        logger.info(f"Resolución efectiva para layout: {sw}x{sh}")

        # 1 columna ancho completo
        self.grid_columnconfigure(0, weight=1)
        # Filas: top_bar 5%, market 95%
        self.grid_rowconfigure(0, weight=0, minsize=int(sh * 0.05))
        self.grid_rowconfigure(1, weight=1, minsize=int(sh * 0.95))

        # --- Fila 0: Barra superior (hora + fecha + tiempo) ---
        self.top_bar = TopBar(self, weather_service, bg='#000000')
        self.top_bar.grid(row=0, column=0, sticky='nsew')

        # --- Fila 1: Mercados / Cryptos ---
        self.market_panel = MarketPanel(
            self, cmc_service, market_service,
            bg=BG_PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.market_panel.grid(row=1, column=0, sticky='nsew', pady=(1, 0))

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
