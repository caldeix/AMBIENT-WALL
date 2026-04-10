"""
Crypto Wall Dashboard — Punto de entrada principal.
Ejecutar: python src/main.py
"""
import sys
import os
import logging
import logging.handlers

# Asegurar que src/ esta en el path para imports absolutos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Configuracion de logging
# ---------------------------------------------------------------------------

def setup_logging(log_cfg):
    level_name = log_cfg.get('level', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)
    log_file    = log_cfg.get('file', 'app.log')
    max_bytes   = log_cfg.get('max_bytes', 5 * 1024 * 1024)
    backup_count = log_cfg.get('backup_count', 3)

    fmt = logging.Formatter(
        '%(asctime)s [%(levelname)-7s] %(name)-20s — %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    root = logging.getLogger()
    root.setLevel(level)

    # Consola
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Archivo rotativo
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
# Carga de configuracion
# ---------------------------------------------------------------------------

def _default_config():
    return {
        'environment': 'pro',
        'display': {
            'fullscreen': True, 'hide_cursor': True,
        },
        'api_keys': {'coinmarketcap': ''},
        'cryptos': {
            'symbols': ['BTC', 'ETH', 'SOL', 'DOT'],
        },
        'weather': {'city': 'Barcelona'},
        'refresh': {
            'cryptos': 300, 'charts': 300,
            'market': 1800, 'weather': 1800,
        },
        'logging': {
            'level': 'INFO', 'file': 'app.log',
            'max_bytes': 5242880, 'backup_count': 3,
        },
    }


def load_config():
    # Buscar config.yaml en la raiz del proyecto (un nivel arriba de src/)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config.yaml')

    if not os.path.exists(config_path):
        logging.warning(f"config.yaml no encontrado en {config_path}. Usando valores por defecto.")
        return _default_config()

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        if not isinstance(cfg, dict):
            raise ValueError("El archivo config.yaml no contiene un objeto YAML valido.")
        # Fusionar con defaults para campos opcionales faltantes
        defaults = _default_config()
        for key, val in defaults.items():
            if key not in cfg:
                cfg[key] = val
            elif isinstance(val, dict):
                for subkey, subval in val.items():
                    cfg[key].setdefault(subkey, subval)
        return cfg
    except Exception as e:
        raise ValueError(f"Error al leer config.yaml: {e}")


# ---------------------------------------------------------------------------
# Arranque
# ---------------------------------------------------------------------------

def main():
    # 1. Cargar config
    try:
        config = load_config()
    except ValueError as err:
        # Mostrar error en pantalla en lugar de un traceback
        _show_error_screen(str(err))
        return

    # 2. Logging
    setup_logging(config.get('logging', {}))
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Crypto Wall Dashboard arrancando...")

    # 3. Validaciones basicas
    refresh = config.get('refresh', {})
    for key, val in refresh.items():
        if isinstance(val, (int, float)) and val < 60:
            logger.warning(
                f"Intervalo '{key}' = {val}s es menor que el minimo (60s). "
                f"Se usara 60s."
            )
            config['refresh'][key] = 60

    environment = config.get('environment', 'pro')
    symbols     = config.get('cryptos', {}).get('symbols', ['BTC', 'ETH'])
    api_keys    = config.get('api_keys', {})
    cmc_key     = api_keys.get('coinmarketcap', '')

    if environment == 'mockup':
        logger.info("coinmarketcap: modo mockup activo — sin llamadas a la API")
    elif not cmc_key:
        logger.warning("coinmarketcap: API key no configurada — cryptos mostraran 'Dato no disponible'")

    # 4. Inicializar servicios
    from services.coinmarketcap import CoinMarketCapService
    from services.market_data import MarketDataService
    from services.weather import WeatherService

    cmc_service = CoinMarketCapService(
        api_key=cmc_key,
        symbols=symbols,
        refresh_interval=refresh.get('cryptos', 300),
        environment=environment,
    )
    market_service = MarketDataService(
        interval_charts=refresh.get('charts', 300),
        interval_market=refresh.get('market', 1800),
    )
    weather_cfg  = config.get('weather', {})
    weather_city = weather_cfg.get('city', 'Barcelona')
    weather_service = WeatherService(
        city=weather_city,
        refresh_interval=refresh.get('weather', 1800),
    )

    cmc_service.start()
    market_service.start()
    weather_service.start()
    logger.info("Servicios de datos iniciados")

    # 5. Arrancar UI (bloquea hasta que se cierre la ventana)
    from ui.app import App
    app = App(config, cmc_service, market_service, weather_service)
    logger.info("Entrando en mainloop de Tkinter")
    app.mainloop()
    logger.info("Aplicacion cerrada")


def _show_error_screen(message):
    """Muestra un mensaje de error en pantalla completa en lugar de un traceback."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.title("Error de configuracion")
        root.configure(bg='#0a0a1a')
        root.geometry("800x300")
        tk.Label(
            root,
            text="ERROR DE CONFIGURACION",
            font=('Helvetica', 16, 'bold'),
            fg='#ff2244', bg='#0a0a1a',
        ).pack(expand=True, pady=(40, 10))
        tk.Label(
            root,
            text=message,
            font=('Helvetica', 12),
            fg='#e0e0e0', bg='#0a0a1a',
            wraplength=700, justify='left',
        ).pack(expand=True, padx=40)
        tk.Label(
            root,
            text="Revisa config.yaml y reinicia la aplicacion.",
            font=('Helvetica', 11),
            fg='#8888aa', bg='#0a0a1a',
        ).pack(expand=True, pady=(10, 40))
        root.bind('<Escape>', lambda e: root.destroy())
        root.mainloop()
    except Exception:
        print(f"ERROR CRITICO: {message}", file=sys.stderr)


if __name__ == '__main__':
    main()
