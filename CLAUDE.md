# Financial Wall — Contexto para Claude

## Qué es este proyecto

Dashboard ambient display en Tkinter para Raspberry Pi que muestra precios de cryptos,
commodities e índices en tiempo real. Incluye una webapp Flask de configuración accesible
desde la red local.

Entornos: `mockup` (sin API, datos falsos) | `test` (real, ventana) | `pro` (fullscreen, RPi)

---

## Árbol de archivos clave

```
crypto_wall/
├── src/
│   ├── main.py                        # Punto de entrada: carga config, arranca servicios, crea App
│   ├── services/
│   │   ├── coinmarketcap.py           # Precios + rank CMC, hot-reload de símbolos
│   │   ├── market_data.py             # Historial OHLC Yahoo Finance (2 threads: charts/market)
│   │   └── weather.py                 # Temperatura wttr.in
│   └── ui/
│       ├── app.py                     # tk.Tk: TopBar + MarketPanel en grid 5%/95%
│       ├── theme.py                   # ÚNICA fuente de colores y fuentes — siempre importar de aquí
│       └── widgets/
│           ├── top_bar.py             # Reloj / fecha / clima — 3 labels + glow separator
│           └── market_panel.py        # Todo el contenido: 6 chart blocks + altcoin grid
├── shared/
│   └── config_manager.py             # Config viva thread-safe + file watcher + notify listeners
├── app-config/
│   ├── server.py                      # Flask app (puerto 5001)
│   ├── static/index.html              # SPA vanilla JS + SortableJS drag-and-drop
│   └── api/
│       ├── config_routes.py           # GET/POST /api/config → lee/escribe config.yaml
│       ├── cmc_routes.py              # GET /api/cmc/coins, /cmc/ranks, POST /cmc/refresh
│       ├── yahoo_routes.py            # GET /api/yahoo/validate?ticker=
│       └── location_routes.py        # GET /api/location/search?q=
├── config.yaml                        # NO en git — generado desde config.example.yaml
├── config.example.yaml                # Plantilla documentada con todos los campos
├── CLAUDE.md                          # Este archivo
└── requirements.txt                   # requests, matplotlib, yfinance, pyyaml, flask
```

---

## Arquitectura: flujo de datos

```
Threads de servicio           Cache thread-safe          Tkinter (main thread)
──────────────────────        ─────────────────          ──────────────────────
CoinMarketCapService  ──►    _cache dict + Lock    ◄──  MarketPanel.after(5000)
MarketDataService(×2) ──►    _cache dict + Lock    ◄──  → _update_display()
WeatherService        ──►    _cache dict + Lock    ◄──  TopBar.after(1000)
```

- Los servicios escriben en su `_cache` con `threading.Lock`.
- La UI llama a `service.get_data()` (devuelve copia) vía `widget.after()` — nunca bloquea el mainloop.
- **Hot-reload**: `ConfigManager` vigila `config.yaml` cada 2 s. Al detectar cambio → notifica `threading.Event` a cada servicio → el servicio despierta de su `wait()` y re-lee config sin reiniciar la app.

---

## Config system

- `config.yaml` en la raíz del proyecto — escrito por la webapp, leído por el dashboard.
- `ConfigManager` (`shared/config_manager.py`) es el árbitro thread-safe; provee `get_symbols()`, `get_chart_blocks()`, `get_environment()`, `get_api_key(service)`.
- Cada servicio llama `config_manager.register_listener()` → recibe su propio `threading.Event`.
- La webapp **no** usa ConfigManager — escribe directamente el YAML; el file watcher lo detecta.

Secciones clave de `config.yaml`:
```yaml
environment: pro | test | mockup
display:     { fullscreen, hide_cursor, sim_resolution }
api_keys:    { coinmarketcap }
weather:     { city }
chart_blocks:            # lista de hasta 6 bloques
  - label, ticker, period, cmc_symbol, format
cryptos:
  symbols: [SOL, DOT, ...]   # altcoin grid (excluye cmc_symbol de chart_blocks)
refresh:     { cryptos, charts, market, weather }
             # mínimos: cryptos=300s, charts=300s, market=1800s, weather=1800s
```

---

## Theme system (`src/ui/theme.py`)

**SIEMPRE** importar constantes desde `theme.py`. Nunca hardcodear colores o fuentes en otros archivos.

Variables principales:
```python
# Fondos
BG_GLOBAL, BG_PANEL
BG_PANEL_CRYPTO    = '#0d0d20'   # bloques crypto
BG_PANEL_COMMODITY = '#0f0e18'   # bloques commodity
BG_PANEL_INDEX     = '#0d1210'   # bloques índice
BG_ALT_ROW_ODD     = '#0c0c1e'   # zebra altcoin grid (impar)
BG_ALT_ROW_EVEN    = '#101025'   # zebra altcoin grid (par)
BG_CHANGE_UP       = '#091409'   # tinte verde oscuro — precio subiendo 24h
BG_CHANGE_DOWN     = '#150a08'   # tinte cálido oscuro — precio bajando 24h

# Separadores (efecto glow: línea bright encima de línea dark)
SEP_BRIGHT = '#2a2a50'
SEP_DARK   = '#0c0c1e'

# Acentos y stripes por tipo de activo
STRIPE_CRYPTO='#00d4ff'   ACCENT_CRYPTO='#00d4ff'    # cian eléctrico
STRIPE_COMMODITY='#f5a623' ACCENT_COMMODITY='#f5a623' # ámbar dorado
STRIPE_INDEX='#00e676'    ACCENT_INDEX='#00e676'      # menta brillante

# Rank badges (uniformes, sin distinción por tier)
RANK_OTHER_BG='#12121e'  RANK_OTHER_FG='#5a5a88'

# Precios
POSITIVE='#00e676'   NEGATIVE='#ff3d5a'

# Top bar
TOPBAR_BG, TOPBAR_CLOCK, TOPBAR_DATE, TOPBAR_WEATHER

# Fuentes — usar el alias correcto según contexto:
FONT_BLOCK_TICKER, FONT_BLOCK_PRICE, FONT_BLOCK_EUR, FONT_BLOCK_CHANGE
FONT_ALT_TICKER, FONT_ALT_VALUE, FONT_ALT_EUR, FONT_ALT_CHANGE
FONT_RANK_BADGE
FONT_TOPBAR_CLOCK, FONT_TOPBAR_DATE, FONT_TOPBAR_WEATHER
```

---

## market_panel.py — estructura interna

El archivo más grande (~650 líneas). Importa todo de `theme.py`.

```
MarketPanel(tk.Frame)
├── _build_chart_grid()         # 2 filas × 3 cols de chart blocks
│   └── _make_chart_block()     # stripe 4px izq + header + eur_row + matplotlib canvas
├── _build_alt_section()        # separador doble + rejilla altcoin N_COLS=3
│   └── celdas por símbolo      # rank_pill + ticker + price + eur + change
└── _update_display()           # llamado cada 5s vía after(); lee caches de CMC + market
    ├── chart blocks:
    │   ├── cmc cache → price, change_24h, rank
    │   ├── market cache → history, ohlc, history_dates
    │   ├── _tint_for_change(change, neutral_bg) → bg dinámico
    │   ├── _apply_block_tint(refs, bg) → actualiza widgets (excluye rank_pill y canvas)
    │   └── _draw_chart() → _draw_candles() o línea fallback
    └── altcoins:
        ├── cmc cache → price, change_24h, rank
        └── tinte directo en cell + labels (excluye rank_pill)
```

**`refs` dict** de cada chart block — keys disponibles:
```
ticker_lbl, price, change, fresh_dot, fresh_lbl, eur_lbl,
date_start, date_end, rank_pill, canvas_widget,
content_frame, header_frame, eur_row_frame, date_row_frame, bg
```

**`_alt_refs[sym]`** — 7-tupla:
```python
(cell, row_bg, rank_pill, ticker_lbl, price_lbl, eur_lbl, change_lbl)
```

**Candlestick rendering**:
- `_draw_candles(ax, ohlc, bg, accent)` — `mpatches.Rectangle` para cuerpos, `ax.plot` para mechas (max 35 velas)
- `_draw_chart(ticker, prices, dates, ohlc=None)` — usa ohlc si disponible, línea como fallback

**Cache keys de MarketDataService** — patrón: `ticker_key(ticker) + sufijo`
```python
ticker_key('BTC-USD') → 'btc_usd'    # re.sub(r'[^a-z0-9]', '_', ticker.lower())
ticker_key('^GSPC')   → 'gspc'
ticker_key('GC=F')    → 'gc_f'
# sufijos: _price, _history, _history_dates, _ohlc, _timestamp
# extra: eurusd_rate, eurusd_timestamp
```

---

## Patrones a seguir al modificar

### Añadir un nuevo campo de datos a un servicio
1. Añadir la clave en `_ensure_cache_keys()` (sufijo nuevo) o `_build_cache()`
2. Rellenarla en el método `_fetch_*()` correspondiente
3. Leerla en `_update_display()` con `market.get('key')` o `cmc.get('key')`

### Añadir un nuevo widget a un chart block
1. Crearlo en `_make_chart_block()`, añadirlo al `refs` dict
2. Si recibe tinte dinámico → añadir su key en `_apply_block_tint()`
3. Actualizarlo en `_update_display()` con `refs['key'].config(...)`

### Cambiar un color o fuente
→ Editar **solo** `theme.py`. Los demás archivos importan por referencia.

### Añadir un campo a config.yaml
1. Default en `_default_config()` en `main.py`
2. Getter en `ConfigManager` si los servicios lo necesitan
3. Documentar en `config.example.yaml`

### Añadir una ruta a la webapp Flask
1. Crear / editar blueprint en `app-config/api/`
2. Registrar en `app-config/server.py` si es un archivo nuevo
3. Consumir desde `app-config/static/index.html`

### Modificar changelog
1. Analizar la ultima entrada del changelog
2. Añadir una nueva con lo faltante

---

## Comandos útiles

```bash
# Dashboard en modo desarrollo (ventana, datos reales)
# Requiere config.yaml con: environment: test, display.fullscreen: false
python src/main.py

# Webapp de configuración
python app-config/server.py
# → http://localhost:5001

# Limpiar __pycache__ antes de copiar al servidor
bash scripts/clean_pycache.sh
```

---

## Lo que NO hacer

- No hardcodear colores ni fuentes fuera de `theme.py`
- No acceder a `service._cache` directamente — usar `.get_data()`
- No usar `time.sleep()` en el hilo de Tkinter — usar `.after(ms, callback)`
- No llamar `tk.mainloop()` explícitamente — lo gestiona `App.mainloop()`
- No hacer `import *` — todos los imports son explícitos

---

## Normas de git para Claude

- **Nunca hacer commit ni push de forma autónoma.** Siempre mostrar los cambios al usuario
  y esperar confirmación explícita antes de cualquier operación git.
- **Para subir cambios**, el usuario invocará `/actualiza-master` o pedirá expresamente
  el push. No ejecutar comandos git por iniciativa propia aunque el trabajo esté terminado.
- **No añadir `Co-Authored-By`** ni `Co-authored-by` en ningún mensaje de commit.
