import threading
import time
import random
import logging

logger = logging.getLogger(__name__)


class MarketDataService:
    """Obtiene historial BTC 7d, Oro, Plata, S&P500, IBEX35 y EUR/USD via yfinance.

    Intervalos configurables en config.yaml:
      refresh.btc_chart  -> historial BTC para sparkline  (default 300s  / 5 min)
      refresh.gold       -> Oro + Plata + EUR/USD          (default 1800s / 30 min)
      refresh.sp500      -> S&P500 + IBEX35                (default 1800s / 30 min)
    """

    def __init__(self, interval_btc_chart=300, interval_gold=1800, interval_sp500=1800):
        self._interval_btc  = max(60, interval_btc_chart)
        self._interval_gold = max(60, interval_gold)
        self._interval_sp   = max(60, interval_sp500)
        self._cache = {
            'gold_price': None,
            'gold_timestamp': None,
            'silver_price': None,
            'silver_timestamp': None,
            'sp500_price': None,
            'sp500_timestamp': None,
            'ibex_price': None,
            'ibex_timestamp': None,
            'eurusd_rate': None,
            'eurusd_timestamp': None,
            'btc_history': None,        # lista de precios float
            'btc_history_dates': None,  # [str_inicio, str_fin]
            'btc_history_timestamp': None,
            'error': None,
        }
        self._lock = threading.Lock()

    def get_data(self):
        with self._lock:
            return dict(self._cache)

    # ------------------------------------------------------------------
    # Fetches independientes por dato
    # ------------------------------------------------------------------

    def _fetch_btc_history(self):
        try:
            import yfinance as yf
            btc = yf.Ticker("BTC-USD")
            hist = btc.history(period="7d", interval="1h")
            if not hist.empty:
                prices = [float(p) for p in hist['Close'].dropna().tolist()]
                if len(prices) > 168:
                    step = max(1, len(prices) // 168)
                    prices = prices[::step]
                idx = hist.index
                start_date = f"{idx[0].day} {idx[0].strftime('%b')}"
                end_date   = f"{idx[-1].day} {idx[-1].strftime('%b')}"
                with self._lock:
                    self._cache['btc_history']           = prices
                    self._cache['btc_history_dates']     = [start_date, end_date]
                    self._cache['btc_history_timestamp'] = time.time()
                logger.info(f"market_data: BTC historial actualizado ({len(prices)} puntos)")
        except ImportError:
            logger.error("market_data: yfinance no instalado. Ejecuta: pip install yfinance")
            with self._lock:
                self._cache['error'] = "yfinance no instalado"
        except Exception as e:
            logger.error(f"market_data: BTC historial error: {e}")

    def _fetch_gold(self):
        try:
            import yfinance as yf
            gold = yf.Ticker("GC=F")
            hist = gold.history(period="5d")
            if not hist.empty:
                price = float(hist['Close'].dropna().iloc[-1])
                with self._lock:
                    self._cache['gold_price']     = price
                    self._cache['gold_timestamp'] = time.time()
                logger.info(f"market_data: Oro ${price:.2f}/oz")
        except Exception as e:
            logger.error(f"market_data: Oro error: {e}")

    def _fetch_sp500(self):
        try:
            import yfinance as yf
            sp = yf.Ticker("^GSPC")
            hist = sp.history(period="5d")
            if not hist.empty:
                price = float(hist['Close'].dropna().iloc[-1])
                with self._lock:
                    self._cache['sp500_price']     = price
                    self._cache['sp500_timestamp'] = time.time()
                logger.info(f"market_data: S&P500 {price:.2f} pts")
        except Exception as e:
            logger.error(f"market_data: S&P500 error: {e}")

    def _fetch_silver(self):
        try:
            import yfinance as yf
            silver = yf.Ticker("SI=F")
            hist = silver.history(period="5d")
            if not hist.empty:
                price = float(hist['Close'].dropna().iloc[-1])
                with self._lock:
                    self._cache['silver_price']     = price
                    self._cache['silver_timestamp'] = time.time()
                logger.info(f"market_data: Plata ${price:.2f}/oz")
        except Exception as e:
            logger.error(f"market_data: Plata error: {e}")

    def _fetch_ibex(self):
        try:
            import yfinance as yf
            ibex = yf.Ticker("^IBEX")
            hist = ibex.history(period="5d")
            if not hist.empty:
                price = float(hist['Close'].dropna().iloc[-1])
                with self._lock:
                    self._cache['ibex_price']     = price
                    self._cache['ibex_timestamp'] = time.time()
                logger.info(f"market_data: IBEX35 {price:.2f} pts")
        except Exception as e:
            logger.error(f"market_data: IBEX35 error: {e}")

    def _fetch_eurusd(self):
        try:
            import yfinance as yf
            fx = yf.Ticker("EURUSD=X")
            hist = fx.history(period="5d")
            if not hist.empty:
                rate = float(hist['Close'].dropna().iloc[-1])
                with self._lock:
                    self._cache['eurusd_rate']      = rate
                    self._cache['eurusd_timestamp'] = time.time()
                logger.info(f"market_data: EUR/USD {rate:.4f}")
        except Exception as e:
            logger.error(f"market_data: EUR/USD error: {e}")

    # ------------------------------------------------------------------
    # Loops independientes (un hilo daemon por dato)
    # ------------------------------------------------------------------

    def _run_btc(self):
        time.sleep(random.randint(5, 20))
        while True:
            self._fetch_btc_history()
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
            f"BTC chart {self._interval_btc}s | "
            f"Oro+Plata+EURUSD {self._interval_gold}s | "
            f"S&P500+IBEX35 {self._interval_sp}s"
        )
