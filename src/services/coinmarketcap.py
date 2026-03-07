import threading
import time
import random
import logging

import requests

logger = logging.getLogger(__name__)

CMC_BASE = "https://pro-api.coinmarketcap.com"


class CoinMarketCapService:
    """Obtiene precios de BTC, ETH, SOL, XRP, DOT, POPCAT, WIF, ALI y AURA en una sola llamada."""

    SYMBOLS = ['BTC', 'ETH', 'SOL', 'XRP', 'DOT', 'POPCAT', 'WIF', 'ALI', 'AURA']

    def __init__(self, api_key, refresh_interval=300):
        self.api_key = api_key
        self.refresh_interval = max(60, refresh_interval)
        self._cache = {
            'btc_price': None, 'btc_change_24h': None,
            'eth_price': None, 'eth_change_24h': None,
            'sol_price': None, 'sol_change_24h': None,
            'xrp_price': None, 'xrp_change_24h': None,
            'dot_price': None, 'dot_change_24h': None,
            'popcat_price': None, 'popcat_change_24h': None,
            'wif_price': None, 'wif_change_24h': None,
            'ali_price': None, 'ali_change_24h': None,
            'aura_price': None, 'aura_change_24h': None,
            'timestamp': None,
            'is_stale': True,
            'error': None,
            'consecutive_failures': 0,
        }
        self._lock = threading.Lock()

    def get_data(self):
        with self._lock:
            return dict(self._cache)

    def _fetch(self):
        if not self.api_key:
            with self._lock:
                self._cache['error'] = "API key no configurada"
                self._cache['is_stale'] = True
            return
        try:
            headers = {
                'X-CMC_PRO_API_KEY': self.api_key,
                'Accept': 'application/json',
            }
            resp = requests.get(
                f"{CMC_BASE}/v1/cryptocurrency/quotes/latest",
                params={'symbol': ','.join(self.SYMBOLS), 'convert': 'USD'},
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 429:
                logger.warning("coinmarketcap: rate limit 429, manteniendo cache")
                with self._lock:
                    self._cache['is_stale'] = True
                return
            resp.raise_for_status()
            data = resp.json()
            updates = {
                'timestamp': time.time(),
                'is_stale': False,
                'error': None,
                'consecutive_failures': 0,
            }
            for sym in self.SYMBOLS:
                entry = data['data'].get(sym)
                if entry is None:
                    continue
                # CMC devuelve array si hay varios tokens con el mismo simbolo
                if isinstance(entry, list):
                    entry = entry[0]
                try:
                    quote = entry['quote']['USD']
                    updates[f'{sym.lower()}_price']     = quote['price']
                    updates[f'{sym.lower()}_change_24h'] = quote['percent_change_24h']
                except (KeyError, TypeError) as e:
                    logger.warning(f"coinmarketcap: no se pudo parsear {sym}: {e}")
            with self._lock:
                self._cache.update(updates)
            logger.info(
                f"coinmarketcap: BTC ${updates.get('btc_price', 0):,.0f} | "
                f"ETH ${updates.get('eth_price', 0):,.0f} | "
                f"SOL ${updates.get('sol_price', 0):.1f} | "
                f"XRP ${updates.get('xrp_price', 0):.4f} | "
                f"DOT ${updates.get('dot_price', 0):.2f} | "
                f"WIF ${updates.get('wif_price', 0):.3f}"
            )
        except requests.exceptions.Timeout:
            logger.warning("coinmarketcap: timeout >10s, manteniendo cache")
            with self._lock:
                self._cache['is_stale'] = True
                self._cache['consecutive_failures'] += 1
        except Exception as e:
            logger.error(f"coinmarketcap: {e}")
            with self._lock:
                self._cache['is_stale'] = True
                self._cache['error'] = str(e)
                self._cache['consecutive_failures'] += 1

    def _run(self):
        # Jitter inicial para no sincronizar peticiones al arrancar
        time.sleep(random.randint(0, 15))
        while True:
            self._fetch()
            time.sleep(self.refresh_interval)

    def start(self):
        t = threading.Thread(target=self._run, daemon=True, name="svc-cmc")
        t.start()
        logger.info(f"coinmarketcap: servicio iniciado (intervalo {self.refresh_interval}s)")
