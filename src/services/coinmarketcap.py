import threading
import time
import random
import logging

import requests

logger = logging.getLogger(__name__)

CMC_BASE = "https://pro-api.coinmarketcap.com"

# Datos mockup para entorno 'mockup' (sin llamadas a la API)
_MOCKUP = {
    'BTC':    {'price': 73_000.0,  'change_24h':  1.36, 'rank':   1},
    'ETH':    {'price':  3_480.0,  'change_24h':  2.10, 'rank':   2},
    'BNB':    {'price':    580.0,  'change_24h':  0.55, 'rank':   4},
    'SOL':    {'price':    178.5,  'change_24h': -0.82, 'rank':   5},
    'XRP':    {'price':      0.52, 'change_24h': -1.20, 'rank':   6},
    'DOT':    {'price':      8.20, 'change_24h':  3.20, 'rank':  14},
    'JUP':    {'price':      0.75, 'change_24h':  0.90, 'rank':  55},
    'WIF':    {'price':      2.10, 'change_24h':  1.20, 'rank':  65},
    'ALI':    {'price':      0.018,'change_24h': -2.00, 'rank':  95},
    'STRK':   {'price':      0.38, 'change_24h': -1.30, 'rank': 110},
    'ROSE':   {'price':      0.055,'change_24h':  2.80, 'rank': 150},
    'POPCAT': {'price':      0.42, 'change_24h': -5.10, 'rank': 180},
    'RAIL':   {'price':      1.20, 'change_24h': -0.50, 'rank': 190},
    'GPU':    {'price':      0.095,'change_24h':  7.20, 'rank': 210},
    'AURA':   {'price':      0.0035,'change_24h': 4.50, 'rank': 320},
    'HSUITE': {'price':      0.0082,'change_24h':-3.10, 'rank': 450},
}


class CoinMarketCapService:
    """Obtiene precios y ranking de las cryptos definidas en config.yaml."""

    def __init__(self, api_key, symbols, refresh_interval=300, environment='pro'):
        self.api_key          = api_key
        self.symbols          = [s.upper() for s in symbols]
        self.refresh_interval = max(60, refresh_interval)
        self.environment      = environment
        # Cache generado dinamicamente segun los simbolos configurados
        self._cache = {
            **{f'{s.lower()}_{field}': None
               for s in self.symbols
               for field in ('price', 'change_24h', 'rank')},
            'timestamp': None,
            'error': None,
        }
        self._lock = threading.Lock()

    def get_data(self):
        with self._lock:
            return dict(self._cache)

    # ------------------------------------------------------------------
    # Fetch real (pro / test)
    # ------------------------------------------------------------------

    def _fetch_real(self):
        if not self.api_key:
            with self._lock:
                self._cache['error'] = "API key no configurada"
            return
        try:
            resp = requests.get(
                f"{CMC_BASE}/v1/cryptocurrency/quotes/latest",
                params={
                    'symbol':  ','.join(self.symbols),
                    'convert': 'USD',
                    'aux':     'cmc_rank',
                },
                headers={
                    'X-CMC_PRO_API_KEY': self.api_key,
                    'Accept': 'application/json',
                },
                timeout=10,
            )
            if resp.status_code == 429:
                logger.warning("coinmarketcap: rate limit 429, manteniendo cache")
                return
            resp.raise_for_status()
            data = resp.json()
            updates = {'timestamp': time.time(), 'error': None}
            for sym in self.symbols:
                entry = data['data'].get(sym)
                if entry is None:
                    continue
                if isinstance(entry, list):
                    entry = entry[0]
                try:
                    quote = entry['quote']['USD']
                    updates[f'{sym.lower()}_price']     = quote['price']
                    updates[f'{sym.lower()}_change_24h'] = quote['percent_change_24h']
                    updates[f'{sym.lower()}_rank']       = entry.get('cmc_rank')
                except (KeyError, TypeError) as e:
                    logger.warning(f"coinmarketcap: no se pudo parsear {sym}: {e}")
            with self._lock:
                self._cache.update(updates)
            sample = " | ".join(
                f"{s} ${updates.get(f'{s.lower()}_price', 0):,.2f}"
                for s in self.symbols[:4]
            )
            logger.info(f"coinmarketcap: {sample}")
        except requests.exceptions.Timeout:
            logger.warning("coinmarketcap: timeout >10s, manteniendo cache")
        except Exception as e:
            logger.error(f"coinmarketcap: {e}")
            with self._lock:
                self._cache['error'] = str(e)

    # ------------------------------------------------------------------
    # Fetch mockup
    # ------------------------------------------------------------------

    def _fetch_mockup(self):
        updates = {'timestamp': time.time(), 'error': None}
        for sym in self.symbols:
            base = _MOCKUP.get(sym, {
                'price':      round(random.uniform(0.001, 50), 6),
                'change_24h': round(random.uniform(-10, 10), 2),
                'rank':       random.randint(100, 999),
            })
            jitter = 1 + random.uniform(-0.005, 0.005)
            updates[f'{sym.lower()}_price']     = base['price'] * jitter
            updates[f'{sym.lower()}_change_24h'] = base['change_24h']
            updates[f'{sym.lower()}_rank']       = base['rank']
        with self._lock:
            self._cache.update(updates)
        logger.debug(f"coinmarketcap: mockup actualizado ({len(self.symbols)} simbolos)")

    # ------------------------------------------------------------------
    # Loop
    # ------------------------------------------------------------------

    def _run(self):
        time.sleep(random.randint(0, 15))
        while True:
            if self.environment == 'mockup':
                self._fetch_mockup()
            else:
                self._fetch_real()
            time.sleep(self.refresh_interval)

    def start(self):
        t = threading.Thread(target=self._run, daemon=True, name="svc-cmc")
        t.start()
        logger.info(
            f"coinmarketcap: servicio iniciado — "
            f"{len(self.symbols)} simbolos, "
            f"intervalo {self.refresh_interval}s, "
            f"env={self.environment}"
        )
