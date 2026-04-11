"""
Rutas de configuración.
  GET  /api/config          — devuelve config.yaml como JSON
  POST /api/config          — sobreescribe config.yaml y señala hot-reload
"""
import os
import logging

import yaml
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

config_bp = Blueprint('config', __name__)

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'config.yaml',
)


def _read_config():
    with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _write_config(data):
    with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, indent=2)


@config_bp.get('/config')
def get_config():
    try:
        return jsonify(_read_config())
    except FileNotFoundError:
        return jsonify({'error': 'config.yaml no encontrado'}), 404
    except Exception as e:
        logger.error(f"config GET: {e}")
        return jsonify({'error': str(e)}), 500


@config_bp.post('/config')
def post_config():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'JSON inválido'}), 400
    try:
        _write_config(data)
        logger.info("config POST: config.yaml actualizado")
        return jsonify({'ok': True})
    except Exception as e:
        logger.error(f"config POST: {e}")
        return jsonify({'error': str(e)}), 500
