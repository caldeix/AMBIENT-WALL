# CHANGELOG — Crypto Wall Dashboard

---

## [1.2.0] — 2026-04-10

### Config por entornos, modo mockup, cryptos dinámicas desde YAML, CMC rank y limpieza de código.

#### Nuevas funcionalidades

- **Entornos de ejecución (`environment`):** nuevo campo en `config.yaml` con tres valores:
  - `mockup` — sin llamadas a la API de CoinMarketCap; la cache se rellena con precios
    inventados realistas (con jitter por ciclo para simular movimiento). Ideal para desarrollo
    sin gastar créditos de API.
  - `test` — llamadas reales pero con configuración de desarrollo.
  - `pro` — producción completa (Raspberry Pi, fullscreen, sin cursor).

- **Cryptos configurables desde YAML:** la lista de símbolos se lee de
  `config.yaml → cryptos.symbols`. Añadir o quitar una moneda ya no requiere tocar código.
  La cache de `CoinMarketCapService` se genera automáticamente a partir de los símbolos
  configurados usando dict comprehension.

- **CMC Rank visible:** cada crypto muestra su posición en CoinMarketCap: `#1 BTC`,
  `#2 ETH`, `#5 SOL`. El rank se obtiene del campo `cmc_rank` de la API y se actualiza
  en cada ciclo de refresco. Mientras no llega el primer dato, el label muestra el símbolo limpio.

- **Rejilla de altcoins dinámica:** `market_panel.py` construye la rejilla inferior en tiempo
  de ejecución según los símbolos del config (excluye BTC y ETH, que van en bloques con gráfica).
  3 columnas fijas, filas calculadas automáticamente. Sin referencias hardcodeadas por moneda.

- **Decimales automáticos:** los precios de altcoins usan `_auto_decimals(price)` para
  determinar los decimales según la magnitud del precio: ≥$100 → 2, ≥$0.01 → 4, <$0.01 → 6.

- **Script de limpieza:** `scripts/clean_pycache.sh` elimina todos los `__pycache__/`,
  `.pyc` y `.pyo` del árbol del proyecto. Usar antes de copiar al servidor.

#### Nuevo rumbo de diseño

- **Layout simplificado a panel único:** se abandona el grid 4-cajones (reloj/tiempo,
  mercados, nodo DePIN, noticias RSS) en favor de una sola pantalla centrada en datos
  financieros. El nuevo layout es:
  - **Top bar (5%):** una línea con hora, fecha y resumen del tiempo actual (temperatura +
    condición). Sin panel de reloj independiente, sin ASCII art, sin viento ni humedad.
  - **Market panel (95%):** ocupa casi toda la pantalla. Fila 1: BTC, ETH, Oro con
    sparkline. Fila 2: S&P500, Plata, IBEX35 con sparkline. Fila 3+: rejilla de altcoins
    dinámica 3 columnas.
- **Eliminados:** panel de reloj/tiempo grande (`clock_weather_panel`), panel DePIN
  (`placeholder_panel`), ticker de noticias (`news_panel`, `rss.py`). El foco del
  dashboard es exclusivamente mercados y precios en tiempo real.

#### Cambios en configuración

- Nuevo campo `environment: pro` en `config.yaml` y `config.example.yaml`.
- Nueva sección `cryptos.symbols` con la lista de monedas a mostrar.
- Claves de refresco renombradas para ser más descriptivas:
  - `btc_price` → `cryptos` (aplica a todas las cryptos, no solo BTC)
  - `btc_chart` → `charts`
  - `gold` + `sp500` unificados en `market` (mismo intervalo para todos los activos de Yahoo Finance)
  - `weather` sin cambios.

#### Cambios en servicios

- `CoinMarketCapService`:
  - Constructor recibe `symbols` (lista) y `environment` en lugar de tenerlos hardcodeados.
  - `SYMBOLS` eliminado como constante de clase; los símbolos viven en `self.symbols`.
  - Cache generada dinámicamente: `{sym_price, sym_change_24h, sym_rank}` × N símbolos.
  - `_fetch_mockup()`: rellena la cache desde `_MOCKUP` dict con jitter aleatorio ±0.5%.
  - `_fetch_real()`: separado de `_fetch_mockup()` con lógica limpia; el parámetro `aux`
    simplificado a solo `cmc_rank` (se eliminaron los campos de volumen no utilizados).
  - Campos eliminados del cache: `is_stale`, `consecutive_failures` (no se leían en ningún sitio).

- `MarketDataService`:
  - Constructor simplificado: `interval_charts` e `interval_market` en lugar de tres parámetros.
  - `_run_gold` + `_run_sp500` fusionados en un único thread `_run_market`.

#### Limpieza de código

- Eliminados archivos sin uso: `src/clock/clock.py`, `src/ui/widgets/placeholder_panel.py`,
  `src/ui/widgets/clock_weather_panel.py`.
- Eliminada función `fmt_change()` de `formatting.py` (importada pero nunca llamada).
- Eliminado dict `WEATHER_EMOJI` de `weather.py` (nunca referenciado).
- Eliminados `_fetch_art()`, `art_text` de `weather.py` (solo usados por `clock_weather_panel`,
  que fue eliminado).
- Eliminados `display.width`, `display.height` y `refresh.news` de `config.example.yaml`.
- Corregido docstring de `CoinMarketCapService` (mencionaba XRP, que no estaba en SYMBOLS).
- Corregido log en `_fetch` que referenciaba `xrp_price` (moneda eliminada).

---

## [1.2.1] — 2026-04-10

### Ciudad del tiempo configurable desde config.yaml.

#### Cambios

- **`weather.city` en config:** la ciudad para el servicio meteorológico pasa de estar
  hardcodeada en `main.py` (`city="Barcelona"`) a leerse de `config.yaml → weather.city`.
  Valor por defecto: `Barcelona`. Cualquier ciudad soportada por wttr.in es válida.

  ```yaml
  weather:
    city: "Barcelona"   # Cambiar por tu ciudad
  ```

- `_default_config()` actualizado para incluir la sección `weather`.
- `WeatherService` no cambia; el parámetro `city` ya existía en el constructor.

---

## [1.1.0] — 2026-03-08

### Nuevos activos, rediseno del panel de tiempo, layout 3+1 y mejoras visuales.

#### Nuevas funcionalidades

- **Layout 3+1:** grid rediseñado de 2×2 a 3 columnas superiores + barra de noticias a ancho
  completo en la fila inferior. Pesos de fila: superior `weight=2`, inferior `weight=1`.
  Orden de cajones: Hora/Tiempo | Mercados | Nodo DePIN — Noticias (fila completa).

- **Nuevas criptomonedas:** DOT (Polkadot), POPCAT, WIF (dogwifhat), ALI y AURA añadidos
  al panel de mercados. Todos muestran precio USD y EUR al lado. Precio obtenido en la misma
  llamada al servicio CoinMarketCap (sin peticiones adicionales).
  - Monedas de bajo precio (POPCAT, WIF, ALI, AURA) muestran 4 decimales.
  - La API CMC puede devolver array cuando hay varios tokens con el mismo símbolo; el servicio
    toma el primero (mayor market cap) de forma segura.

- **ETH, SOL, XRP:** precios integrados en `CoinMarketCapService` (misma llamada que BTC).
  Aparecen en el panel de mercados con precio USD + EUR.

- **Panel Hora & Tiempo rediseñado (`clock_weather_panel.py`):**
  - Icono Unicode del tiempo a tamaño grande (28px): `☀ ⛅ ☁ ☂ ❄ ⛈`.
  - Flecha de dirección del viento (`↑ ↓ ← → ↖ ↗ ↘ ↙`) obtenida del campo
    `winddir16Point` de wttr.in, con código de punto cardinal entre paréntesis.
  - Layout vertical con espaciadores flexibles: reloj centrado verticalmente en su mitad.
  - Sección meteorológica reorganizada: icono + temperatura + sensación en fila superior,
    descripción, viento con flecha, humedad en filas separadas.

- **Panel Mercados — activos tradicionales con precio EUR:**
  - Plata (SI=F) añadida debajo del Oro con precio USD + EUR/oz.
  - IBEX35 (^IBEX) añadido debajo del S&P500 con precio en pts.
  - Todos los activos (Oro, Plata, S&P500, IBEX35) muestran EUR al lado mediante
    conversión EUR/USD obtenida de Yahoo Finance (`EURUSD=X`).

- **Feed de noticias RSS (`news_panel.py`, `rss.py`):**
  - Cajon inferior a ancho completo mostrando noticias de Cointelegraph y CoinDesk.
  - Rotación automática cada 6 segundos. Títulos completos con `wraplength` para 2 líneas.
  - Fuente: `feedparser` + `requests` (timeout controlado de 8s). Intervalo de refresco: 30min.

#### Cambios en servicios

- `CoinMarketCapService`: `SYMBOLS` ampliado a 9 monedas. Loop de parseo robusto:
  maneja respuestas en array de CMC y errores por símbolo sin romper el fetch completo.
- `MarketDataService`: añadidos `silver_price` (SI=F), `ibex_price` (^IBEX),
  `eurusd_rate` (EURUSD=X).
- `WeatherService`: nuevo campo `wind_dir` (`winddir16Point`) en la cache.

#### Correcciones

- **Fullscreen Linux:** reemplazado `overrideredirect(True) + geometry()` por
  `attributes("-fullscreen", True) + wm_attributes('-type', 'splash')` para evitar
  el offset de posición del window manager en LXDE/X11.
- **Crontab autostart:** eliminado `source venv/bin/activate` (no funciona en `/bin/sh`).
  Usar ruta absoluta al Python del virtualenv: `/home/crypto-wall/venv/bin/python`.
- **`fmt_eur(value, 0)`:** corregido `IndexError` al formatear valores sin decimales
  (el `split('.')` sobre `f"{n:,.0f}"` no genera parte decimal).
- **RSS timeout:** `feedparser.parse(url)` podía colgar indefinidamente. Corregido
  usando `requests.get(url, timeout=8)` primero y pasando `resp.content` a feedparser.

---

## [1.0.0] — 2026-03-07

### Primera version estable. App completa y funcional para Raspberry Pi 4 con pantalla 1024x600.

---

## Descripcion general

Dashboard de pared para pantalla permanente (Raspberry Pi 4). Muestra en tiempo real
cuatro bloques de informacion (cajones) en un grid 2x2 que ocupa la pantalla completa.
Modo kiosk sin decoraciones de ventana, sin cursor, sin barra de tareas.

---

## Arquitectura

```
crypto_wall/
├── config.yaml                         # Configuracion central (intervalos, API keys, pantalla)
├── requirements.txt                    # Dependencias Python
├── CHANGELOG.md
└── src/
    ├── main.py                         # Punto de entrada
    ├── clock/
    │   └── clock.py                    # Prototipo standalone del reloj (referencia)
    ├── services/
    │   ├── coinmarketcap.py            # BTC/ETH/SOL/XRP/DOT/POPCAT/WIF/ALI/AURA (CMC API)
    │   ├── market_data.py              # Historial BTC 7d + Oro + Plata + S&P500 + IBEX35 + EUR/USD
    │   ├── weather.py                  # Tiempo meteorologico Barcelona (wttr.in)
    │   └── rss.py                      # Noticias cripto RSS (Cointelegraph + CoinDesk)
    ├── ui/
    │   ├── app.py                      # Ventana principal, grid 3+1, fullscreen
    │   ├── theme.py                    # Colores y fuentes centralizados
    │   └── widgets/
    │       ├── market_panel.py         # Cajon 2: mercados (cryptos + commodities)
    │       ├── clock_weather_panel.py  # Cajon 1: reloj + meteorologia con iconos Unicode
    │       ├── news_panel.py           # Cajon 4 (fila completa): noticias RSS rotativas
    │       └── placeholder_panel.py   # Cajon 3: DePIN (placeholder)
    └── utils/
        └── formatting.py              # Formateo numerico y colores de frescura
```

---

## Patron de datos: daemon threads + cache + polling UI

Todos los servicios de red siguen el mismo patron:

1. **Daemon thread** independiente hace la peticion HTTP cada N segundos.
2. El resultado se guarda en un **dict en memoria** protegido por `threading.Lock`.
3. La UI **nunca bloquea el hilo principal**: usa `widget.after(N, callback)` de Tkinter
   para leer la cache periodicamente y actualizar los labels.
4. Si una peticion falla, la cache conserva el ultimo dato valido y se marca `is_stale=True`.

Esto garantiza que la UI nunca se congela por latencia de red.

---

## Componentes

### `config.yaml`

Archivo de configuracion central en la raiz del proyecto.

```yaml
display:
  fullscreen: true       # true en produccion (Raspberry Pi)
  hide_cursor: false     # true en produccion (sin raton)

api_keys:
  coinmarketcap: "..."   # API key gratuita de CoinMarketCap

refresh:
  btc_price: 300         # segundos — CoinMarketCap (5 min)
  btc_chart: 300         # segundos — Yahoo Finance sparkline (5 min)
  gold:      1800        # segundos — Yahoo Finance oro (30 min)
  sp500:     1800        # segundos — Yahoo Finance S&P500 (30 min)
  weather:   1800        # segundos — wttr.in Barcelona (30 min)

logging:
  level: "INFO"
  file: "app.log"
  max_bytes: 5242880     # 5 MB
  backup_count: 3
```

Intervalo minimo permitido: 60 segundos. Si se configura menos, `main.py` lo fuerza a 60s
y registra un warning en el log.

---

### `src/main.py` — Punto de entrada

1. Busca `config.yaml` un nivel arriba de `src/` (`os.path.dirname(__file__)/../`).
2. Si no existe, usa valores por defecto hardcodeados.
3. Configura logging con `RotatingFileHandler` (archivo `app.log`) y salida a consola.
4. Valida que ningun intervalo sea menor de 60s.
5. Instancia los tres servicios de datos y llama a `.start()` en cada uno.
6. Crea la ventana `App` y entra en el mainloop de Tkinter (bloquea hasta cierre).
7. Si `config.yaml` tiene un error de sintaxis, muestra una ventana de error en pantalla
   en lugar de un traceback en consola.

---

### `src/ui/app.py` — Ventana principal

Subclase de `tk.Tk`. Configura el grid 2x2 y el modo fullscreen.

**Grid 2x2:**
```
┌─────────────────┬─────────────────┐
│  Cajon 1        │  Cajon 2        │
│  MERCADOS       │  NODO DePIN     │
│  (MarketPanel)  │  (Placeholder)  │
├─────────────────┼─────────────────┤
│  Cajon 3        │  Cajon 4        │
│  NOTICIAS       │  HORA & TIEMPO  │
│  (Placeholder)  │  (ClockWeather) │
└─────────────────┴─────────────────┘
```

Cada columna y fila tiene `weight=1, uniform='col'/'row'` para que los cuatro cajones
ocupen exactamente el mismo espacio independientemente de la resolucion.

**Fullscreen Linux (modo kiosk):**

```python
self.attributes("-fullscreen", True)
self.wm_attributes('-type', 'splash')
```

`-type splash` elimina las decoraciones del window manager (barra de titulo, bordes)
sin usar `overrideredirect`, que en LXDE/X11 causaba un offset de posicion.
`-fullscreen True` delega la geometria al WM, que la ajusta a la resolucion real.

**Fullscreen Windows (desarrollo):**
```python
self.overrideredirect(True)
self.state('zoomed')
```

Teclas de debug: `Escape` cierra la app, `F11` alterna fullscreen.

---

### `src/services/coinmarketcap.py` — Precio BTC

- **Endpoint:** `https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=BTC&convert=USD`
- **Intervalo:** configurable, minimo 60s, por defecto 300s (5 min).
- **Jitter inicial:** espera aleatoria 0-15s al arrancar para no sincronizar con otros servicios.
- **Manejo de errores:**
  - HTTP 429 (rate limit): mantiene cache, registra warning, no cuenta como fallo.
  - Timeout (>10s): mantiene cache, incrementa `consecutive_failures`.
  - Cualquier otro error: registra en log, mantiene ultimo dato valido.
- **Cache:**
  ```python
  {
    'btc_price': float,          # precio en USD
    'btc_change_24h': float,     # variacion porcentual 24h
    'timestamp': float,          # epoch del ultimo fetch exitoso
    'is_stale': bool,            # True si el ultimo intento fallo
    'error': str | None,
    'consecutive_failures': int,
  }
  ```

---

### `src/services/market_data.py` — Oro + S&P500 + Historial BTC

Usa **yfinance** (Yahoo Finance, sin API key). Tres daemon threads completamente independientes:

| Thread        | Ticker  | Dato                              | Intervalo default |
|---------------|---------|-----------------------------------|--------------------|
| `svc-btc-chart` | BTC-USD | Historial 7d intervalo 1h (sparkline) | 300s (5 min)   |
| `svc-gold`    | GC=F    | Precio ultimo cierre Gold Futures | 1800s (30 min)     |
| `svc-sp500`   | ^GSPC   | Precio ultimo cierre S&P 500      | 1800s (30 min)     |

Cada thread tiene un **jitter inicial diferente** (5-20s, 10-40s, 15-45s) para escalonar
las peticiones a Yahoo Finance al arrancar.

El historial BTC se limita a 168 puntos maximo (una semana en horas). Si hay mas puntos
(por ejemplo si Yahoo devuelve intervalos de 30min), se submuestrea con `prices[::step]`.

---

### `src/services/weather.py` — Meteorologia Barcelona

- **Fuente:** `https://wttr.in/Barcelona?format=j1` (gratuito, sin API key).
- **Intervalo:** configurable, minimo 300s, por defecto 1800s (30 min).
- **Jitter inicial:** 2-10s.
- **Datos que extrae de la API:**
  - `temp_C` → temperatura actual en grados Celsius (entero)
  - `FeelsLikeC` → sensacion termica
  - `humidity` → humedad relativa %
  - `windspeedKmph` → velocidad del viento km/h
  - `weatherCode` → codigo numerico del estado (113=despejado, 116=parcialmente nublado, etc.)
- Los codigos numericos se mapean a descripciones en español (`WEATHER_DESC`) y a iconos
  de texto corto para el panel (`SOL`, `NUBLADO`, `LLUVIA`, `TORMENTA`, etc.).

---

### `src/ui/widgets/market_panel.py` — Cajon 1: MERCADOS

Polling cada **5 segundos** sobre la cache de `CoinMarketCapService` y `MarketDataService`.

**Contenido:**
- **BTC:** precio en formato español (`$67.234,12`) + flecha de variacion 24h coloreada
  (verde `▲` / rojo `▼`).
- **Sparkline 7 dias:** grafico de linea Matplotlib embebido en Tkinter via
  `FigureCanvasTkAgg`. La figura se reutiliza entre actualizaciones (no se recrea),
  solo se llama a `ax.clear()` + `canvas.draw_idle()`. Incluye area sombreada bajo la linea.
  Si matplotlib no esta instalado, muestra un mensaje de aviso en su lugar.
- **Fechas del grafico:** etiquetas inicio/fin del periodo debajo del sparkline.
- **Oro (GC=F):** precio en USD por onza troy (`$2.051,30 /oz`).
- **S&P 500 (^GSPC):** precio en puntos (`5.102,45 pts`) + indicador "Mercado cerrado"
  fuera del horario NYSE (lunes-viernes 14:30-21:00 CET / 15:30-22:00 CEST).
- **Indicador de frescura:** punto de color en el header que cambia segun la antiguedad del dato:
  - Verde: dato dentro del intervalo esperado (< 1.5x el intervalo)
  - Amarillo: un ciclo perdido (1.5x - 2.5x el intervalo)
  - Rojo: dato muy antiguo o sin conexion (> 2.5x el intervalo)

---

### `src/ui/widgets/clock_weather_panel.py` — Cajon 4: HORA & TIEMPO

**Reloj digital:**
- Se actualiza cada **1 segundo** via `self.after(1000, self._tick)`.
- Muestra HH:MM en fuente grande (Courier 52px) y :SS en fuente menor (Courier 22px).
- Fecha completa en español: "Sabado, 7 de marzo de 2026".

**Meteorologia:**
- Al arrancar, hace polling cada **5 segundos** hasta obtener el primer dato del servicio.
- Una vez recibido el primer dato, el polling pasa a **60 segundos**.
- Muestra: temperatura (°C), icono de texto (SOL / LLUVIA / etc.), descripcion en español,
  humedad, velocidad del viento y sensacion termica.
- Indicador de frescura igual que el panel de mercados (verde/amarillo/rojo).

---

### `src/ui/widgets/placeholder_panel.py` — Cajones 2 y 3

Paneles estaticos que muestran titulo, color de acento y lista de lineas de texto.
Preparados para ser reemplazados en fases futuras:
- **Cajon 2** (NODO DePIN): futuro monitor del nodo Filecoin/Storj.
- **Cajon 3** (NOTICIAS CRIPTO): futuro feed RSS (Cointelegraph, CoinDesk).

---

### `src/ui/theme.py` — Tema visual

Paleta oscura, estilo ambient display:

| Constante        | Valor     | Uso                          |
|------------------|-----------|------------------------------|
| `BG_GLOBAL`      | `#0a0a1a` | Fondo de la ventana raiz     |
| `BG_PANEL`       | `#0f0f23` | Fondo de cada cajon          |
| `BORDER`         | `#1a1a2e` | Separadores y bordes         |
| `TEXT_PRIMARY`   | `#e0e0e0` | Texto principal (precios)    |
| `TEXT_SECONDARY` | `#8888aa` | Texto secundario (labels)    |
| `ACCENT_MARKET`  | `#00d4ff` | Cian — Cajon 1               |
| `ACCENT_NODE`    | `#00ff88` | Verde menta — Cajon 2        |
| `ACCENT_NEWS`    | `#ffaa00` | Naranja dorado — Cajon 3     |
| `ACCENT_CLOCK`   | `#7777bb` | Violeta suave — Cajon 4      |
| `POSITIVE`       | `#00ff88` | Variacion positiva           |
| `NEGATIVE`       | `#ff4466` | Variacion negativa           |
| `ERROR`          | `#ff2244` | Error / dato no disponible   |

---

### `src/utils/formatting.py` — Formateo

| Funcion           | Descripcion                                              |
|-------------------|----------------------------------------------------------|
| `fmt_usd(v)`      | Formato español: `$67.234,12` (punto miles, coma decimal)|
| `fmt_change(v)`   | Retorna `(texto, color)`: `"▲ +2,34%"` en verde          |
| `fmt_gold(v)`     | Anade `/oz` al precio del oro                            |
| `fmt_sp500(v)`    | Anade ` pts` al indice                                   |
| `time_ago(ts)`    | Tiempo desde timestamp: `"5m"`, `"2h"`, `"30s"`         |
| `freshness_color` | Color verde/amarillo/rojo segun antiguedad relativa      |

---

## Dependencias

| Paquete      | Version minima | Uso                                      |
|--------------|----------------|------------------------------------------|
| `requests`   | 2.31.0         | HTTP para CoinMarketCap y wttr.in        |
| `matplotlib` | 3.7.0          | Sparkline BTC embebido en Tkinter        |
| `yfinance`   | 0.2.40         | Historial BTC, precio Oro, S&P500        |
| `pyyaml`     | 6.0            | Lectura de config.yaml                   |
| `tkinter`    | stdlib         | UI (incluido en Python estandar)         |

---

## Instalacion en Raspberry Pi OS (Bookworm)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Autoarranque via crontab:
```
@reboot sleep 15 && DISPLAY=:0 /home/crypto-wall/venv/bin/python /home/crypto-wall/src/main.py
```

Resolucion 1024x600 en `/boot/config.txt`:
```
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0
```

---

## Fases pendientes

| Fase | Descripcion                                           |
|------|-------------------------------------------------------|
| 6    | Feed RSS en Cajon 3 (feedparser, rotacion automatica) |
| 7    | Monitor DePIN mock en Cajon 2 (Filecoin / Storj)      |
| 8    | Test de estabilidad 72h en hardware real              |
