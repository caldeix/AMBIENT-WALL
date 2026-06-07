import tkinter as tk
import datetime
import re

from ui.theme import (
    BG_PANEL, BG_PANEL_CRYPTO, BG_PANEL_COMMODITY, BG_PANEL_INDEX,
    BG_ALT_ROW_ODD, BG_ALT_ROW_EVEN, BG_CHANGE_UP, BG_CHANGE_DOWN,
    BORDER, SEP_BRIGHT, SEP_DARK,
    TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_MARKET, ACCENT_CRYPTO, ACCENT_COMMODITY, ACCENT_INDEX,
    STRIPE_CRYPTO, STRIPE_COMMODITY, STRIPE_INDEX,
    RANK_GOLD_BG, RANK_GOLD_FG, RANK_SILVER_BG, RANK_SILVER_FG,
    RANK_OTHER_BG, RANK_OTHER_FG,
    POSITIVE, NEGATIVE, ERROR, WARNING,
    FONT_BLOCK_TICKER, FONT_BLOCK_PRICE, FONT_BLOCK_CHANGE, FONT_BLOCK_EUR,
    FONT_RANK_BADGE,
    FONT_ALT_TICKER, FONT_ALT_VALUE, FONT_ALT_EUR, FONT_ALT_CHANGE,
    FONT_TIMESTAMP,
)
from utils.formatting import (
    fmt_usd, fmt_gold, fmt_sp500, fmt_ibex,
    fmt_eur, usd_to_eur,
    time_ago, freshness_color,
)
from services.market_data import DEFAULT_CHART_BLOCKS, ticker_key
from ui.widgets.notif_banner import NotifBanner

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.patches as mpatches
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


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


# ------------------------------------------------------------------
# Helpers de diseño por tipo de activo
# ------------------------------------------------------------------

def _block_type(block):
    """Devuelve 'crypto', 'commodity' o 'index' según la config del bloque."""
    fmt = block.get('format', '')
    if not fmt:
        if block.get('cmc_symbol'):
            return 'crypto'
        t = block.get('ticker', '')
        if t.endswith('=F'):
            return 'commodity'
        if t.startswith('^'):
            return 'index'
        return 'crypto'
    if fmt == 'commodity':
        return 'commodity'
    if fmt in ('index', 'index_int'):
        return 'index'
    return 'crypto'


def _block_accent_colors(btype):
    """Devuelve (stripe_color, accent_color, bg_color) según tipo de bloque."""
    if btype == 'commodity':
        return STRIPE_COMMODITY, ACCENT_COMMODITY, BG_PANEL_COMMODITY
    if btype == 'index':
        return STRIPE_INDEX, ACCENT_INDEX, BG_PANEL_INDEX
    return STRIPE_CRYPTO, ACCENT_CRYPTO, BG_PANEL_CRYPTO


def _rank_badge_colors(rank):
    """Devuelve (bg, fg) del rank pill — color uniforme sin distinción por posición."""
    return RANK_OTHER_BG, RANK_OTHER_FG


def _tint_for_change(change, neutral_bg):
    """Devuelve el color de fondo según dirección del precio. None → neutral."""
    if change is None:
        return neutral_bg
    return BG_CHANGE_UP if change > 0 else BG_CHANGE_DOWN


def _apply_block_tint(refs, bg):
    """Actualiza el bg de todos los widgets del bloque excepto el rank pill y matplotlib."""
    for key in ('ticker_lbl', 'price', 'change', 'fresh_dot', 'fresh_lbl',
                'eur_lbl', 'date_start', 'date_end'):
        w = refs.get(key)
        if w:
            try:
                w.config(bg=bg)
            except tk.TclError:
                pass
    for key in ('content_frame', 'header_frame', 'eur_row_frame', 'date_row_frame'):
        w = refs.get(key)
        if w and w.winfo_exists():
            try:
                w.config(bg=bg)
            except tk.TclError:
                pass


class MarketPanel(tk.Frame):
    """Panel principal del dashboard.

    Fila 1-2: bloques con sparkline (de chart_blocks config, hot-reload).
    Fila 3+:  rejilla de altcoins dinamica (hot-reload).
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
        self._alt_separator2   = None
        self._alt_grid_frame   = None

        self._prev_prices    = {}   # {sym: float} para detección de spikes
        self._active_banners = []   # NotifBanner activos en pantalla

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
        """Destruye y reconstruye los bloques de grafico. Llamado en hot-reload."""
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
        btype              = _block_type(block)
        stripe_c, accent_c, bg = _block_accent_colors(btype)
        # Evolución 2: color de franja configurable por bloque
        custom_color = block.get('color')
        if custom_color:
            stripe_c = custom_color
            accent_c = custom_color
        label              = block.get('label', block['ticker'])

        # Marco exterior
        frame = tk.Frame(parent, bg=bg,
                         highlightbackground=BORDER, highlightthickness=1)

        # Stripe de color a la izquierda (4px)
        stripe_frame = tk.Frame(frame, bg=stripe_c, width=4)
        stripe_frame.pack(side='left', fill='y')

        # Contenido a la derecha del stripe
        content = tk.Frame(frame, bg=bg)
        content.pack(side='left', fill='both', expand=True)

        # Fila de cabecera
        header = tk.Frame(content, bg=bg)
        header.pack(fill='x', padx=(6, 8), pady=(5, 2))

        # Rank pill (inicialmente sin pack; se muestra en _update_display)
        rank_pill = tk.Label(header, text='', font=FONT_RANK_BADGE,
                             bg=RANK_OTHER_BG, fg=RANK_OTHER_FG,
                             padx=5, pady=1)

        ticker_lbl = tk.Label(header, text=label, font=FONT_BLOCK_TICKER,
                              fg=TEXT_SECONDARY, bg=bg)
        ticker_lbl.pack(side='left', padx=(0, 6))

        price_lbl = tk.Label(header, text="--", font=FONT_BLOCK_PRICE,
                             fg=TEXT_PRIMARY, bg=bg)
        price_lbl.pack(side='left')

        change_lbl = tk.Label(header, text="", font=FONT_BLOCK_CHANGE,
                              fg=TEXT_SECONDARY, bg=bg)
        change_lbl.pack(side='left', padx=(6, 0))

        fresh_dot = tk.Label(header, text="●", font=('Courier', 8),
                             fg=TEXT_SECONDARY, bg=bg)
        fresh_dot.pack(side='right', padx=(0, 2))
        fresh_lbl = tk.Label(header, text="", font=FONT_TIMESTAMP,
                             fg=TEXT_SECONDARY, bg=bg)
        fresh_lbl.pack(side='right')

        # Fila de precio en EUR (debajo del header principal, solo para cryptos)
        eur_row = tk.Frame(content, bg=bg)
        eur_row.pack(fill='x', padx=(10, 8), pady=(0, 2))
        eur_lbl = tk.Label(eur_row, text="", font=FONT_BLOCK_EUR,
                           fg=TEXT_SECONDARY, bg=bg)
        eur_lbl.pack(side='left')

        refs = {
            'ticker_lbl': ticker_lbl,
            'rank_pill': rank_pill,
            'rank_pill_packed': False,
            'price': price_lbl,
            'change': change_lbl,
            'fresh_dot': fresh_dot,
            'fresh_lbl': fresh_lbl,
            'eur_lbl': eur_lbl,
            'fig': None, 'ax': None, 'canvas': None,
            'date_start': None, 'date_end': None,
            'accent_color': accent_c,
            'bg': bg,
            'stripe_frame': stripe_frame,
            'content_frame': content,
            'header_frame': header,
            'eur_row_frame': eur_row,
        }

        if HAS_MPL:
            fig = Figure(figsize=(3.2, 1.1), dpi=90)
            fig.patch.set_facecolor(bg)
            ax = fig.add_subplot(111)
            ax.set_facecolor(bg)
            fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05)
            canvas = FigureCanvasTkAgg(fig, master=content)
            widget = canvas.get_tk_widget()
            widget.configure(bg=bg, highlightthickness=0, bd=0)
            widget.pack(fill='x', padx=2)

            date_row = tk.Frame(content, bg=bg)
            date_row.pack(fill='x', padx=8, pady=(0, 4))
            date_start = tk.Label(date_row, text="", font=FONT_TIMESTAMP,
                                  fg=TEXT_SECONDARY, bg=bg)
            date_start.pack(side='left')
            date_end = tk.Label(date_row, text="", font=FONT_TIMESTAMP,
                                fg=TEXT_SECONDARY, bg=bg)
            date_end.pack(side='right')
            refs.update({'fig': fig, 'ax': ax, 'canvas': canvas,
                         'date_start': date_start, 'date_end': date_end,
                         'date_row_frame': date_row})
        else:
            tk.Label(content, text="[matplotlib no instalado]",
                     font=FONT_TIMESTAMP, fg=WARNING, bg=bg).pack(pady=4)

        return frame, refs

    # ------------------------------------------------------------------
    # Rejilla altcoins (hot-reload)
    # ------------------------------------------------------------------

    def _build_alt_section(self):
        for sep in (self._alt_separator, self._alt_separator2):
            if sep and sep.winfo_exists():
                sep.destroy()
        if self._alt_grid_frame and self._alt_grid_frame.winfo_exists():
            self._alt_grid_frame.destroy()

        self._alt_symbols = [
            s for s in self._cmc.symbols
            if s.upper() not in self._chart_cmc_syms
        ]
        self._last_syms = list(self._cmc.symbols)

        # Separador doble: linea brillante + linea oscura (efecto glow edge)
        self._alt_separator = tk.Frame(self, bg=SEP_BRIGHT, height=1)
        self._alt_separator.pack(fill='x')
        self._alt_separator2 = tk.Frame(self, bg=SEP_DARK, height=1)
        self._alt_separator2.pack(fill='x')

        self._alt_grid_frame = tk.Frame(self, bg=self._bg)
        self._alt_grid_frame.pack(fill='both', expand=True, padx=4, pady=(6, 4))

        N_COLS = 3
        for c in range(N_COLS):
            self._alt_grid_frame.grid_columnconfigure(c, weight=1)

        self._alt_refs = {}
        for i, sym in enumerate(self._alt_symbols):
            row_idx = i // N_COLS
            col     = i % N_COLS
            row_bg  = BG_ALT_ROW_EVEN if row_idx % 2 == 0 else BG_ALT_ROW_ODD

            cell = tk.Frame(self._alt_grid_frame, bg=row_bg)
            cell.grid(row=row_idx, column=col, sticky='nsew', padx=4, pady=2)

            # Ancho fijo (width=5 chars) para alinear todos los rank badges
            rank_pill = tk.Label(cell, text='', font=FONT_RANK_BADGE,
                                 bg=RANK_OTHER_BG, fg=RANK_OTHER_FG,
                                 width=5, anchor='center', padx=2, pady=1)

            ticker_lbl = tk.Label(cell, text=sym, font=FONT_ALT_TICKER,
                                  fg=TEXT_SECONDARY, bg=row_bg, width=7, anchor='w')
            ticker_lbl.pack(side='left', padx=(6, 0))

            price_lbl = tk.Label(cell, text="--", font=FONT_ALT_VALUE,
                                 fg=TEXT_PRIMARY, bg=row_bg)
            price_lbl.pack(side='left', padx=(6, 0))

            eur_lbl = tk.Label(cell, text="", font=FONT_ALT_EUR,
                               fg=TEXT_SECONDARY, bg=row_bg)
            eur_lbl.pack(side='left', padx=(4, 0))

            change_lbl = tk.Label(cell, text="", font=FONT_ALT_CHANGE,
                                  fg=TEXT_SECONDARY, bg=row_bg)
            change_lbl.pack(side='right', padx=(0, 6))

            self._alt_refs[sym] = (cell, row_bg, rank_pill, ticker_lbl, price_lbl, eur_lbl, change_lbl)

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def _poll(self):
        # Hot-reload: chart blocks
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
    # Dibujo de velas japonesas
    # ------------------------------------------------------------------

    def _draw_candles(self, ax, ohlc, bg, accent):
        """Renderiza velas japonesas en ax dado una lista de tuplas (o, h, l, c)."""
        if not ohlc:
            return
        n          = len(ohlc)
        body_width = 0.6

        all_lows  = [c[2] for c in ohlc]
        all_highs = [c[1] for c in ohlc]
        mn, mx = min(all_lows), max(all_highs)
        price_range = mx - mn
        pad = price_range * 0.08 if price_range > 0 else 1.0
        ax.set_xlim(-0.5, n - 0.5)
        ax.set_ylim(mn - pad, mx + pad)

        doji_threshold = price_range * 0.0015 if price_range > 0 else 1e-9

        for i, (o, h, l, c) in enumerate(ohlc):
            bullish = c >= o
            color   = POSITIVE if bullish else NEGATIVE

            # Mecha: linea vertical de low a high
            ax.plot([i, i], [l, h],
                    color=color, linewidth=0.7, solid_capstyle='butt', zorder=1)

            body_bottom = min(o, c)
            body_height = abs(c - o)

            if body_height < doji_threshold:
                # Doji: dash horizontal
                ax.plot([i - body_width / 2, i + body_width / 2], [c, c],
                        color=color, linewidth=1.0, zorder=2)
            else:
                rect = mpatches.Rectangle(
                    xy=(i - body_width / 2, body_bottom),
                    width=body_width,
                    height=body_height,
                    facecolor=color,
                    edgecolor=color,
                    linewidth=0,
                    zorder=2,
                )
                ax.add_patch(rect)

    # ------------------------------------------------------------------
    # Dibujo del grafico (velas o linea como fallback)
    # ------------------------------------------------------------------

    def _draw_chart(self, ticker, prices, dates, ohlc=None):
        """Dibuja velas japonesas si hay datos OHLC; si no, grafico lineal."""
        refs = self._charts.get(ticker)
        if refs is None or refs['ax'] is None:
            return
        accent = refs.get('accent_color', ACCENT_MARKET)
        bg     = refs.get('bg', BG_PANEL)
        ax = refs['ax']
        ax.clear()
        ax.set_facecolor(bg)
        ax.axis('off')

        if ohlc and len(ohlc) > 2:
            self._draw_candles(ax, ohlc, bg, accent)
        elif prices and len(prices) > 2:
            x = list(range(len(prices)))
            mn, mx = min(prices), max(prices)
            pad = (mx - mn) * 0.12 if mx != mn else 1.0
            ax.set_ylim(mn - pad, mx + pad)
            ax.plot(x, prices, color=accent, linewidth=1.5,
                    solid_capstyle='round', solid_joinstyle='round')
            ax.fill_between(x, prices, mn - pad, alpha=0.18, color=accent)
        else:
            ax.axhline(y=0.5, color=TEXT_SECONDARY, linewidth=1, alpha=0.4)
            ax.text(0.5, 0.5, 'Sin datos', transform=ax.transAxes,
                    ha='center', va='center', color=TEXT_SECONDARY, fontsize=9)

        refs['fig'].subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05)
        refs['canvas'].draw_idle()
        if dates and refs.get('date_start'):
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

        self._check_price_spikes(cmc)

        # --- Bloques de grafico ---
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
                # Tinte de fondo según dirección del precio
                _apply_block_tint(refs, _tint_for_change(change, refs['bg']))

                # Label sin rank (el rank va en el pill dedicado)
                refs['ticker_lbl'].config(text=label)

                # Rank pill
                pill = refs.get('rank_pill')
                if pill:
                    if rank is not None:
                        bg_p, fg_p = _rank_badge_colors(rank)
                        pill.config(text=f"#{rank}", bg=bg_p, fg=fg_p)
                        if not refs.get('rank_pill_packed'):
                            pill.pack(side='left', padx=(0, 5),
                                      before=refs['ticker_lbl'])
                            refs['rank_pill_packed'] = True
                    elif refs.get('rank_pill_packed'):
                        pill.pack_forget()
                        refs['rank_pill_packed'] = False

                # EUR price label (solo cryptos con cmc_symbol)
                eur_lbl = refs.get('eur_lbl')
                if eur_lbl:
                    if cmc_sym and price is not None and eurusd:
                        eur = usd_to_eur(price, eurusd)
                        eur_lbl.config(text=fmt_eur(eur, _auto_decimals(price)))
                    else:
                        eur_lbl.config(text="")

            if price is not None:
                price_str = _format_price(block, price)
                if block.get('format') == 'index' and not _is_nyse_open():
                    price_str += " cerrado"
                self._set_price(t, price_str, change)
            else:
                self._set_price(t, "--")

            self._draw_chart(
                t,
                market.get(f'{tkey}_history'),
                market.get(f'{tkey}_history_dates'),
                ohlc=market.get(f'{tkey}_ohlc'),
            )
            self._update_freshness(t, ts, interval)

        # --- Rejilla altcoins ---
        # Evolución 1: colores personalizados por símbolo desde config
        custom_colors = {}
        if self._cfg_mgr:
            cfg_now = self._cfg_mgr.get()
            custom_colors = cfg_now.get('cryptos', {}).get('colors', {}) if cfg_now else {}

        for sym in self._alt_symbols:
            if sym not in self._alt_refs:
                continue
            cell, row_bg, rank_pill, ticker_lbl, price_lbl, eur_lbl, change_lbl = self._alt_refs[sym]
            key       = sym.lower()
            price_val = cmc.get(f'{key}_price')
            rank      = cmc.get(f'{key}_rank')
            change_24 = cmc.get(f'{key}_change_24h')

            # Tinte de fondo según dirección del precio
            tint = _tint_for_change(change_24, row_bg)
            try:
                cell.config(bg=tint)
                ticker_lbl.config(bg=tint)
                price_lbl.config(bg=tint)
                eur_lbl.config(bg=tint)
                change_lbl.config(bg=tint)
            except tk.TclError:
                pass

            # Ticker sin rank en el texto
            custom_fg = custom_colors.get(sym) or custom_colors.get(sym.upper())
            ticker_lbl.config(text=sym,
                              fg=custom_fg if custom_fg else TEXT_SECONDARY)

            # Rank pill (ancho fijo, badge propio)
            if rank is not None:
                bg_p, fg_p = _rank_badge_colors(rank)
                rank_pill.config(text=f"#{rank}", bg=bg_p,
                                 fg=custom_fg if custom_fg else fg_p)
                try:
                    rank_pill.pack_info()
                except tk.TclError:
                    rank_pill.pack(side='left', padx=(4, 0),
                                   before=ticker_lbl)

            # Precio USD + EUR
            if price_val is not None:
                decimals = _auto_decimals(price_val)
                price_lbl.config(text=fmt_usd(price_val, decimals), fg=TEXT_PRIMARY)
                eur = usd_to_eur(price_val, eurusd)
                eur_lbl.config(text=f"({fmt_eur(eur, decimals)})" if eur else "")
            else:
                price_lbl.config(text="--", fg=TEXT_SECONDARY)
                eur_lbl.config(text="")

            # Cambio 24h
            if change_24 is not None:
                sign  = "▲" if change_24 >= 0 else "▼"
                color = POSITIVE if change_24 >= 0 else NEGATIVE
                change_lbl.config(text=f"{sign}{abs(change_24):.1f}%", fg=color)
            else:
                change_lbl.config(text="")

    # ------------------------------------------------------------------
    # Evolución 3 — Sistema de notificaciones flotantes
    # ------------------------------------------------------------------

    def _check_price_spikes(self, cmc_data):
        """Detecta movimientos bruscos entre ciclos CMC y dispara banners."""
        if not self._cfg_mgr:
            return
        cfg = self._cfg_mgr.get() or {}
        notif_cfg = cfg.get('notifications', {})
        if not notif_cfg.get('enabled', True):
            return

        spike_threshold = float(notif_cfg.get('spike_pct', 3.0))
        duration_s      = int(notif_cfg.get('duration_s', 10))

        # Todos los símbolos CMC visibles: chart blocks + altcoins
        monitored = set()
        for b in self._chart_blocks:
            sym = b.get('cmc_symbol')
            if sym:
                monitored.add(sym.upper())
        for sym in self._alt_symbols:
            monitored.add(sym.upper())

        for sym in monitored:
            key   = sym.lower()
            price = cmc_data.get(f'{key}_price')
            if price is None:
                continue

            prev = self._prev_prices.get(sym)
            if prev is not None and prev != price:
                spike_pct = (price - prev) / prev * 100
                if abs(spike_pct) >= spike_threshold:
                    change_24  = cmc_data.get(f'{key}_change_24h')
                    price_str  = fmt_usd(price, _auto_decimals(price))
                    self._show_notification(sym, spike_pct, change_24, price_str, duration_s)

            self._prev_prices[sym] = price

    def _show_notification(self, sym, spike_pct, change_24h, price_str, duration_s=10):
        """Crea un NotifBanner y lo posiciona en top-center de la ventana raíz."""
        root = self.winfo_toplevel()

        def on_dismiss(banner):
            if banner in self._active_banners:
                self._active_banners.remove(banner)
            self._reposition_banners()

        banner = NotifBanner(
            root, sym, spike_pct, change_24h, price_str,
            on_dismiss=on_dismiss,
            duration_s=duration_s,
        )
        self._active_banners.append(banner)
        self._reposition_banners()

    def _reposition_banners(self):
        """Reposiciona los banners activos apilados en top-center."""
        BANNER_W = 520
        BANNER_H = 52
        GAP      = 6
        root   = self.winfo_toplevel()
        root_w = root.winfo_width()
        x = max(0, (root_w - BANNER_W) // 2)
        for i, banner in enumerate(self._active_banners):
            y = 8 + i * (BANNER_H + GAP)
            try:
                banner.place(x=x, y=y, width=BANNER_W, height=BANNER_H)
            except tk.TclError:
                pass
