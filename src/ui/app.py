import tkinter as tk
import platform
import logging

from ui.theme import BG_GLOBAL, BG_PANEL, BORDER
from ui.widgets.top_bar import TopBar
from ui.widgets.market_panel import MarketPanel

logger = logging.getLogger(__name__)


class App(tk.Tk):
    """Ventana principal: barra superior + panel de mercados, fullscreen cross-platform."""

    def __init__(self, config, cmc_service, market_service, weather_service, config_manager=None):
        super().__init__()
        self._cfg   = config
        display     = config.get('display', {})
        fullscreen  = display.get('fullscreen', True)
        hide_cursor = display.get('hide_cursor', True)

        self.title("Financial Wall Dashboard")
        self.configure(bg=BG_GLOBAL)
        self.resizable(False, False)

        sim_res = display.get('sim_resolution')
        if sim_res:
            sim_w, sim_h = (int(x) for x in sim_res.split('x'))
        else:
            sim_w, sim_h = None, None

        if fullscreen:
            self._set_fullscreen()
        else:
            w = sim_w or self.winfo_screenwidth()
            h = sim_h or self.winfo_screenheight()
            logger.info(f"Ventana desarrollo: {w}x{h}")
            self.geometry(f"{w}x{h}+0+0")

        if hide_cursor:
            self.config(cursor='none')

        self.update_idletasks()
        sw = sim_w or self.winfo_screenwidth()
        sh = sim_h or self.winfo_screenheight()
        logger.info(f"Resolución efectiva para layout: {sw}x{sh}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0, minsize=int(sh * 0.05))
        self.grid_rowconfigure(1, weight=1, minsize=int(sh * 0.95))

        self.top_bar = TopBar(self, weather_service, bg='#000000')
        self.top_bar.grid(row=0, column=0, sticky='nsew')

        self.market_panel = MarketPanel(
            self, cmc_service, market_service,
            config=config,
            config_manager=config_manager,
            bg=BG_PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.market_panel.grid(row=1, column=0, sticky='nsew', pady=(1, 0))

        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<F11>', self._toggle_fullscreen)
        logger.info(f"UI inicializada (fullscreen={fullscreen})")

    def _set_fullscreen(self):
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
        current = bool(self.attributes('-fullscreen'))
        if current:
            self.attributes('-fullscreen', False)
        else:
            self._set_fullscreen()
