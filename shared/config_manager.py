"""
ConfigManager — config viva compartida entre el dashboard y app-config.

Uso en el dashboard (src/main.py):
    mgr = ConfigManager(config_dict, config_path)
    mgr.start_file_watcher()          # detecta cambios externos de app-config
    ev  = mgr.register_listener()     # evento que los servicios escuchan

Uso en app-config (escribe config.yaml y el file watcher del dashboard lo detecta):
    No necesita ConfigManager — lee/escribe config.yaml directamente.
"""
import copy
import logging
import os
import threading
import time

import yaml

logger = logging.getLogger(__name__)


class ConfigManager:
    """Config viva con notificación de cambios a servicios.

    Thread-safe. Los servicios llaman a register_listener() y reciben
    un threading.Event que se activa cuando el config cambia.
    """

    def __init__(self, config_dict, config_path):
        self._config      = copy.deepcopy(config_dict)
        self._config_path = config_path
        self._lock        = threading.Lock()
        self._listeners   = []   # lista de threading.Event

    # ------------------------------------------------------------------
    # Registro de listeners (uno por thread de servicio)
    # ------------------------------------------------------------------

    def register_listener(self):
        """Devuelve un Event propio que se activa en cada reload."""
        ev = threading.Event()
        self._listeners.append(ev)
        return ev

    def _notify_listeners(self):
        for ev in self._listeners:
            ev.set()
        logger.debug(f"config_manager: {len(self._listeners)} listeners notificados")

    # ------------------------------------------------------------------
    # Lectura thread-safe
    # ------------------------------------------------------------------

    def get(self):
        with self._lock:
            return copy.deepcopy(self._config)

    def get_symbols(self):
        """Devuelve todos los símbolos CMC: cryptos.symbols + cmc_symbol de chart_blocks."""
        with self._lock:
            base = list(self._config.get('cryptos', {}).get('symbols', []))
            chart_syms = [
                b['cmc_symbol'].upper()
                for b in self._config.get('chart_blocks', [])
                if b.get('cmc_symbol')
            ]
            seen, result = set(), []
            for s in chart_syms + [x.upper() for x in base]:
                if s not in seen:
                    seen.add(s)
                    result.append(s)
            return result

    def get_chart_blocks(self):
        with self._lock:
            return copy.deepcopy(self._config.get('chart_blocks', []))

    def get_environment(self):
        with self._lock:
            return self._config.get('environment', 'pro')

    def get_api_key(self, service):
        with self._lock:
            return self._config.get('api_keys', {}).get(service, '')

    @property
    def config_path(self):
        return self._config_path

    # ------------------------------------------------------------------
    # Escritura (uso interno / tests — app-config escribe el fichero directamente)
    # ------------------------------------------------------------------

    def update_from_dict(self, new_config):
        """Actualiza config en memoria y notifica listeners."""
        with self._lock:
            self._config = copy.deepcopy(new_config)
        self._notify_listeners()
        logger.info("config_manager: config actualizado en memoria")

    # ------------------------------------------------------------------
    # File watcher — detecta cambios externos (escritura desde app-config)
    # ------------------------------------------------------------------

    def start_file_watcher(self):
        """Arranca daemon thread que vigila config.yaml y recarga si cambia."""
        t = threading.Thread(
            target=self._watch_loop,
            daemon=True,
            name="cfg-watcher",
        )
        t.start()
        logger.info(f"config_manager: vigilando {self._config_path}")

    def _watch_loop(self):
        last_mtime = self._mtime()
        while True:
            time.sleep(2)
            try:
                mtime = self._mtime()
                if mtime and mtime != last_mtime:
                    last_mtime = mtime
                    self._reload_from_disk()
            except Exception as e:
                logger.error(f"config_manager: error en file watcher: {e}")

    def _mtime(self):
        try:
            return os.path.getmtime(self._config_path)
        except OSError:
            return None

    def _reload_from_disk(self):
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                new_cfg = yaml.safe_load(f)
            if not isinstance(new_cfg, dict):
                logger.warning("config_manager: config.yaml inválido, ignorando")
                return
            with self._lock:
                self._config = new_cfg
            self._notify_listeners()
            logger.info("config_manager: config.yaml recargado desde disco")
        except Exception as e:
            logger.error(f"config_manager: error al recargar config.yaml: {e}")
