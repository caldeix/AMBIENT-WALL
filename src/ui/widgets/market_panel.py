import tkinter as tk
import datetime

from ui.theme import (
    BG_PANEL, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_MARKET, ERROR, WARNING, POSITIVE, NEGATIVE,
    FONT_BTC, FONT_CHANGE, FONT_TIMESTAMP,
)
from utils.formatting import (
    fmt_usd, fmt_gold, fmt_sp500,
    fmt_eur, fmt_ibex, usd_to_eur,
    time_ago, freshness_color,
)

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# Fuentes bloques de gráfico (fila superior x2)
_F_BLOCK_TICKER = ('Helvetica', 11, 'normal')
_F_BLOCK_PRICE  = ('Courier',   18, 'bold')
_F_BLOCK_CHANGE = ('Helvetica', 12, 'normal')

# Fuentes rejilla altcoins (+15% sobre los valores originales de 10/12pt)
_F_ALT_TICKER = ('Helvetica', 12, 'normal')   # era 10
_F_ALT_VALUE  = ('Helvetica', 14, 'normal')   # era 12
_F_ALT_EUR    = ('Helvetica', 11, 'normal')   # era 10


_CHART_CRYPTOS = {'BTC', 'ETH'}


def _auto_decimals(price):
    """Decimales segun magnitud del precio."""
    if price is None or price >= 100:
        return 2
    if price >= 0.01:
        return 4
    return 6


def _pct_change(history):
    """Calcula % de cambio entre el penúltimo y último valor del historial."""
    if history and len(history) >= 2:
        prev, last = history[-2], history[-1]
        if prev and prev != 0:
            return (last - prev) / prev * 100
    return None


def _is_nyse_open():
    now = datetime.datetime.now()
    if now.weekday() >= 5:
        return False
    import time as _time
    utc_offset_h = -(_time.timezone if not _time.daylight else _time.altzone) / 3600
    nyse_open_local  = 9.5  + (utc_offset_h + 5)
    nyse_close_local = 16.0 + (utc_offset_h + 5)
    current_h = now.hour + now.minute / 60
    return nyse_open_local <= current_h <= nyse_close_local


class MarketPanel(tk.Frame):
    """Layout:
      Fila 1: [BTC  gráfico] [ETH  gráfico] [ORO  gráfico]
      Fila 2: [S&P  gráfico] [PLATA gráfico] [IBEX gráfico]
      Fila 3: rejilla 3 columnas — altcoins restantes
    """

    def __init__(self, parent, cmc_service, market_service, **kwargs):
        kwargs.setdefault('bg', BG_PANEL)
        super().__init__(parent, **kwargs)
        self._cmc    = cmc_service
        self._market = market_service
        self._bg     = self.cget('bg')
        self._charts = {}   # ticker -> {fig, ax, canvas, price, change, date_start, date_end}
        self._build_ui()
        self._poll()

    # ------------------------------------------------------------------
    # Helpers de construcción
    # ------------------------------------------------------------------

    def _make_chart_block(self, parent, ticker, show_freshness=False):
        """Crea un bloque con ticker/precio/cambio + sparkline. Devuelve refs dict."""
        bg = self._bg
        block = tk.Frame(parent, bg=bg,
                         highlightbackground=BORDER, highlightthickness=1)

        header = tk.Frame(block, bg=bg)
        header.pack(fill='x', padx=8, pady=(6, 2))

        ticker_lbl = tk.Label(header, text=ticker, font=_F_BLOCK_TICKER,
                              fg=TEXT_SECONDARY, bg=bg)
        ticker_lbl.pack(side='left', padx=(0, 8))

        price_lbl = tk.Label(header, text="--", font=_F_BLOCK_PRICE,
                             fg=TEXT_PRIMARY, bg=bg)
        price_lbl.pack(side='left')

        change_lbl = tk.Label(header, text="", font=_F_BLOCK_CHANGE,
                              fg=TEXT_SECONDARY, bg=bg)
        change_lbl.pack(side='left', padx=(8, 0))

        refs = {
            'ticker_lbl': ticker_lbl,
            'price': price_lbl, 'change': change_lbl,
            'fig': None, 'ax': None, 'canvas': None,
            'date_start': None, 'date_end': None,
        }

        if show_freshness:
            fresh_dot = tk.Label(header, text="●", font=('Courier', 9),
                                 fg=TEXT_SECONDARY, bg=bg)
            fresh_dot.pack(side='right', padx=(0, 3))
            fresh_lbl = tk.Label(header, text="", font=FONT_TIMESTAMP,
                                 fg=TEXT_SECONDARY, bg=bg)
            fresh_lbl.pack(side='right')
            refs['fresh_dot'] = fresh_dot
            refs['fresh_lbl'] = fresh_lbl

        if HAS_MPL:
            fig = Figure(figsize=(3.2, 1.2), dpi=90)
            fig.patch.set_facecolor(BG_PANEL)
            ax = fig.add_subplot(111)
            ax.set_facecolor(BG_PANEL)
            fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05)

            canvas = FigureCanvasTkAgg(fig, master=block)
            widget = canvas.get_tk_widget()
            widget.configure(bg=BG_PANEL, highlightthickness=0, bd=0)
            widget.pack(fill='x', padx=4)

            date_row = tk.Frame(block, bg=bg)
            date_row.pack(fill='x', padx=8, pady=(0, 4))
            date_start = tk.Label(date_row, text="", font=FONT_TIMESTAMP,
                                  fg=TEXT_SECONDARY, bg=bg)
            date_start.pack(side='left')
            date_end = tk.Label(date_row, text="", font=FONT_TIMESTAMP,
                                fg=TEXT_SECONDARY, bg=bg)
            date_end.pack(side='right')

            refs.update({
                'fig': fig, 'ax': ax, 'canvas': canvas,
                'date_start': date_start, 'date_end': date_end,
            })
        else:
            tk.Label(block, text="[matplotlib no instalado]",
                     font=FONT_TIMESTAMP, fg=WARNING, bg=bg).pack(pady=4)

        return block, refs

    def _make_chart_row(self, tickers):
        """Crea un Frame horizontal con 3 bloques de gráfico."""
        bg = self._bg
        row = tk.Frame(self, bg=bg)
        row.pack(fill='both', expand=True)
        for i in range(3):
            row.grid_columnconfigure(i, weight=1)

        for col, ticker in enumerate(tickers):
            show_fresh = (ticker == 'BTC')
            block, refs = self._make_chart_block(row, ticker, show_freshness=show_fresh)
            block.grid(row=0, column=col, sticky='nsew', padx=(0 if col == 0 else 1, 0))
            self._charts[ticker] = refs

    def _make_alt_row(self, parent, row, col, ticker):
        """Crea una fila de altcoin en la rejilla inferior."""
        bg = self._bg
        cell = tk.Frame(parent, bg=bg)
        cell.grid(row=row, column=col, sticky='nsew', padx=12, pady=5)
        ticker_lbl = tk.Label(cell, text=ticker, font=_F_ALT_TICKER, fg=TEXT_SECONDARY,
                              bg=bg, width=10, anchor='w')
        ticker_lbl.pack(side='left')
        price_lbl = tk.Label(cell, text="--", font=_F_ALT_VALUE,
                             fg=TEXT_PRIMARY, bg=bg)
        price_lbl.pack(side='left', padx=(6, 0))
        eur_lbl = tk.Label(cell, text="", font=_F_ALT_EUR,
                           fg=TEXT_SECONDARY, bg=bg)
        eur_lbl.pack(side='left', padx=(4, 0))
        return ticker_lbl, price_lbl, eur_lbl

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Fila 1: BTC | ETH | ORO
        self._make_chart_row(['BTC', 'ETH', 'ORO'])

        tk.Frame(self, bg=BORDER, height=1).pack(fill='x')

        # Fila 2: S&P500 | PLATA | IBEX35
        self._make_chart_row(['S&P500', 'PLATA', 'IBEX35'])

        tk.Frame(self, bg=BORDER, height=1).pack(fill='x')

        # Fila 3+: rejilla altcoins generada dinamicamente desde config
        self._build_alt_grid()

    def _build_alt_grid(self):
        """Construye la rejilla de altcoins dinamicamente desde cmc_service.symbols."""
        self._alt_symbols = [s for s in self._cmc.symbols if s not in _CHART_CRYPTOS]

        grid = tk.Frame(self, bg=self._bg)
        grid.pack(fill='both', expand=True, padx=4, pady=(6, 4))
        N_COLS = 3
        for c in range(N_COLS):
            grid.grid_columnconfigure(c, weight=1)

        self._alt_refs = {}
        for i, sym in enumerate(self._alt_symbols):
            row = i // N_COLS
            col = i % N_COLS
            ticker_lbl, price_lbl, eur_lbl = self._make_alt_row(grid, row, col, sym)
            self._alt_refs[sym] = (ticker_lbl, price_lbl, eur_lbl)

    # ------------------------------------------------------------------
    # Polling y actualización
    # ------------------------------------------------------------------

    def _poll(self):
        self._update_display()
        self.after(5_000, self._poll)

    def _draw_chart(self, ticker, prices, dates):
        refs = self._charts.get(ticker)
        if refs is None or refs['ax'] is None:
            return
        ax = refs['ax']
        ax.clear()
        ax.set_facecolor(BG_PANEL)
        ax.axis('off')

        if prices and len(prices) > 2:
            x = list(range(len(prices)))
            mn, mx = min(prices), max(prices)
            pad = (mx - mn) * 0.12 if mx != mn else 1.0
            ax.set_ylim(mn - pad, mx + pad)
            ax.plot(x, prices, color=ACCENT_MARKET, linewidth=1.5,
                    solid_capstyle='round', solid_joinstyle='round')
            ax.fill_between(x, prices, mn - pad, alpha=0.15, color=ACCENT_MARKET)
        else:
            ax.axhline(y=0.5, color=TEXT_SECONDARY, linewidth=1, alpha=0.4)
            ax.text(0.5, 0.5, 'Sin datos', transform=ax.transAxes,
                    ha='center', va='center', color=TEXT_SECONDARY, fontsize=9)

        refs['fig'].subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05)
        refs['canvas'].draw_idle()

        if dates and refs['date_start']:
            refs['date_start'].config(text=dates[0] or "")
            refs['date_end'].config(text=dates[1] or "")

    def _set_price(self, ticker, price_text, change_pct=None):
        refs = self._charts.get(ticker)
        if refs is None:
            return
        refs['price'].config(text=price_text, fg=TEXT_PRIMARY if price_text != "--" else ERROR)
        if change_pct is not None:
            sign = "▲" if change_pct >= 0 else "▼"
            color = POSITIVE if change_pct >= 0 else NEGATIVE
            refs['change'].config(text=f"{sign}{abs(change_pct):.2f}%", fg=color)
        else:
            refs['change'].config(text="")

    def _update_coin(self, price_lbl, eur_lbl, price_val, eurusd, decimals=2,
                     rank=None, ticker_lbl=None, ticker=""):
        if ticker_lbl is not None:
            prefix = f"#{rank} " if rank else ""
            ticker_lbl.config(text=f"{prefix}{ticker}")
        if price_val is not None:
            price_lbl.config(text=fmt_usd(price_val, decimals), fg=TEXT_PRIMARY)
            eur = usd_to_eur(price_val, eurusd)
            eur_lbl.config(text=f"({fmt_eur(eur, decimals)})" if eur else "")
        else:
            price_lbl.config(text="--", fg=TEXT_SECONDARY)
            eur_lbl.config(text="")

    def _update_display(self):
        cmc    = self._cmc.get_data()
        market = self._market.get_data()
        eurusd = market.get('eurusd_rate')

        # --- BTC ---
        btc_rank = cmc.get('btc_rank')
        refs_btc = self._charts['BTC']
        if btc_rank and 'ticker_lbl' in refs_btc:
            refs_btc['ticker_lbl'].config(text=f"#{btc_rank} BTC")
        btc_price = cmc.get('btc_price')
        if btc_price is not None:
            self._set_price('BTC', fmt_usd(btc_price), cmc.get('btc_change_24h'))
        else:
            self._set_price('BTC', "--")
        self._draw_chart('BTC', market.get('btc_history'), market.get('btc_history_dates'))

        # Frescura BTC
        ts = cmc.get('timestamp')
        refs_btc = self._charts['BTC']
        if 'fresh_dot' in refs_btc:
            refs_btc['fresh_dot'].config(fg=freshness_color(ts, 300))
        if 'fresh_lbl' in refs_btc and ts:
            refs_btc['fresh_lbl'].config(text=f"hace {time_ago(ts)}")

        # --- ETH ---
        eth_rank = cmc.get('eth_rank')
        refs_eth = self._charts['ETH']
        if eth_rank and 'ticker_lbl' in refs_eth:
            refs_eth['ticker_lbl'].config(text=f"#{eth_rank} ETH")
        eth_price = cmc.get('eth_price')
        if eth_price is not None:
            self._set_price('ETH', fmt_usd(eth_price), cmc.get('eth_change_24h'))
        else:
            self._set_price('ETH', "--")
        self._draw_chart('ETH', market.get('eth_history'), market.get('eth_history_dates'))

        # --- ORO ---
        gold = market.get('gold_price')
        gold_hist = market.get('gold_history')
        if gold is not None:
            eur = usd_to_eur(gold, eurusd)
            price_str = f"{fmt_gold(gold)}" + (f"  {fmt_eur(eur)}/oz" if eur else "")
            self._set_price('ORO', fmt_gold(gold), _pct_change(gold_hist))
        else:
            self._set_price('ORO', "--")
        self._draw_chart('ORO', gold_hist, market.get('gold_history_dates'))

        # --- S&P500 ---
        sp = market.get('sp500_price')
        sp_hist = market.get('sp500_history')
        if sp is not None:
            status = " cerrado" if not _is_nyse_open() else ""
            self._set_price('S&P500', fmt_sp500(sp) + status, _pct_change(sp_hist))
        else:
            self._set_price('S&P500', "--")
        self._draw_chart('S&P500', sp_hist, market.get('sp500_history_dates'))

        # --- PLATA ---
        silver = market.get('silver_price')
        silver_hist = market.get('silver_history')
        if silver is not None:
            self._set_price('PLATA', fmt_gold(silver), _pct_change(silver_hist))
        else:
            self._set_price('PLATA', "--")
        self._draw_chart('PLATA', silver_hist, market.get('silver_history_dates'))

        # --- IBEX35 ---
        ibex = market.get('ibex_price')
        ibex_hist = market.get('ibex_history')
        if ibex is not None:
            self._set_price('IBEX35', fmt_ibex(ibex), _pct_change(ibex_hist))
        else:
            self._set_price('IBEX35', "--")
        self._draw_chart('IBEX35', ibex_hist, market.get('ibex_history_dates'))

        # --- Altcoins (rejilla dinamica) ---
        for sym in self._alt_symbols:
            ticker_lbl, price_lbl, eur_lbl = self._alt_refs[sym]
            key = sym.lower()
            price_val = cmc.get(f'{key}_price')
            self._update_coin(
                price_lbl, eur_lbl, price_val, eurusd,
                decimals=_auto_decimals(price_val),
                rank=cmc.get(f'{key}_rank'),
                ticker_lbl=ticker_lbl, ticker=sym,
            )
