import re
import threading
import time
import random
import logging

import requests

_NON_SGR_RE = re.compile(r'\x1b\[(?![0-9;]*m)[0-9;]*[A-Za-z]')

logger = logging.getLogger(__name__)

WEATHER_DESC = {
    113: "Despejado",       116: "Parcialmente nublado", 119: "Nublado",
    122: "Muy nublado",     143: "Niebla",               176: "Lluvia ligera",
    179: "Nieve ligera",    182: "Aguanieve",             200: "Tormenta",
    227: "Nevada",          230: "Nevada intensa",        248: "Niebla",
    260: "Niebla helada",   263: "Llovizna",              266: "Llovizna",
    281: "Lluvia helada",   293: "Lluvia ligera",         296: "Lluvia ligera",
    299: "Lluvia moderada", 302: "Lluvia moderada",       305: "Lluvia intensa",
    308: "Lluvia intensa",  317: "Aguanieve",             320: "Nieve ligera",
    326: "Nieve ligera",    329: "Nieve moderada",        335: "Nieve intensa",
    350: "Granizo",         353: "Lluvia ligera",         356: "Lluvia intensa",
    359: "Lluvia torrencial",362: "Aguanieve",            368: "Nieve ligera",
    371: "Nieve intensa",   374: "Granizo",               386: "Tormenta",
    389: "Tormenta intensa",392: "Tormenta con nieve",    395: "Tormenta con nieve",
}


class WeatherService:
    """Obtiene el tiempo via wttr.in (gratuito, sin API key).

    Hot-reload: si se pasa config_manager, detecta cambios de ciudad
    y lanza un fetch inmediato sin reiniciar la app.
    """

    def __init__(self, city="Barcelona", refresh_interval=1800, config_manager=None):
        self.city             = city
        self.refresh_interval = max(300, refresh_interval)
        self._cfg_mgr         = config_manager
        self._reload_ev       = config_manager.register_listener() if config_manager else None
        self._cache = {
            'temp_c': None, 'feels_like_c': None, 'humidity': None,
            'wind_kmh': None, 'wind_dir': None, 'description': None,
            'weather_code': None, 'timestamp': None, 'error': None,
        }
        self._lock = threading.Lock()

    def get_data(self):
        with self._lock:
            return dict(self._cache)

    def _fetch(self):
        try:
            url = f"https://wttr.in/{self.city}?format=j1"
            resp = requests.get(url, timeout=10,
                                headers={'User-Agent': 'crypto-wall-dashboard/2.0'})
            resp.raise_for_status()
            data    = resp.json()
            current = data['current_condition'][0]
            code    = int(current.get('weatherCode', 113))
            desc_en = current['weatherDesc'][0]['value'] if current.get('weatherDesc') else ""
            desc    = WEATHER_DESC.get(code, desc_en)
            with self._lock:
                self._cache.update({
                    'temp_c':       int(current['temp_C']),
                    'feels_like_c': int(current['FeelsLikeC']),
                    'humidity':     int(current['humidity']),
                    'wind_kmh':     int(current['windspeedKmph']),
                    'wind_dir':     current.get('winddir16Point', '--'),
                    'description':  desc,
                    'weather_code': code,
                    'timestamp':    time.time(),
                    'error':        None,
                })
            logger.info(
                f"weather: {self.city} {self._cache['temp_c']}C, "
                f"{self._cache['description']}, viento {self._cache['wind_kmh']} km/h"
            )
        except requests.exceptions.Timeout:
            logger.warning("weather: timeout, manteniendo cache")
            with self._lock:
                self._cache['error'] = "timeout"
        except Exception as e:
            logger.error(f"weather: {e}")
            with self._lock:
                self._cache['error'] = str(e)

    def _run(self):
        time.sleep(random.randint(2, 10))
        while True:
            # Hot-reload: re-lee ciudad del config_manager
            if self._cfg_mgr:
                new_city = self._cfg_mgr.get().get('weather', {}).get('city', self.city)
                if new_city != self.city:
                    logger.info(f"weather: ciudad actualizada → {new_city}")
                    self.city = new_city
            self._fetch()
            # Espera interruptible
            if self._reload_ev:
                woken = self._reload_ev.wait(timeout=self.refresh_interval)
                if woken:
                    self._reload_ev.clear()
            else:
                time.sleep(self.refresh_interval)

    def start(self):
        t = threading.Thread(target=self._run, daemon=True, name="svc-weather")
        t.start()
        logger.info(f"weather: servicio iniciado para {self.city} (intervalo {self.refresh_interval}s)")
