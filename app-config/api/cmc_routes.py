"""
Rutas CoinMarketCap.
  GET /api/cmc/coins?q=&page=1&limit=50  — búsqueda paginada en el mapa local
  POST /api/cmc/refresh                  — fuerza recarga del mapa desde CMC
"""
import json
import logging
import os
import time

import requests
import yaml
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

cmc_bp = Blueprint('cmc', __name__)

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHE_FILE  = os.path.join(_PROJECT_DIR, 'resources', 'cmc_map_cache.json')
_CACHE_TTL   = 7 * 24 * 3600   # 1 semana
_CMC_LIMIT   = 3000
_CMC_BASE    = "https://pro-api.coinmarketcap.com"

# Cache en memoria (se carga al primer acceso)
_map_data = []
_map_loaded_at = 0.0


def _get_api_key():
    config_path = os.path.join(_PROJECT_DIR, 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get('api_keys', {}).get('coinmarketcap', '')
    except Exception:
        return ''


def _fetch_from_cmc(api_key):
    """Descarga las primeras _CMC_LIMIT monedas activas de CMC."""
    resp = requests.get(
        f"{_CMC_BASE}/v1/cryptocurrency/map",
        params={'listing_status': 'active', 'limit': _CMC_LIMIT, 'sort': 'cmc_rank'},
        headers={'X-CMC_PRO_API_KEY': api_key, 'Accept': 'application/json'},
        timeout=15,
    )
    resp.raise_for_status()
    coins = resp.json().get('data', [])
    # Guardar solo los campos necesarios
    return [
        {'id': c['id'], 'rank': c.get('rank', 9999),
         'name': c['name'], 'symbol': c['symbol']}
        for c in coins if c.get('is_active') == 1
    ]


def _save_cache(coins):
    os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
    with open(_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'fetched_at': time.time(), 'data': coins}, f, ensure_ascii=False)


def _load_cache():
    with open(_CACHE_FILE, 'r', encoding='utf-8') as f:
        obj = json.load(f)
    return obj.get('data', []), obj.get('fetched_at', 0.0)


def _ensure_map(force=False):
    """Asegura que _map_data está cargado y no ha expirado."""
    global _map_data, _map_loaded_at

    # ¿Ya en memoria y fresco?
    if not force and _map_data and (time.time() - _map_loaded_at) < _CACHE_TTL:
        return

    # ¿Cache en disco válida?
    if not force and os.path.exists(_CACHE_FILE):
        try:
            coins, fetched_at = _load_cache()
            if coins and (time.time() - fetched_at) < _CACHE_TTL:
                _map_data      = coins
                _map_loaded_at = fetched_at
                logger.info(f"cmc_map: cargado desde disco ({len(coins)} monedas)")
                return
        except Exception as e:
            logger.warning(f"cmc_map: cache de disco inválida: {e}")

    # Descargar de CMC
    api_key = _get_api_key()
    if not api_key:
        logger.warning("cmc_map: API key no configurada, no se puede descargar el mapa")
        return

    try:
        coins = _fetch_from_cmc(api_key)
        _save_cache(coins)
        _map_data      = coins
        _map_loaded_at = time.time()
        logger.info(f"cmc_map: descargado de CMC ({len(coins)} monedas)")
    except Exception as e:
        logger.error(f"cmc_map: error al descargar: {e}")
        # Si falla y hay cache vieja, úsala
        if os.path.exists(_CACHE_FILE):
            try:
                coins, fetched_at = _load_cache()
                _map_data      = coins
                _map_loaded_at = fetched_at
                logger.warning("cmc_map: usando cache de disco expirada como fallback")
            except Exception:
                pass


@cmc_bp.get('/cmc/coins')
def get_coins():
    _ensure_map()
    if not _map_data:
        return jsonify({'error': 'Mapa CMC no disponible. Comprueba la API key.'}), 503

    q     = request.args.get('q', '').strip().lower()
    page  = max(1, int(request.args.get('page', 1)))
    limit = min(100, max(1, int(request.args.get('limit', 50))))

    if q:
        # Coincidencia exacta de símbolo primero, luego nombre empieza por q, luego contiene q
        exact   = [c for c in _map_data if c['symbol'].lower() == q]
        starts  = [c for c in _map_data if c['name'].lower().startswith(q) and c not in exact]
        rest    = [c for c in _map_data if q in c['name'].lower() and c not in exact and c not in starts]
        filtered = exact + starts + rest
    else:
        filtered = _map_data   # ya ordenado por rank

    total  = len(filtered)
    offset = (page - 1) * limit
    page_data = filtered[offset:offset + limit]

    return jsonify({
        'total': total,
        'page':  page,
        'pages': (total + limit - 1) // limit,
        'results': page_data,
    })


@cmc_bp.post('/cmc/refresh')
def refresh_map():
    api_key = _get_api_key()
    if not api_key:
        return jsonify({'error': 'API key no configurada'}), 400
    try:
        _ensure_map(force=True)
        return jsonify({'ok': True, 'count': len(_map_data)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
