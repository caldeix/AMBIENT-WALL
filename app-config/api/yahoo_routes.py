"""
Rutas Yahoo Finance.
  GET  /api/yahoo/search?q=   — búsqueda de tickers via yf.Search
  POST /api/yahoo/validate    — verifica si un ticker tiene datos históricos
                                body: {"ticker": "BTC-USD", "period": "7d"}
"""
import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

yahoo_bp = Blueprint('yahoo', __name__)


@yahoo_bp.get('/yahoo/search')
def search_yahoo():
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify({'results': []})
    try:
        import yfinance as yf
        results_raw = yf.Search(q, max_results=15).quotes
        results = [
            {
                'ticker':   r.get('symbol', ''),
                'name':     r.get('shortname') or r.get('longname', ''),
                'type':     r.get('typeDisp', ''),
                'exchange': r.get('exchange', ''),
            }
            for r in results_raw
            if r.get('symbol')
        ]
        return jsonify({'results': results})
    except AttributeError:
        # yfinance antiguo sin Search
        return jsonify({'error': 'yfinance >= 0.2.37 requerido para búsqueda'}), 501
    except Exception as e:
        logger.error(f"yahoo search '{q}': {e}")
        return jsonify({'error': str(e)}), 500


@yahoo_bp.post('/yahoo/validate')
def validate_ticker():
    """Verifica que un ticker tiene datos históricos descargables."""
    body   = request.get_json(silent=True) or {}
    ticker = body.get('ticker', '').strip()
    period = body.get('period', '7d')

    if not ticker:
        return jsonify({'valid': False, 'error': 'ticker vacío'}), 400

    try:
        import yfinance as yf
        interval = '1h' if period == '7d' else '1d'
        hist = yf.Ticker(ticker).history(period=period, interval=interval)
        if hist.empty:
            return jsonify({
                'valid': False,
                'error': f'Sin datos históricos para {ticker} (period={period})',
            })
        price = float(hist['Close'].dropna().iloc[-1])
        return jsonify({'valid': True, 'price': price, 'points': len(hist)})
    except Exception as e:
        logger.warning(f"yahoo validate '{ticker}': {e}")
        return jsonify({'valid': False, 'error': str(e)})
