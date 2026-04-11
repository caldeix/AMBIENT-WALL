"""
Ruta de geolocalización.
  GET /api/location?lat=41.38&lon=2.17  — reverse geocode a nombre de ciudad
  Usa Nominatim (OpenStreetMap) — gratuito, sin API key.
"""
import logging

import requests
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

location_bp = Blueprint('location', __name__)

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
_HEADERS = {'User-Agent': 'CryptoWallDashboard/2.0'}


@location_bp.get('/location')
def get_location():
    try:
        lat = float(request.args['lat'])
        lon = float(request.args['lon'])
    except (KeyError, ValueError):
        return jsonify({'error': 'lat y lon requeridos (float)'}), 400

    try:
        resp = requests.get(
            _NOMINATIM_URL,
            params={'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 10},
            headers=_HEADERS,
            timeout=5,
        )
        resp.raise_for_status()
        data    = resp.json()
        address = data.get('address', {})
        city    = (
            address.get('city')
            or address.get('town')
            or address.get('village')
            or address.get('county')
            or data.get('display_name', '').split(',')[0]
        )
        return jsonify({'city': city, 'display_name': data.get('display_name', '')})
    except Exception as e:
        logger.error(f"location reverse geocode: {e}")
        return jsonify({'error': str(e)}), 500
