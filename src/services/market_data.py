"""
MarketDataService — historial y precios de activos Yahoo Finance.

Los activos a obtener se leen de chart_blocks en config_manager.
Si no hay config_manager, usa los bloques por defecto (backward compat).

Cache keys se generan dinámicamente a partir del ticker:
  'BTC-USD' → 'btc_usd'   '^GSPC' → 'gspc'   'GC=F' → 'gc_f'
"""
import re
import threading
import time
import random
import logging

logger = logging.getLogger(__name__)

# Bloques por defecto si no hay config_manager
DEFAULT_CHART_BLOCKS = [
    {'label': 'BTC',    'ticker': 'BTC-USD', 'period': '7d',  'cmc_symbol': 'BTC',  'format': 'crypto'},
    {'label': 'ETH',    'ticker': 'ETH-USD', 'period': '7d',  'cmc_symbol': 'ETH',  'format': 'crypto'},
    {'label': 'ORO',    'ticker': 'GC=F',    'period': '1mo', 'cmc_symbol': None,    'format': 'commodity'},
    {'label': 'S&P500', 'ticker': '^GSPC',   'period': '1mo', 'cmc_symbol': None,    'format': 'index'},
    {'label': 'PLATA',  'ticker': 'SI=F',    'period': '1mo', 'cmc_symbol': None,    'format': 'commodity'},
    {'label': 'IBEX35', 'ticker': '^IBEX',   'period': '1mo', 'cmc_symbol': None,    'format': 'index_int'},
]

_FX_TICKER = 'EURUSD=X'


def ticker_key(ticker):
    """Convierte ticker a clave de cache segura.
    'BTC-USD' → 'btc_usd'  '^GSPC' → 'gspc'  'GC=F' → 'gc_f'
    """
    return re.sub(r'[^a-z0-9]', '_', ticker.lower()).strip('_')


def _interval_for_period(period):
    return '1h' if period == '7d' else '1d'


def _max_pts_for_period(period):
    return 168 if period == '7d' else 60


def _extract_history(hist, max_pts=60):
    """Extrae lista de precios y etiquetas inicio/fin de un DataFrame yfinance."""
    prices = [float(p) for p in hist['Close'].dropna().tolist()]
    if len(prices) > max_pts:
        step = max(1, len(prices) // max_pts)
        prices = prices[::step]
    idx = hist.index
    start_date = f"{idx[0].day} {idx[0].strftime('%b')}"
    end_date   = f"{idx[-1].day} {idx[-1].strftime('%b')}"
    return prices, [start_date, end_date]


class MarketDataService:
    """Obtiene historial y precios de activos Yahoo Finance.

    Dos threads paralelos:
      svc-charts  — tickers con period='7d'  (historial intradía)
      svc-market  — tickers con period!='7d' + EUR/USD

    Hot-reload: si se pasa config_manager, re-lee chart_blocks en cada
    ciclo y ajusta los fetches sin reiniciar la app.
    """

    def __init__(self, interval_charts=300, interval_market=1800, config_manager=None):
        self._interval_charts = max(60, interval_charts)
        self._interval_market = max(60, interval_market)
        self._cfg_mgr         = config_manager
        # Dos eventos independientes, uno por thread
        if config_manager:
            self._reload_ev_charts = config_manager.register_listener()
            self._reload_ev_market = config_manager.register_listener()
        else:
            self._reload_ev_charts = None
            self._reload_ev_market = None

        self._cache = {
            'eurusd_rate':      None,
            'eurusd_timestamp': None,
            'error':            None,
        }
        self._lock = threading.Lock()

        # Inicializar entradas de cache para los bloques iniciales
        initial_blocks = (
            config_manager.get_chart_blocks() if config_manager else DEFAULT_CHART_BLOCKS
        )
        self._ensure_cache_keys(initial_blocks)

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _ensure_cache_keys(self, blocks):
        """Añade entradas de cache para bloques nuevos (no borra los existentes)."""
        with self._lock:
            for block in blocks:
                key = ticker_key(block['ticker'])
                for suffix in ('price', 'history', 'history_dates', 'timestamp'):
                    self._cache.setdefault(f'{key}_{suffix}', None)

    def get_data(self):
        with self._lock:
            return dict(self._cache)

    # ------------------------------------------------------------------
    # Fetches
    # ------------------------------------------------------------------

    def _fetch_ticker(self, t, period):
        """Descarga historial y precio actual de cualquier ticker Yahoo Finance."""
        try:
            import yfinance as yf
            interval = _interval_for_period(period)
            max_pts  = _max_pts_for_period(period)
            hist = yf.Ticker(t).history(period=period, interval=interval)
            if hist.empty:
                logger.warning(f"market_data: {t} → historial vacío")
                return
            clean  = hist['Close'].dropna()
            price  = float(clean.iloc[-1])
            prices, dates = _extract_history(hist, max_pts=max_pts)
            key = ticker_key(t)
            with self._lock:
                self._cache[f'{key}_price']         = price
                self._cache[f'{key}_history']       = prices
                self._cache[f'{key}_history_dates'] = dates
                self._cache[f'{key}_timestamp']     = time.time()
            logger.info(f"market_data: {t} {price:.4g} ({len(prices)} pts)")
        except ImportError:
            logger.error("market_data: yfinance no instalado")
            with self._lock:
                self._cache['error'] = "yfinance no instalado"
        except Exception as e:
            logger.error(f"market_data: {t} error: {e}")

    def _fetch_eurusd(self):
        try:
            import yfinance as yf
            hist = yf.Ticker(_FX_TICKER).history(period="5d")
            if not hist.empty:
                rate = float(hist['Close'].dropna().iloc[-1])
                with self._lock:
                    self._cache['eurusd_rate']      = rate
                    self._cache['eurusd_timestamp'] = time.time()
                logger.info(f"market_data: EUR/USD {rate:.4f}")
        except Exception as e:
            logger.error(f"market_data: EUR/USD error: {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current_blocks(self):
        if self._cfg_mgr:
            return self._cfg_mgr.get_chart_blocks()
        return DEFAULT_CHART_BLOCKS

    def _interruptible_wait(self, reload_ev, seconds):
        if reload_ev:
            woken = reload_ev.wait(timeout=seconds)
            if woken:
                reload_ev.clear()
        else:
            time.sleep(seconds)

    # ------------------------------------------------------------------
    # Threads
    # ------------------------------------------------------------------

    def _run_charts(self):
        time.sleep(random.randint(5, 20))
        while True:
            blocks = self._current_blocks()
            self._ensure_cache_keys(blocks)
            for block in blocks:
                if block.get('period', '1mo') == '7d':
                    self._fetch_ticker(block['ticker'], '7d')
            self._interruptible_wait(self._reload_ev_charts, self._interval_charts)

    def _run_market(self):
        time.sleep(random.randint(10, 40))
        while True:
            blocks = self._current_blocks()
            self._ensure_cache_keys(blocks)
            self._fetch_eurusd()
            for block in blocks:
                if block.get('period', '1mo') != '7d':
                    self._fetch_ticker(block['ticker'], block.get('period', '1mo'))
            self._interruptible_wait(self._reload_ev_market, self._interval_market)

    def start(self):
        threading.Thread(target=self._run_charts, daemon=True, name="svc-charts").start()
        threading.Thread(target=self._run_market, daemon=True, name="svc-market").start()
        logger.info(
            f"market_data: servicios iniciados — "
            f"charts {self._interval_charts}s | "
            f"market {self._interval_market}s"
        )
