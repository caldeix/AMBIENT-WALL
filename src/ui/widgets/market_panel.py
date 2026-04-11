import tkinter as tk
import datetime
import re

from ui.theme import (
    BG_PANEL, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_MARKET, ERROR, WARNING, POSITIVE, NEGATIVE,
    FONT_BTC, FONT_CHANGE, FONT_TIMESTAMP,
)
from utils.formatting import (
    fmt_usd, fmt_gold, fmt_sp500, fmt_ibex,
    fmt_eur, usd_to_eur,
    time_ago, freshness_color,
)
from services.market_data import DEFAULT_CHART_BLOCKS, ticker_key

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

_F_BLOCK_TICKER = ('Helvetica', 11, 'normal')
_F_BLOCK_PRICE  = ('Courier',   18, 'bold')
_F_BLOCK_CHANGE = ('Helvetica', 12, 'normal')
_F_ALT_TICKER   = ('Helvetica', 12, 'normal')
_F_ALT_VALUE    = ('Helvetica', 14, 'normal')
_F_ALT_EUR      = ('Helvetica', 11, 'normal')


# ------------------------------------------------------------------
# Helpers de formato
# ------------------------------------------------------------------

def _auto_decimals(price):
    if price is None or price >= 100:
        return 2
    if price >= 0.01:
        return 4
    return 6


def _pct_change(history):
    if history and len(history) >= 2:
        prev, last = history[-2], history[-1]
        if prev and prev != 0:
            return (last - prev) / prev * 100
    return None


def _format_price(block, price):
    fmt    = block.get('format', '')
    ticker = block.get('ticker', '')
    if not fmt:
        if block.get('cmc_symbol'):
            fmt = 'crypto'
        elif ticker.endswith('=F'):
            fmt = 'commodity'
        elif ticker.startswith('^'):
            fmt = 'index'
        else:
            fmt = 'crypto'
    if fmt == 'commodity':
        return fmt_gold(price)
    if fmt == 'index_int':
        return fmt_ibex(price)
    if fmt == 'index':
        return fmt_sp500(price)
    return fmt_usd(price, _auto_decimals(price))


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
    """Panel principal del dashboard.

    Fila 1–2: bloques con sparkline (de chart_blocks config, hot-reload).
    Fila 3+:  rejilla de altcoins dinámica (hot-reload).
    """

    def __init__(self, parent, cmc_service, market_service,
                 config=None, config_manager=None, **kwargs):
        kwargs.setdefault('bg', BG_PANEL)
        super().__init__(parent, **kwargs)
        self._cmc      = cmc_service
        self._market   = market_service
        self._cfg_mgr  = config_manager
        self._bg       = self.cget('bg')

        cfg = config or {}
        self._chart_blocks = list(cfg.get('chart_blocks', DEFAULT_CHART_BLOCKS))
        self._last_chart_blocks = list(self._chart_blocks)

        self._chart_cmc_syms = self._calc_chart_cmc_syms()
        self._charts           = {}
        self._alt_refs         = {}
        self._last_syms        = []
        self._chart_container  = None
        self._alt_separator    = None
        self._alt_grid_frame   = None

        self._build_chart_container()
        self._build_alt_section()
        self._poll()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _calc_chart_cmc_syms(self):
        return {
            b['cmc_symbol'].upper()
            for b in self._chart_blocks
            if b.get('cmc_symbol')
        }

    # ------------------------------------------------------------------
    # Chart blocks
    # ------------------------------------------------------------------

    def _build_chart_container(self):
        self._chart_container = tk.Frame(self, bg=self._bg)
        self._chart_container.pack(fill='both', expand=False)
        self._build_chart_rows_in(self._chart_container)

    def _rebuild_chart_rows(self):
        """Destruye y reconstruye los bloques de gráfico. Llamado en hot-reload."""
        # Cerrar figuras matplotlib para liberar memoria
        for refs in self._charts.values():
            fig = refs.get('fig')
            if fig:
                try:
                    fig.clf()
                except Exception:
                    pass
        self._charts = {}

        if self._chart_container and self._chart_container.winfo_exists():
            self._chart_container.destroy()

        self._chart_container = tk.Frame(self, bg=self._bg)
        if self._alt_separator and self._alt_separator.winfo_exists():
            self._chart_container.pack(fill='both', expand=False,
                                       before=self._alt_separator)
        else:
            self._chart_container.pack(fill='both', expand=False)

        self._build_chart_rows_in(self._chart_container)

    def _build_chart_rows_in(self, container):
        blocks = self._chart_blocks
        for row_idx in range(0, min(len(blocks), 6), 3):
            row_blocks = blocks[row_idx:row_idx + 3]
            row_frame  = tk.Frame(container, bg=self._bg)
            row_frame.pack(fill='both', expand=True)
            for c in range(3):
                row_frame.grid_columnconfigure(c, weight=1, uniform='chart_cols')
            for col, block in enumerate(row_blocks):
                blk_frame, refs = self._make_chart_block(row_frame, block)
                blk_frame.grid(row=0, column=col, sticky='nsew',
                               padx=(0 if col == 0 else 1, 0))
                self._charts[block['ticker']] = refs
            if row_idx + 3 < min(len(blocks), 6):
                tk.Frame(container, bg=BORDER, height=1).pack(fill='x')

    def _make_chart_block(self, parent, block):
        bg    = self._bg
        label = block.get('label', block['ticker'])
        frame = tk.Frame(parent, bg=bg,
                         highlightbackground=BORDER, highlightthickness=1)

        header = tk.Frame(frame, bg=bg)
        header.pack(fill='x', padx=8, pady=(6, 2))

        ticker_lbl = tk.Label(header, text=label, font=_F_BLOCK_TICKER,
                              fg=TEXT_SECONDARY, bg=bg)
        ticker_lbl.pack(side='left', padx=(0, 8))

        price_lbl = tk.Label(header, text="--", font=_F_BLOCK_PRICE,
                             fg=TEXT_PRIMARY, bg=bg)
        price_lbl.pack(side='left')

        change_lbl = tk.Label(header, text="", font=_F_BLOCK_CHANGE,
                              fg=TEXT_SECONDARY, bg=bg)
        change_lbl.pack(side='left', padx=(8, 0))

        fresh_dot = tk.Label(header, text="●", font=('Courier', 9),
                             fg=TEXT_SECONDARY, bg=bg)
        fresh_dot.pack(side='right', padx=(0, 3))
        fresh_lbl = tk.Label(header, text="", font=FONT_TIMESTAMP,
                             fg=TEXT_SECONDARY, bg=bg)
        fresh_lbl.pack(side='right')

        refs = {
            'ticker_lbl': ticker_lbl, 'price': price_lbl,
            'change': change_lbl, 'fresh_dot': fresh_dot, 'fresh_lbl': fresh_lbl,
            'fig': None, 'ax': None, 'canvas': None,
            'date_start': None, 'date_end': None,
        }

        if HAS_MPL:
            fig = Figure(figsize=(3.2, 1.2), dpi=90)
            fig.patch.set_facecolor(BG_PANEL)
            ax = fig.add_subplot(111)
            ax.set_facecolor(BG_PANEL)
            fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05)
            canvas = FigureCanvasTkAgg(fig, master=frame)
            widget = canvas.get_tk_widget()
            widget.configure(bg=BG_PANEL, highlightthickness=0, bd=0)
            widget.pack(fill='x', padx=4)

            date_row = tk.Frame(frame, bg=bg)
            date_row.pack(fill='x', padx=8, pady=(0, 4))
            date_start = tk.Label(date_row, text="", font=FONT_TIMESTAMP,
                                  fg=TEXT_SECONDARY, bg=bg)
            date_start.pack(side='left')
            date_end = tk.Label(date_row, text="", font=FONT_TIMESTAMP,
                                fg=TEXT_SECONDARY, bg=bg)
            date_end.pack(side='right')
            refs.update({'fig': fig, 'ax': ax, 'canvas': canvas,
                         'date_start': date_start, 'date_end': date_end})
        else:
            tk.Label(frame, text="[matplotlib no instalado]",
                     font=FONT_TIMESTAMP, fg=WARNING, bg=bg).pack(pady=4)

        return frame, refs

    # ------------------------------------------------------------------
    # Rejilla altcoins (hot-reload)
    # ------------------------------------------------------------------

    def _build_alt_section(self):
        if self._alt_separator and self._alt_separator.winfo_exists():
            self._alt_separator.destroy()
        if self._alt_grid_frame and self._alt_grid_frame.winfo_exists():
            self._alt_grid_frame.destroy()

        self._alt_symbols = [
            s for s in self._cmc.symbols
            if s.upper() not in self._chart_cmc_syms
        ]
        self._last_syms = list(self._cmc.symbols)

        self._alt_separator = tk.Frame(self, bg=BORDER, height=1)
        self._alt_separator.pack(fill='x')

        self._alt_grid_frame = tk.Frame(self, bg=self._bg)
        self._alt_grid_frame.pack(fill='both', expand=True, padx=4, pady=(6, 4))

        N_COLS = 3
        for c in range(N_COLS):
            self._alt_grid_frame.grid_columnconfigure(c, weight=1)

        self._alt_refs = {}
        for i, sym in enumerate(self._alt_symbols):
            row = i // N_COLS
            col = i % N_COLS
            cell = tk.Frame(self._alt_grid_frame, bg=self._bg)
            cell.grid(row=row, column=col, sticky='nsew', padx=12, pady=5)
            ticker_lbl = tk.Label(cell, text=sym, font=_F_ALT_TICKER,
                                  fg=TEXT_SECONDARY, bg=self._bg, width=10, anchor='w')
            ticker_lbl.pack(side='left')
            price_lbl = tk.Label(cell, text="--", font=_F_ALT_VALUE,
                                 fg=TEXT_PRIMARY, bg=self._bg)
            price_lbl.pack(side='left', padx=(6, 0))
            eur_lbl = tk.Label(cell, text="", font=_F_ALT_EUR,
                               fg=TEXT_SECONDARY, bg=self._bg)
            eur_lbl.pack(side='left', padx=(4, 0))
            self._alt_refs[sym] = (ticker_lbl, price_lbl, eur_lbl)

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def _poll(self):
        # Hot-reload: chart blocks (desde config_manager)
        if self._cfg_mgr:
            new_blocks = self._cfg_mgr.get_chart_blocks()
            if new_blocks != self._last_chart_blocks:
                self._chart_blocks      = new_blocks
                self._last_chart_blocks = list(new_blocks)
                self._chart_cmc_syms    = self._calc_chart_cmc_syms()
                self._rebuild_chart_rows()

        # Hot-reload: rejilla altcoins
        current_syms = list(self._cmc.symbols)
        if current_syms != self._last_syms:
            self._build_alt_section()

        self._update_display()
        self.after(5_000, self._poll)

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

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
        refs['price'].config(
            text=price_text,
            fg=TEXT_PRIMARY if price_text not in ("--", "—") else ERROR,
        )
        if change_pct is not None:
            sign  = "▲" if change_pct >= 0 else "▼"
            color = POSITIVE if change_pct >= 0 else NEGATIVE
            refs['change'].config(text=f"{sign}{abs(change_pct):.2f}%", fg=color)
        else:
            refs['change'].config(text="")

    def _update_freshness(self, ticker, ts, interval):
        refs = self._charts.get(ticker)
        if refs is None:
            return
        refs['fresh_dot'].config(fg=freshness_color(ts, interval))
        if ts:
            refs['fresh_lbl'].config(text=f"hace {time_ago(ts)}")

    def _update_display(self):
        cmc    = self._cmc.get_data()
        market = self._market.get_data()
        eurusd = market.get('eurusd_rate')

        # --- Bloques de gráfico ---
        for block in self._chart_blocks:
            t       = block['ticker']
            cmc_sym = block.get('cmc_symbol')
            tkey    = ticker_key(t)
            label   = block.get('label', t)

            if cmc_sym:
                key      = cmc_sym.lower()
                price    = cmc.get(f'{key}_price')
                change   = cmc.get(f'{key}_change_24h')
                rank     = cmc.get(f'{key}_rank')
                ts       = cmc.get('timestamp')
                interval = 300
            else:
                price    = market.get(f'{tkey}_price')
                hist_    = market.get(f'{tkey}_history')
                change   = _pct_change(hist_)
                rank     = None
                ts       = market.get(f'{tkey}_timestamp')
                interval = 1800

            refs = self._charts.get(t)
            if refs:
                refs['ticker_lbl'].config(text=f"#{rank} {label}" if rank else label)

            if price is not None:
                price_str = _format_price(block, price)
                if block.get('format') == 'index' and not _is_nyse_open():
                    price_str += " cerrado"
                self._set_price(t, price_str, change)
            else:
                self._set_price(t, "--")

            self._draw_chart(t, market.get(f'{tkey}_history'), market.get(f'{tkey}_history_dates'))
            self._update_freshness(t, ts, interval)

        # --- Rejilla altcoins ---
        for sym in self._alt_symbols:
            if sym not in self._alt_refs:
                continue
            ticker_lbl, price_lbl, eur_lbl = self._alt_refs[sym]
            key       = sym.lower()
            price_val = cmc.get(f'{key}_price')
            rank      = cmc.get(f'{key}_rank')
            ticker_lbl.config(text=f"#{rank} {sym}" if rank else sym)
            if price_val is not None:
                decimals = _auto_decimals(price_val)
                price_lbl.config(text=fmt_usd(price_val, decimals), fg=TEXT_PRIMARY)
                eur = usd_to_eur(price_val, eurusd)
                eur_lbl.config(text=f"({fmt_eur(eur, decimals)})" if eur else "")
            else:
                price_lbl.config(text="--", fg=TEXT_SECONDARY)
                eur_lbl.config(text="")
