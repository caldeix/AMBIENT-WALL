import threading
import time
import random
import html
import re
import logging

import requests

logger = logging.getLogger(__name__)

DEFAULT_FEEDS = [
    ('COINTELEGRAPH', 'https://cointelegraph.com/rss'),
    ('COINDESK',      'https://www.coindesk.com/arc/outboundfeeds/rss/'),
]

MAX_ITEMS = 30


class RSSService:
    """Obtiene noticias cripto de feeds RSS (Cointelegraph + CoinDesk).

    Usa feedparser (sin API key). Mezcla ambos feeds, ordena por fecha
    y guarda los MAX_ITEMS mas recientes en cache.
    """

    def __init__(self, feeds=None, refresh_interval=1800):
        self._feeds = feeds or DEFAULT_FEEDS
        self._interval = max(300, refresh_interval)
        self._cache = {
            'items': [],      # lista de dicts: {title, source, published}
            'timestamp': None,
            'error': None,
        }
        self._lock = threading.Lock()

    def get_data(self):
        with self._lock:
            return dict(self._cache)

    def _fetch(self):
        try:
            import feedparser
            all_items = []
            for source, url in self._feeds:
                try:
                    # Fetch con timeout controlado via requests, luego parsear contenido
                    resp = requests.get(
                        url, timeout=8,
                        headers={'User-Agent': 'crypto-wall-dashboard/1.0'},
                    )
                    resp.raise_for_status()
                    feed = feedparser.parse(resp.content)
                    for entry in feed.entries[:15]:
                        title = html.unescape(entry.get('title', '')).strip()
                        title = re.sub(r'<[^>]+>', '', title).strip()
                        if not title:
                            continue
                        published = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published = time.mktime(entry.published_parsed)
                        all_items.append({
                            'title': title,
                            'source': source,
                            'published': published or time.time(),
                        })
                    logger.info(f"rss: {source} — {len(feed.entries)} items obtenidos")
                except Exception as e:
                    logger.error(f"rss: {source} error: {e}")

            if not all_items:
                logger.warning("rss: ningun feed devolvio items")
                return

            all_items.sort(key=lambda x: x['published'], reverse=True)
            all_items = all_items[:MAX_ITEMS]

            with self._lock:
                self._cache['items']     = all_items
                self._cache['timestamp'] = time.time()
                self._cache['error']     = None

            logger.info(f"rss: cache actualizada con {len(all_items)} noticias")

        except ImportError:
            logger.error("rss: feedparser no instalado. Ejecuta: pip install feedparser")
            with self._lock:
                self._cache['error'] = "feedparser no instalado"
        except Exception as e:
            logger.error(f"rss: error general: {e}")
            with self._lock:
                self._cache['error'] = str(e)

    def _run(self):
        time.sleep(random.randint(3, 12))
        while True:
            self._fetch()
            time.sleep(self._interval)

    def start(self):
        t = threading.Thread(target=self._run, daemon=True, name="svc-rss")
        t.start()
        logger.info(
            f"rss: servicio iniciado — "
            f"{len(self._feeds)} feeds, intervalo {self._interval}s"
        )
