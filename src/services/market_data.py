import threading
import time
import random
import logging

logger = logging.getLogger(__name__)


def _extract_history(hist, max_pts=60):
    """Extrae lista de precios y fechas de inicio/fin de un DataFrame de yfinance."""
    prices = [float(p) for p in hist['Close'].dropna().tolist()]
    if len(prices) > max_pts:
        step = max(1, len(prices) // max_pts)
        prices = prices[::step]
    idx = hist.index
    start_date = f"{idx[0].day} {idx[0].strftime('%b')}"
    end_date   = f"{idx[-1].day} {idx[-1].strftime('%b')}"
    return prices, [start_date, end_date]


class MarketDataService:
    """Obtiene historial BTC/ETH 7d y Oro/Plata/S&P500/IBEX35 1mo via yfinance.

    Intervalos configurables en config.yaml:
      refresh.btc_chart  -> BTC + ETH historial         (default 300s  / 5 min)
      refresh.gold       -> Oro + Plata + EUR/USD        (default 1800s / 30 min)
      refresh.sp500      -> S&P500 + IBEX35              (default 1800s / 30 min)
    """

    def __init__(self, interval_btc_chart=300, interval_gold=1800, interval_sp500=1800):
        self._interval_btc  = max(60, interval_btc_chart)
        self._interval_gold = max(60, interval_gold)
        self._interval_sp   = max(60, interval_sp500)
        self._cache = {
            # BTC
            'btc_history': None,
            'btc_history_dates': None,
            'btc_history_timestamp': None,
            # ETH
            'eth_history': None,
            'eth_history_dates': None,
            'eth_history_timestamp': None,
            # Oro
            'gold_price': None,
            'gold_history': None,
            'gold_history_dates': None,
            'gold_timestamp': None,
            # Plata
            'silver_price': None,
            'silver_history': None,
            'silver_history_dates': None,
            'silver_timestamp': None,
            # EUR/USD
            'eurusd_rate': None,
            'eurusd_timestamp': None,
            # S&P500
            'sp500_price': None,
            'sp500_history': None,
            'sp500_history_dates': None,
            'sp500_timestamp': None,
            # IBEX35
            'ibex_price': None,
            'ibex_history': None,
            'ibex_history_dates': None,
            'ibex_timestamp': None,
            'error': None,
        }
        self._lock = threading.Lock()

    def get_data(self):
        with self._lock:
            return dict(self._cache)

    # ------------------------------------------------------------------
    # Fetches
    # ------------------------------------------------------------------

    def _fetch_btc_history(self):
        try:
            import yfinance as yf
            hist = yf.Ticker("BTC-USD").history(period="7d", interval="1h")
            if not hist.empty:
                prices, dates = _extract_history(hist, max_pts=168)
                with self._lock:
                    self._cache['btc_history']           = prices
                    self._cache['btc_history_dates']     = dates
                    self._cache['btc_history_timestamp'] = time.time()
                logger.info(f"market_data: BTC historial ({len(prices)} pts)")
        except ImportError:
            logger.error("market_data: yfinance no instalado")
            with self._lock:
                self._cache['error'] = "yfinance no instalado"
        except Exception as e:
            logger.error(f"market_data: BTC historial error: {e}")

    def _fetch_eth_history(self):
        try:
            import yfinance as yf
            hist = yf.Ticker("ETH-USD").history(period="7d", interval="1h")
            if not hist.empty:
                prices, dates = _extract_history(hist, max_pts=168)
                with self._lock:
                    self._cache['eth_history']           = prices
                    self._cache['eth_history_dates']     = dates
                    self._cache['eth_history_timestamp'] = time.time()
                logger.info(f"market_data: ETH historial ({len(prices)} pts)")
        except Exception as e:
            logger.error(f"market_data: ETH historial error: {e}")

    def _fetch_gold(self):
        try:
            import yfinance as yf
            hist = yf.Ticker("GC=F").history(period="1mo", interval="1d")
            if not hist.empty:
                clean = hist['Close'].dropna()
                price = float(clean.iloc[-1])
                prices, dates = _extract_history(hist)
                with self._lock:
                    self._cache['gold_price']         = price
                    self._cache['gold_history']       = prices
                    self._cache['gold_history_dates'] = dates
                    self._cache['gold_timestamp']     = time.time()
                logger.info(f"market_data: Oro ${price:.2f}/oz")
        except Exception as e:
            logger.error(f"market_data: Oro error: {e}")

    def _fetch_silver(self):
        try:
            import yfinance as yf
            hist = yf.Ticker("SI=F").history(period="1mo", interval="1d")
            if not hist.empty:
                clean = hist['Close'].dropna()
                price = float(clean.iloc[-1])
                prices, dates = _extract_history(hist)
                with self._lock:
                    self._cache['silver_price']         = price
                    self._cache['silver_history']       = prices
                    self._cache['silver_history_dates'] = dates
                    self._cache['silver_timestamp']     = time.time()
                logger.info(f"market_data: Plata ${price:.2f}/oz")
        except Exception as e:
            logger.error(f"market_data: Plata error: {e}")

    def _fetch_sp500(self):
        try:
            import yfinance as yf
            hist = yf.Ticker("^GSPC").history(period="1mo", interval="1d")
            if not hist.empty:
                clean = hist['Close'].dropna()
                price = float(clean.iloc[-1])
                prices, dates = _extract_history(hist)
                with self._lock:
                    self._cache['sp500_price']         = price
                    self._cache['sp500_history']       = prices
                    self._cache['sp500_history_dates'] = dates
                    self._cache['sp500_timestamp']     = time.time()
                logger.info(f"market_data: S&P500 {price:.2f} pts")
        except Exception as e:
            logger.error(f"market_data: S&P500 error: {e}")

    def _fetch_ibex(self):
        try:
            import yfinance as yf
            hist = yf.Ticker("^IBEX").history(period="1mo", interval="1d")
            if not hist.empty:
                clean = hist['Close'].dropna()
                price = float(clean.iloc[-1])
                prices, dates = _extract_history(hist)
                with self._lock:
                    self._cache['ibex_price']         = price
                    self._cache['ibex_history']       = prices
                    self._cache['ibex_history_dates'] = dates
                    self._cache['ibex_timestamp']     = time.time()
                logger.info(f"market_data: IBEX35 {price:.2f} pts")
        except Exception as e:
            logger.error(f"market_data: IBEX35 error: {e}")

    def _fetch_eurusd(self):
        try:
            import yfinance as yf
            hist = yf.Ticker("EURUSD=X").history(period="5d")
            if not hist.empty:
                rate = float(hist['Close'].dropna().iloc[-1])
                with self._lock:
                    self._cache['eurusd_rate']      = rate
                    self._cache['eurusd_timestamp'] = time.time()
                logger.info(f"market_data: EUR/USD {rate:.4f}")
        except Exception as e:
            logger.error(f"market_data: EUR/USD error: {e}")

    # ------------------------------------------------------------------
    # Loops de hilos daemon
    # ------------------------------------------------------------------

    def _run_btc(self):
        time.sleep(random.randint(5, 20))
        while True:
            self._fetch_btc_history()
            self._fetch_eth_history()
            time.sleep(self._interval_btc)

    def _run_gold(self):
        time.sleep(random.randint(10, 40))
        while True:
            self._fetch_gold()
            self._fetch_silver()
            self._fetch_eurusd()
            time.sleep(self._interval_gold)

    def _run_sp500(self):
        time.sleep(random.randint(15, 45))
        while True:
            self._fetch_sp500()
            self._fetch_ibex()
            time.sleep(self._interval_sp)

    def start(self):
        threading.Thread(target=self._run_btc,   daemon=True, name="svc-btc-chart").start()
        threading.Thread(target=self._run_gold,  daemon=True, name="svc-gold").start()
        threading.Thread(target=self._run_sp500, daemon=True, name="svc-sp500").start()
        logger.info(
            f"market_data: servicios iniciados — "
            f"BTC+ETH chart {self._interval_btc}s | "
            f"Oro+Plata+EURUSD {self._interval_gold}s | "
            f"S&P500+IBEX35 {self._interval_sp}s"
        )
