"""
Crypto Wall Dashboard — Punto de entrada principal.
Ejecutar: python src/main.py
"""
import sys
import os
import logging
import logging.handlers

# Rutas: src/ para imports de servicios/UI, raíz del proyecto para shared/
_SRC_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SRC_DIR)
sys.path.insert(0, _SRC_DIR)
sys.path.insert(0, _PROJECT_DIR)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(log_cfg):
    level_name   = log_cfg.get('level', 'INFO').upper()
    level        = getattr(logging, level_name, logging.INFO)
    log_file     = log_cfg.get('file', 'app.log')
    max_bytes    = log_cfg.get('max_bytes', 5 * 1024 * 1024)
    backup_count = log_cfg.get('backup_count', 3)

    fmt = logging.Formatter(
        '%(asctime)s [%(levelname)-7s] %(name)-20s — %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    root = logging.getLogger()
    root.setLevel(level)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    try:
        fh = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes,
            backupCount=backup_count, encoding='utf-8',
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception as e:
        logging.warning(f"No se pudo abrir el archivo de log '{log_file}': {e}")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _default_chart_blocks():
    from services.market_data import DEFAULT_CHART_BLOCKS
    return DEFAULT_CHART_BLOCKS


def _default_config():
    return {
        'environment': 'pro',
        'display':  {'fullscreen': True, 'hide_cursor': True},
        'api_keys': {'coinmarketcap': ''},
        'cryptos':  {'symbols': ['BTC', 'ETH', 'SOL', 'DOT']},
        'chart_blocks': _default_chart_blocks(),
        'weather':  {'city': 'Barcelona'},
        'refresh':  {'cryptos': 300, 'charts': 300, 'market': 1800, 'weather': 1800},
        'logging':  {'level': 'INFO', 'file': 'app.log', 'max_bytes': 5242880, 'backup_count': 3},
    }


def load_config():
    config_path = os.path.join(_PROJECT_DIR, 'config.yaml')
    if not os.path.exists(config_path):
        logging.warning(f"config.yaml no encontrado. Usando valores por defecto.")
        return _default_config(), config_path

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        if not isinstance(cfg, dict):
            raise ValueError("El archivo config.yaml no contiene un objeto YAML válido.")
        defaults = _default_config()
        for key, val in defaults.items():
            if key not in cfg:
                cfg[key] = val
            elif isinstance(val, dict):
                for subkey, subval in val.items():
                    cfg[key].setdefault(subkey, subval)
        return cfg, config_path
    except Exception as e:
        raise ValueError(f"Error al leer config.yaml: {e}")


# ---------------------------------------------------------------------------
# Arranque
# ---------------------------------------------------------------------------

def main():
    try:
        config, config_path = load_config()
    except ValueError as err:
        _show_error_screen(str(err))
        return

    setup_logging(config.get('logging', {}))
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Crypto Wall Dashboard arrancando...")

    # Validar intervalos mínimos
    refresh = config.get('refresh', {})
    for key, val in refresh.items():
        if isinstance(val, (int, float)) and val < 60:
            logger.warning(f"Intervalo '{key}' = {val}s < mínimo 60s. Usando 60s.")
            config['refresh'][key] = 60

    environment = config.get('environment', 'pro')
    cmc_key     = config.get('api_keys', {}).get('coinmarketcap', '')

    if environment == 'mockup':
        logger.info("coinmarketcap: modo mockup activo — sin llamadas a la API")
    elif not cmc_key:
        logger.warning("coinmarketcap: API key no configurada")

    # ConfigManager — config viva + file watcher (detecta cambios de app-config)
    from shared.config_manager import ConfigManager
    cfg_manager = ConfigManager(config, config_path)
    cfg_manager.start_file_watcher()

    # Incluye cmc_symbol de chart_blocks (BTC, ETH) desde el primer fetch
    symbols = cfg_manager.get_symbols()

    # Servicios de datos
    from services.coinmarketcap import CoinMarketCapService
    from services.market_data   import MarketDataService
    from services.weather       import WeatherService

    cmc_service = CoinMarketCapService(
        api_key=cmc_key,
        symbols=symbols,
        refresh_interval=refresh.get('cryptos', 300),
        environment=environment,
        config_manager=cfg_manager,
    )
    market_service = MarketDataService(
        interval_charts=refresh.get('charts', 300),
        interval_market=refresh.get('market', 1800),
        config_manager=cfg_manager,
    )
    weather_service = WeatherService(
        city=config.get('weather', {}).get('city', 'Barcelona'),
        refresh_interval=refresh.get('weather', 1800),
        config_manager=cfg_manager,
    )

    cmc_service.start()
    market_service.start()
    weather_service.start()
    logger.info("Servicios de datos iniciados")

    # UI
    from ui.app import App
    app = App(config, cmc_service, market_service, weather_service, config_manager=cfg_manager)
    logger.info("Entrando en mainloop de Tkinter")
    app.mainloop()
    logger.info("Aplicación cerrada")


def _show_error_screen(message):
    try:
        import tkinter as tk
        root = tk.Tk()
        root.title("Error de configuración")
        root.configure(bg='#0a0a1a')
        root.geometry("800x300")
        tk.Label(root, text="ERROR DE CONFIGURACIÓN",
                 font=('Helvetica', 16, 'bold'), fg='#ff2244', bg='#0a0a1a').pack(expand=True, pady=(40, 10))
        tk.Label(root, text=message,
                 font=('Helvetica', 12), fg='#e0e0e0', bg='#0a0a1a',
                 wraplength=700, justify='left').pack(expand=True, padx=40)
        tk.Label(root, text="Revisa config.yaml y reinicia la aplicación.",
                 font=('Helvetica', 11), fg='#8888aa', bg='#0a0a1a').pack(expand=True, pady=(10, 40))
        root.bind('<Escape>', lambda e: root.destroy())
        root.mainloop()
    except Exception:
        print(f"ERROR CRÍTICO: {message}", file=sys.stderr)


if __name__ == '__main__':
    main()
