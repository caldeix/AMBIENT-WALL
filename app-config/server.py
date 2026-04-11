"""
Financial Wall — App de configuración web.

Ejecutar (independiente del dashboard):
    python app-config/server.py

Acceder desde cualquier PC de la red:
    http://<ip-raspberry>:5001

El servidor lee y escribe config.yaml en la raíz del proyecto.
El dashboard detecta los cambios via file watcher y recarga los servicios
sin reiniciar la app (hot-reload de símbolos y chart_blocks).

Crontab (junto al dashboard):
    @reboot sleep 15 && DISPLAY=:0 ... python /home/crypto-wall/src/main.py &
    @reboot sleep 16 && python /home/crypto-wall/app-config/server.py
"""
import logging
import os
import sys

from flask import Flask, send_from_directory

# Asegurar que la raíz del proyecto está en el path (para shared/)
_APP_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_APP_DIR)
sys.path.insert(0, _PROJECT_DIR)

from api.config_routes   import config_bp
from api.cmc_routes      import cmc_bp
from api.yahoo_routes    import yahoo_bp
from api.location_routes import location_bp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-7s] %(name)-20s — %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')

# Registrar blueprints bajo /api
app.register_blueprint(config_bp,   url_prefix='/api')
app.register_blueprint(cmc_bp,      url_prefix='/api')
app.register_blueprint(yahoo_bp,    url_prefix='/api')
app.register_blueprint(location_bp, url_prefix='/api')


@app.get('/')
def index():
    return send_from_directory('static', 'index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Financial Wall Config iniciando en http://0.0.0.0:{port}")
    logger.info(f"Accede desde la red en http://<ip-dispositivo>:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
