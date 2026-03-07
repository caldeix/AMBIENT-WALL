import tkinter as tk
import datetime

from ui.theme import (
    BG_PANEL, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_MARKET, ERROR, WARNING,
    FONT_TITLE, FONT_BTC, FONT_CHANGE, FONT_SECONDARY,
    FONT_LABEL, FONT_TIMESTAMP,
)
from utils.formatting import (
    fmt_usd, fmt_change, fmt_gold, fmt_sp500,
    fmt_eur, fmt_ibex, usd_to_eur,
    time_ago, freshness_color,
)

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def _is_nyse_open():
    """Comprueba si el mercado NYSE esta abierto segun hora local (Barcelona)."""
    now = datetime.datetime.now()
    if now.weekday() >= 5:
        return False
    # NYSE abre 15:30-22:00 CEST (UTC+2, verano) o 14:30-21:00 CET (UTC+1, invierno)
    # Usamos el offset real del sistema (que en Barcelona ya esta ajustado)
    import time as _time
    utc_offset_h = -(_time.timezone if not _time.daylight else _time.altzone) / 3600
    # NYSE abre 9:30 ET (UTC-5 EST / UTC-4 EDT)
    # Apertura en hora local = 14:30 CET / 15:30 CEST
    nyse_open_local  = 9.5  + (utc_offset_h + 5)   # 9:30 ET -> hora local
    nyse_close_local = 16.0 + (utc_offset_h + 5)   # 16:00 ET -> hora local
    current_h = now.hour + now.minute / 60
    return nyse_open_local <= current_h <= nyse_close_local


class MarketPanel(tk.Frame):
    """Cajon 1 — Mercados: BTC (precio + sparkline 7d), Oro, S&P500."""

    def __init__(self, parent, cmc_service, market_service, **kwargs):
        kwargs.setdefault('bg', BG_PANEL)
        super().__init__(parent, **kwargs)
        self._cmc     = cmc_service
        self._market  = market_service
        self._bg      = self.cget('bg')
        self._fig     = None
        self._ax      = None
        self._canvas  = None
        self._build_ui()
        self._poll()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        bg = self._bg

        # --- Header ---
        header = tk.Frame(self, bg=bg, height=32)
        header.pack(fill='x', padx=10, pady=(8, 4))
        header.pack_propagate(False)

        tk.Label(
            header, text="MERCADOS",
            font=FONT_TITLE, fg=ACCENT_MARKET, bg=bg,
        ).pack(side='left', pady=4)

        self._fresh_dot = tk.Label(
            header, text="●", font=('Courier', 10),
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

        # --- Fila BTC ---
        btc_row = tk.Frame(self, bg=bg)
        btc_row.pack(fill='x', padx=12, pady=(10, 2))

        tk.Label(
            btc_row, text="BTC",
            font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg,
        ).pack(side='left', padx=(0, 8))

        self._btc_price = tk.Label(
            btc_row, text="$--",
            font=FONT_BTC, fg=TEXT_PRIMARY, bg=bg,
        )
        self._btc_price.pack(side='left')

        self._btc_change = tk.Label(
            btc_row, text="",
            font=FONT_CHANGE, fg=TEXT_SECONDARY, bg=bg,
        )
        self._btc_change.pack(side='left', padx=(12, 0))

        # --- Sparkline matplotlib ---
        if HAS_MPL:
            chart_outer = tk.Frame(self, bg=bg)
            chart_outer.pack(fill='x', padx=8, pady=(4, 0))

            self._fig = Figure(figsize=(4.7, 0.75), dpi=100)
            self._fig.patch.set_facecolor(BG_PANEL)
            self._ax = self._fig.add_subplot(111)
            self._ax.set_facecolor(BG_PANEL)
            self._fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05)

            self._canvas = FigureCanvasTkAgg(self._fig, master=chart_outer)
            widget = self._canvas.get_tk_widget()
            widget.configure(bg=BG_PANEL, highlightthickness=0, bd=0)
            widget.pack(fill='x')

            # Etiquetas de fecha debajo del grafico
            date_row = tk.Frame(self, bg=bg)
            date_row.pack(fill='x', padx=14)
            self._date_start = tk.Label(
                date_row, text="", font=FONT_TIMESTAMP,
                fg=TEXT_SECONDARY, bg=bg,
            )
            self._date_start.pack(side='left')
            self._date_end = tk.Label(
                date_row, text="", font=FONT_TIMESTAMP,
                fg=TEXT_SECONDARY, bg=bg,
            )
            self._date_end.pack(side='right')
        else:
            self._date_start = None
            self._date_end = None
            tk.Label(
                self, text="[instalar matplotlib para el grafico]",
                font=FONT_TIMESTAMP, fg=WARNING, bg=bg,
            ).pack(pady=8)

        # --- Separador cripto principal / secundaria ---
        tk.Frame(self, bg=BORDER, height=1).pack(fill='x', padx=8, pady=(3, 0))

        # --- ETH ---
        eth_row = tk.Frame(self, bg=bg)
        eth_row.pack(fill='x', padx=12, pady=(3, 1))
        tk.Label(eth_row, text="ETH", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._eth_eur = tk.Label(eth_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._eth_eur.pack(side='right', padx=(0, 6))
        self._eth_label = tk.Label(eth_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._eth_label.pack(side='left')

        # --- SOL ---
        sol_row = tk.Frame(self, bg=bg)
        sol_row.pack(fill='x', padx=12, pady=(2, 1))
        tk.Label(sol_row, text="SOL", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._sol_eur = tk.Label(sol_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._sol_eur.pack(side='right', padx=(0, 6))
        self._sol_label = tk.Label(sol_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._sol_label.pack(side='left')

        # --- XRP ---
        xrp_row = tk.Frame(self, bg=bg)
        xrp_row.pack(fill='x', padx=12, pady=(2, 1))
        tk.Label(xrp_row, text="XRP", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._xrp_eur = tk.Label(xrp_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._xrp_eur.pack(side='right', padx=(0, 6))
        self._xrp_label = tk.Label(xrp_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._xrp_label.pack(side='left')

        # --- DOT ---
        dot_row = tk.Frame(self, bg=bg)
        dot_row.pack(fill='x', padx=12, pady=(2, 1))
        tk.Label(dot_row, text="DOT", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._dot_eur = tk.Label(dot_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._dot_eur.pack(side='right', padx=(0, 6))
        self._dot_label = tk.Label(dot_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._dot_label.pack(side='left')

        # --- POPCAT ---
        popcat_row = tk.Frame(self, bg=bg)
        popcat_row.pack(fill='x', padx=12, pady=(2, 1))
        tk.Label(popcat_row, text="POPCAT", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._popcat_eur = tk.Label(popcat_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._popcat_eur.pack(side='right', padx=(0, 6))
        self._popcat_label = tk.Label(popcat_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._popcat_label.pack(side='left')

        # --- WIF ---
        wif_row = tk.Frame(self, bg=bg)
        wif_row.pack(fill='x', padx=12, pady=(2, 1))
        tk.Label(wif_row, text="WIF", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._wif_eur = tk.Label(wif_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._wif_eur.pack(side='right', padx=(0, 6))
        self._wif_label = tk.Label(wif_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._wif_label.pack(side='left')

        # --- ALI ---
        ali_row = tk.Frame(self, bg=bg)
        ali_row.pack(fill='x', padx=12, pady=(2, 1))
        tk.Label(ali_row, text="ALI", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._ali_eur = tk.Label(ali_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._ali_eur.pack(side='right', padx=(0, 6))
        self._ali_label = tk.Label(ali_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._ali_label.pack(side='left')

        # --- AURA ---
        aura_row = tk.Frame(self, bg=bg)
        aura_row.pack(fill='x', padx=12, pady=(2, 1))
        tk.Label(aura_row, text="AURA", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._aura_eur = tk.Label(aura_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._aura_eur.pack(side='right', padx=(0, 6))
        self._aura_label = tk.Label(aura_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._aura_label.pack(side='left')

        # --- Separador cripto / mercados tradicionales ---
        tk.Frame(self, bg=BORDER, height=1).pack(fill='x', padx=8, pady=(3, 0))

        # --- ORO ---
        gold_row = tk.Frame(self, bg=bg)
        gold_row.pack(fill='x', padx=12, pady=(3, 1))
        tk.Label(gold_row, text="ORO", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._gold_eur = tk.Label(gold_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._gold_eur.pack(side='right', padx=(0, 6))
        self._gold_label = tk.Label(gold_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._gold_label.pack(side='left')

        # --- PLATA ---
        silver_row = tk.Frame(self, bg=bg)
        silver_row.pack(fill='x', padx=12, pady=(2, 1))
        tk.Label(silver_row, text="PLATA", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._silver_eur = tk.Label(silver_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._silver_eur.pack(side='right', padx=(0, 6))
        self._silver_label = tk.Label(silver_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._silver_label.pack(side='left')

        # --- S&P500 ---
        sp_row = tk.Frame(self, bg=bg)
        sp_row.pack(fill='x', padx=12, pady=(2, 1))
        tk.Label(sp_row, text="S&P500", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._sp_status = tk.Label(sp_row, text="", font=FONT_TIMESTAMP, fg=TEXT_SECONDARY, bg=bg)
        self._sp_status.pack(side='right')
        self._sp_eur = tk.Label(sp_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._sp_eur.pack(side='right', padx=(0, 6))
        self._sp_label = tk.Label(sp_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._sp_label.pack(side='left')

        # --- IBEX35 ---
        ibex_row = tk.Frame(self, bg=bg)
        ibex_row.pack(fill='x', padx=12, pady=(2, 4))
        tk.Label(ibex_row, text="IBEX35", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg, width=7, anchor='w').pack(side='left')
        self._ibex_eur = tk.Label(ibex_row, text="", font=FONT_LABEL, fg=TEXT_SECONDARY, bg=bg)
        self._ibex_eur.pack(side='right', padx=(0, 6))
        self._ibex_label = tk.Label(ibex_row, text="--", font=FONT_SECONDARY, fg=TEXT_PRIMARY, bg=bg)
        self._ibex_label.pack(side='left')

    # ------------------------------------------------------------------
    # Polling y actualizacion (hilo principal via self.after)
    # ------------------------------------------------------------------

    def _poll(self):
        self._update_display()
        self.after(5_000, self._poll)

    def _update_display(self):
        cmc    = self._cmc.get_data()
        market = self._market.get_data()

        # --- BTC precio + variacion ---
        if cmc['btc_price'] is not None:
            self._btc_price.config(text=fmt_usd(cmc['btc_price']), fg=TEXT_PRIMARY)
            change_text, change_color = fmt_change(cmc['btc_change_24h'])
            self._btc_change.config(text=change_text, fg=change_color)
        else:
            self._btc_price.config(text="Dato no disponible", fg=ERROR)
            self._btc_change.config(text="")

        # Indicador de frescura (basado en timestamp CMC)
        ts = cmc.get('timestamp')
        dot_color = freshness_color(ts, 300)
        self._fresh_dot.config(fg=dot_color)
        if ts:
            self._fresh_label.config(
                text=f"Actualizado hace {time_ago(ts)}"
            )

        # --- Sparkline ---
        if self._fig is not None:
            self._update_chart(
                market.get('btc_history'),
                market.get('btc_history_dates'),
            )

        eurusd = market.get('eurusd_rate')

        # --- ETH ---
        eth = cmc.get('eth_price')
        if eth is not None:
            self._eth_label.config(text=fmt_usd(eth), fg=TEXT_PRIMARY)
            eur = usd_to_eur(eth, eurusd)
            self._eth_eur.config(text=fmt_eur(eur) if eur else "")
        else:
            self._eth_label.config(text="--", fg=TEXT_SECONDARY)
            self._eth_eur.config(text="")

        # --- SOL ---
        sol = cmc.get('sol_price')
        if sol is not None:
            self._sol_label.config(text=fmt_usd(sol), fg=TEXT_PRIMARY)
            eur = usd_to_eur(sol, eurusd)
            self._sol_eur.config(text=fmt_eur(eur) if eur else "")
        else:
            self._sol_label.config(text="--", fg=TEXT_SECONDARY)
            self._sol_eur.config(text="")

        # --- XRP ---
        xrp = cmc.get('xrp_price')
        if xrp is not None:
            self._xrp_label.config(text=fmt_usd(xrp), fg=TEXT_PRIMARY)
            eur = usd_to_eur(xrp, eurusd)
            self._xrp_eur.config(text=fmt_eur(eur) if eur else "")
        else:
            self._xrp_label.config(text="--", fg=TEXT_SECONDARY)
            self._xrp_eur.config(text="")

        # --- DOT ---
        dot = cmc.get('dot_price')
        if dot is not None:
            self._dot_label.config(text=fmt_usd(dot), fg=TEXT_PRIMARY)
            eur = usd_to_eur(dot, eurusd)
            self._dot_eur.config(text=fmt_eur(eur) if eur else "")
        else:
            self._dot_label.config(text="--", fg=TEXT_SECONDARY)
            self._dot_eur.config(text="")

        # --- POPCAT ---
        popcat = cmc.get('popcat_price')
        if popcat is not None:
            self._popcat_label.config(text=fmt_usd(popcat, 4), fg=TEXT_PRIMARY)
            eur = usd_to_eur(popcat, eurusd)
            self._popcat_eur.config(text=fmt_eur(eur, 4) if eur else "")
        else:
            self._popcat_label.config(text="--", fg=TEXT_SECONDARY)
            self._popcat_eur.config(text="")

        # --- WIF ---
        wif = cmc.get('wif_price')
        if wif is not None:
            self._wif_label.config(text=fmt_usd(wif, 4), fg=TEXT_PRIMARY)
            eur = usd_to_eur(wif, eurusd)
            self._wif_eur.config(text=fmt_eur(eur, 4) if eur else "")
        else:
            self._wif_label.config(text="--", fg=TEXT_SECONDARY)
            self._wif_eur.config(text="")

        # --- ALI ---
        ali = cmc.get('ali_price')
        if ali is not None:
            self._ali_label.config(text=fmt_usd(ali, 4), fg=TEXT_PRIMARY)
            eur = usd_to_eur(ali, eurusd)
            self._ali_eur.config(text=fmt_eur(eur, 4) if eur else "")
        else:
            self._ali_label.config(text="--", fg=TEXT_SECONDARY)
            self._ali_eur.config(text="")

        # --- AURA ---
        aura = cmc.get('aura_price')
        if aura is not None:
            self._aura_label.config(text=fmt_usd(aura, 4), fg=TEXT_PRIMARY)
            eur = usd_to_eur(aura, eurusd)
            self._aura_eur.config(text=fmt_eur(eur, 4) if eur else "")
        else:
            self._aura_label.config(text="--", fg=TEXT_SECONDARY)
            self._aura_eur.config(text="")

        # --- Oro ---
        gold = market.get('gold_price')
        if gold is not None:
            self._gold_label.config(text=fmt_gold(gold), fg=TEXT_PRIMARY)
            eur = usd_to_eur(gold, eurusd)
            self._gold_eur.config(text=fmt_eur(eur) + " /oz" if eur else "")
        else:
            self._gold_label.config(text="Dato no disponible", fg=ERROR)
            self._gold_eur.config(text="")

        # --- Plata ---
        silver = market.get('silver_price')
        if silver is not None:
            self._silver_label.config(text=fmt_gold(silver), fg=TEXT_PRIMARY)
            eur = usd_to_eur(silver, eurusd)
            self._silver_eur.config(text=fmt_eur(eur) + " /oz" if eur else "")
        else:
            self._silver_label.config(text="Dato no disponible", fg=ERROR)
            self._silver_eur.config(text="")

        # --- S&P 500 ---
        sp = market.get('sp500_price')
        if sp is not None:
            self._sp_label.config(text=fmt_sp500(sp), fg=TEXT_PRIMARY)
            eur = usd_to_eur(sp, eurusd)
            self._sp_eur.config(text=fmt_eur(eur, 0) + " pts" if eur else "")
            self._sp_status.config(
                text="cerrado" if not _is_nyse_open() else "",
                fg=TEXT_SECONDARY,
            )
        else:
            self._sp_label.config(text="Dato no disponible", fg=ERROR)
            self._sp_eur.config(text="")
            self._sp_status.config(text="")

        # --- IBEX35 ---
        ibex = market.get('ibex_price')
        if ibex is not None:
            self._ibex_label.config(text=fmt_ibex(ibex), fg=TEXT_PRIMARY)
            self._ibex_eur.config(text=fmt_eur(ibex, 0) + " pts")
        else:
            self._ibex_label.config(text="Dato no disponible", fg=ERROR)
            self._ibex_eur.config(text="")

    def _update_chart(self, prices, dates):
        self._ax.clear()
        self._ax.set_facecolor(BG_PANEL)
        self._ax.axis('off')

        if prices and len(prices) > 2:
            x = list(range(len(prices)))
            mn = min(prices)
            mx = max(prices)
            padding = (mx - mn) * 0.12 if mx != mn else 1.0

            self._ax.set_ylim(mn - padding, mx + padding)
            self._ax.plot(
                x, prices,
                color=ACCENT_MARKET, linewidth=1.5,
                solid_capstyle='round', solid_joinstyle='round',
            )
            self._ax.fill_between(
                x, prices, mn - padding,
                alpha=0.15, color=ACCENT_MARKET,
            )
        else:
            # Sin datos: linea gris horizontal + texto
            self._ax.axhline(y=0.5, color=TEXT_SECONDARY, linewidth=1, alpha=0.4)
            self._ax.text(
                0.5, 0.5, 'Sin datos',
                transform=self._ax.transAxes,
                ha='center', va='center',
                color=TEXT_SECONDARY, fontsize=9,
            )

        self._fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05)
        self._canvas.draw_idle()

        if self._date_start and dates:
            self._date_start.config(text=dates[0] if dates[0] else "")
            self._date_end.config(text=dates[1] if dates[1] else "")
