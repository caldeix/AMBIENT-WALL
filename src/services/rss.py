import threading
import time
import random
import html
import re
import logging
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

logger = logging.getLogger(__name__)

DEFAULT_FEEDS = [
    ('COINTELEGRAPH', 'https://cointelegraph.com/rss'),
    ('COINDESK',      'https://www.coindesk.com/arc/outboundfeeds/rss/'),
]

MAX_ITEMS = 30


def _parse_rss(content):
    """Parsea RSS 2.0 con xml.etree.ElementTree (stdlib, sin dependencias externas)."""
    items = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        raise ValueError(f"XML invalido: {e}")

    # Soporte RSS 2.0 (<rss><channel><item>) y Atom (<feed><entry>)
    ns_atom = '{http://www.w3.org/2005/Atom}'
    if root.tag == f'{ns_atom}feed':
        # Atom feed
        for entry in root.findall(f'{ns_atom}entry')[:15]:
            title = entry.findtext(f'{ns_atom}title', '').strip()
            published_str = entry.findtext(f'{ns_atom}published') or entry.findtext(f'{ns_atom}updated', '')
            published = _parse_date_iso(published_str)
            items.append({'title': _clean(title), 'published': published})
    else:
        # RSS 2.0
        channel = root.find('channel') or root
        for item in channel.findall('item')[:15]:
            title = item.findtext('title', '').strip()
            pubdate = item.findtext('pubDate', '')
            published = _parse_date_rfc2822(pubdate)
            items.append({'title': _clean(title), 'published': published})

    return items


def _clean(text):
    """Elimina tags HTML y decodifica entidades."""
    text = html.unescape(text or '')
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


def _parse_date_rfc2822(s):
    """Parsea fecha RFC 2822 (pubDate de RSS): 'Mon, 08 Mar 2026 10:00:00 +0000'."""
    try:
        return parsedate_to_datetime(s).timestamp()
    except Exception:
        return time.time()


def _parse_date_iso(s):
    """Parsea fecha ISO 8601 (Atom): '2026-03-08T10:00:00Z'."""
    try:
        import datetime
        s = s.rstrip('Z').split('+')[0]
        dt = datetime.datetime.fromisoformat(s)
        return dt.timestamp()
    except Exception:
        return time.time()


class RSSService:
    """Obtiene noticias cripto de feeds RSS (Cointelegraph + CoinDesk).

    Parsea RSS 2.0 con xml.etree.ElementTree (stdlib puro, sin feedparser).
    Mezcla ambos feeds, ordena por fecha y guarda los MAX_ITEMS mas recientes.
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
        all_items = []
        for source, url in self._feeds:
            try:
                resp = requests.get(
                    url, timeout=8,
                    headers={'User-Agent': 'crypto-wall-dashboard/1.0'},
                )
                resp.raise_for_status()
                parsed = _parse_rss(resp.content)
                for item in parsed:
                    if not item['title']:
                        continue
                    all_items.append({
                        'title':     item['title'],
                        'source':    source,
                        'published': item['published'],
                    })
                logger.info(f"rss: {source} — {len(parsed)} items obtenidos")
            except Exception as e:
                logger.error(f"rss: {source} error: {e}")

        if not all_items:
            logger.warning("rss: ningun feed devolvio items")
            with self._lock:
                self._cache['error'] = "sin datos"
            return

        all_items.sort(key=lambda x: x['published'], reverse=True)
        all_items = all_items[:MAX_ITEMS]

        with self._lock:
            self._cache['items']     = all_items
            self._cache['timestamp'] = time.time()
            self._cache['error']     = None

        logger.info(f"rss: cache actualizada con {len(all_items)} noticias")

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
