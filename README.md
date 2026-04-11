# Crypto Wall Dashboard

![Version](https://img.shields.io/badge/version-1.3.1-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%204-red?logo=raspberry-pi&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Last update](https://img.shields.io/badge/last%20update-2026--04--12-lightgrey)

> Tener un ojo en el mercado no debería obligarte a tener el móvil en la mano.
> Crypto Wall convierte una pantalla spare en un ambient display permanente — cryptos,
> materias primas e índices en tiempo real, con estética oscura pensada para quedarse
> encendida 24/7 sin molestar.

![Crypto Wall Dashboard](resources/img/frontwall.png)

---

## Por qué existe esto

La mayoría de dashboards de crypto son webs pensadas para sesiones cortas: abres, miras,
cierras. Crypto Wall tiene el objetivo opuesto: una pantalla que siempre está ahí, en la
pared, legible de un vistazo desde cualquier punto de la habitación.

El caso de uso es simple — una Raspberry Pi 4 con una pantalla de 10" o superior montada
en la pared, arrancando sola al encenderse, sin teclado ni ratón, mostrando en modo kiosk:
precios en vivo con sparklines de 7 días para BTC y ETH, commodities (oro, plata) e índices
(S&P500, IBEX35), y una rejilla de altcoins completamente configurable desde un YAML o desde
una webapp de configuración local.

---

## Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  14:35:22   Sábado, 10 de abril de 2026   ☀ 22°C Barcelona      │  ← Top bar (5%)
├────────────────────┬────────────────────┬───────────────────────┤
│  #1 BTC            │  #2 ETH            │  ORO                  │
│  $73.234,12        │  $3.480,50         │  $2.321,40 /oz        │  ← Fila 1
│  ▲ 1,36%           │  ▲ 2,10%           │  ▲ 0,42%              │    (chart_blocks 1–3)
│  [sparkline 7d]    │  [sparkline 7d]    │  [sparkline 1mo]      │
├────────────────────┼────────────────────┼───────────────────────┤
│  S&P500            │  PLATA             │  IBEX35               │
│  5.102,45 pts      │  $32,10 /oz        │  11.234 pts           │  ← Fila 2
│  ▼ 0,18%           │  ▲ 0,80%           │  ▲ 1,12%              │    (chart_blocks 4–6)
│  [sparkline 1mo]   │  [sparkline 1mo]   │  [sparkline 1mo]      │
├────────────────────┴────────────────────┴───────────────────────┤
│  #5 SOL   $178,50 (€165,28) │ #55 JUP  $0,7500 (€0,6944) │ #14 DOT  $8,20 (€7,59)   │
│  #65 WIF  $2,1000 (€1,9444) │ #110 STRK $0,3800 (€0,3519) │ #180 POPCAT $0,4200 ...  │
│  #95 ALI  $0,0180 (€0,0167) │ #150 ROSE $0,0550 (€0,0509) │ #210 GPU  $0,0950 ...    │
│  #190 RAIL $1,2000          │ #320 AURA $0,0035           │ #450 HSUITE $0,0082 ...  │
└─────────────────────────────────────────────────────────────────┘
```

Cada bloque de las filas 1 y 2 ocupa exactamente **1/3 del ancho**, independientemente de
cuántos bloques estén configurados.

---

## Características

- **Bloques con sparkline configurables** — hasta 6 activos (crypto o mercado) con gráfica
  histórica. Se configuran desde `config.yaml` o desde la webapp de configuración.
- **Rejilla de altcoins dinámica** — cualquier número de cryptos CMC, 3 columnas, definida en `config.yaml`.
- **CMC Rank visible** — cada crypto muestra su posición: `#1 BTC`, `#5 SOL`...
- **Precios en USD y EUR** — conversión automática via EUR/USD de Yahoo Finance.
- **3 entornos** — `mockup` (sin API, datos inventados), `test` (ventana), `pro` (kiosk fullscreen).
- **Hot-reload** — cambios en `config.yaml` se aplican al dashboard sin reiniciar.
- **Webapp de configuración** — UI web local para editar la config, con drag & drop de activos.
- **Modo kiosk** — fullscreen sin cursor ni barra de tareas, Linux y Windows.
- **Sin bloqueos** — daemon threads + cache en memoria + polling Tkinter.

---

## Arquitectura

```
crypto_wall/
├── config.example.yaml          # Plantilla — copiar a config.yaml
├── config.yaml                  # Tu configuracion (en .gitignore)
├── requirements.txt             # Dependencias Python (dashboard + webapp)
├── scripts/
│   ├── install.sh               # Instalacion automatizada Linux/Raspberry Pi
│   ├── install.bat              # Instalacion automatizada Windows
│   └── clean_pycache.sh         # Limpia __pycache__ antes de subir al servidor
├── resources/
│   ├── cmc_map_cache.json       # Cache local del listado CMC (~3000 monedas, TTL 7d)
│   └── img/                     # Imagenes del proyecto
├── shared/
│   └── config_manager.py        # ConfigManager — hot-reload y file watcher compartido
├── app-config/                  # Webapp de configuracion (Flask)
│   ├── server.py                # Punto de entrada Flask (puerto 5001)
│   ├── api/
│   │   ├── config_routes.py     # GET/POST /api/config — lectura y escritura de config.yaml
│   │   ├── cmc_routes.py        # GET /api/cmc/coins — busqueda paginada en cache CMC
│   │   ├── yahoo_routes.py      # GET /api/yahoo/search — busqueda y validacion de tickers
│   │   └── location_routes.py   # GET /api/location — geocodificacion via Nominatim/OSM
│   └── static/
│       └── index.html           # UI de configuracion (Vue-less, Sortable.js, dark theme)
└── src/                         # Dashboard Tkinter
    ├── main.py                  # Punto de entrada
    ├── services/
    │   ├── coinmarketcap.py     # Precios + rank via CMC API (dinamico + mockup)
    │   ├── market_data.py       # Sparklines + precios via Yahoo Finance
    │   └── weather.py           # Meteorologia via wttr.in (sin API key)
    ├── ui/
    │   ├── app.py               # Ventana principal, layout, fullscreen cross-platform
    │   ├── theme.py             # Paleta oscura y fuentes centralizadas
    │   └── widgets/
    │       ├── top_bar.py       # Barra superior: hora, fecha, resumen del tiempo
    │       └── market_panel.py  # Bloques con sparkline + rejilla altcoins dinamica
    └── utils/
        └── formatting.py        # Formatos numericos en locale espanol
```

### Patrón de datos

```
Daemon thread  →  fetch HTTP  →  cache (Lock)  →  Tkinter after()  →  UI labels
```

1. Cada servicio corre en un **daemon thread** independiente.
2. Los datos se guardan en un **dict en memoria** protegido por `threading.Lock`.
3. La UI usa `widget.after(N, callback)` para leer la cache sin bloquear el hilo principal.
4. Si una petición falla, **la cache conserva el último dato válido** — la pantalla nunca se queda en blanco por un error de red puntual.

---

## Instalación

### Opción A — Script automático (recomendado)

```bash
# Linux / Raspberry Pi
bash scripts/install.sh

# Windows
scripts\install.bat
```

El script localiza Python 3, crea el entorno virtual, instala dependencias y crea `config.yaml`
desde la plantilla. Al finalizar imprime las instrucciones para el crontab.

### Opción B — Manual

```bash
git clone <repo-url>
cd crypto_wall

python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
cp config.example.yaml config.yaml
# Editar config.yaml: api key, entorno, symbols
```

---

## Ejecutar

### Dashboard (pantalla principal)

```bash
# Linux con display X11
DISPLAY=:0 venv/bin/python src/main.py

# Windows / desarrollo
venv\Scripts\python src\main.py
```

### Webapp de configuración

```bash
# Linux
DISPLAY=:0 venv/bin/python app-config/server.py

# Windows
venv\Scripts\python app-config\server.py
```

Abre `http://localhost:5001` en el navegador. El dashboard detecta cambios en `config.yaml`
y se actualiza automáticamente (hot-reload).

---

## Autoarranque en Raspberry Pi

```bash
crontab -e
```

Añadir al final:

```
@reboot sleep 15 && DISPLAY=:0 XAUTHORITY=/home/pi/.Xauthority /home/pi/crypto_wall/venv/bin/python /home/pi/crypto_wall/src/main.py >> /home/pi/crypto_wall/src/app.log 2>&1
```

> Usa siempre la ruta absoluta al Python del virtualenv.
> `source venv/bin/activate` no funciona en crontab (`/bin/sh`).

---

## Resolución 1024×768 en Raspberry Pi (`/boot/config.txt`)

```ini
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=16
```

Para resolución personalizada 1024×600 (pantalla 7"):

```ini
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0
```

---

## Configuración (`config.yaml`)

Copia `config.example.yaml` a `config.yaml`. Referencia completa de campos:

| Campo | Tipo | Descripción |
|---|---|---|
| `environment` | `mockup\|test\|pro` | Modo de ejecución. `mockup` = sin llamadas CMC, datos inventados. |
| `display.fullscreen` | bool | `true` en producción (Raspberry Pi). |
| `display.hide_cursor` | bool | `true` en producción (sin ratón). |
| `display.sim_resolution` | `WxH` | Opcional. Simula resolución en modo ventana para desarrollo. |
| `api_keys.coinmarketcap` | string | API key de CoinMarketCap. No necesaria en `mockup`. |
| `weather.city` | string | Ciudad para wttr.in. Ejemplos: `Barcelona`, `Madrid`, `London`. |
| `chart_blocks[]` | lista | Hasta 6 bloques con sparkline. Ver tabla abajo. |
| `cryptos.symbols` | lista | Símbolos CMC para la rejilla de altcoins. |
| `refresh.cryptos` | int (seg) | Intervalo refresco precios CMC. Mínimo 60. |
| `refresh.charts` | int (seg) | Intervalo sparklines BTC/ETH Yahoo Finance. |
| `refresh.market` | int (seg) | Intervalo Oro, Plata, S&P500, IBEX35, EUR/USD. |
| `refresh.weather` | int (seg) | Intervalo meteorología wttr.in. |
| `logging.level` | `DEBUG\|INFO\|WARNING\|ERROR` | Nivel de log. |
| `logging.file` | string | Nombre del fichero de log rotativo. |

### Campos de `chart_blocks`

| Campo | Descripción |
|---|---|
| `label` | Texto del header del bloque (p. ej. `BTC`, `ORO`, `S&P500`). |
| `ticker` | Símbolo de Yahoo Finance (`BTC-USD`, `GC=F`, `^GSPC`, `^IBEX`, `ETH-USD`...). |
| `period` | Periodo del historial: `7d` (semana) o `1mo` (mes). |
| `cmc_symbol` | Símbolo CMC para el precio en tiempo real (`BTC`, `ETH`). `null` para no-cryptos. |
| `format` | Formato del precio: `crypto`, `commodity` (añade `/oz`), `index`, `index_int`. |

---

## Referencia de servicios

### `CoinMarketCapService`

| | |
|---|---|
| Endpoint | `GET /v1/cryptocurrency/quotes/latest` |
| Símbolos | Leídos de `config.yaml → cryptos.symbols` + `chart_blocks[].cmc_symbol` |
| Cache | Generada dinámicamente por símbolo: `{sym}_price`, `{sym}_change_24h`, `{sym}_rank` |
| Mockup | En `environment: mockup`, rellena cache con datos estáticos + jitter aleatorio ±0,5% |
| Rate limit | HTTP 429 → mantiene cache, no cuenta como fallo |
| Timeout | >10s → mantiene cache, registra warning |

### `MarketDataService`

Dos threads paralelos vía **yfinance** (Yahoo Finance, sin API key):

| Thread | Qué obtiene | Intervalo |
|---|---|---|
| `svc-charts` | Historial BTC 7d + ETH 7d (sparklines) | `refresh.charts` |
| `svc-market` | Oro, Plata, S&P500, IBEX35, EUR/USD | `refresh.market` |

### `WeatherService`

- Fuente: `https://wttr.in/{ciudad}?format=j1` (gratuito, sin API key)
- Extrae: temperatura, sensación térmica, humedad, viento, condición
- Códigos numéricos mapeados a descripciones en español

---

## Tema visual

| Constante | Color | Uso |
|---|---|---|
| `BG_GLOBAL` | `#0a0a1a` | Fondo ventana raíz |
| `BG_PANEL` | `#0f0f23` | Fondo paneles |
| `BORDER` | `#1a1a2e` | Separadores |
| `TEXT_PRIMARY` | `#e0e0e0` | Precios y valores |
| `TEXT_SECONDARY` | `#8888aa` | Labels y metadatos |
| `ACCENT_MARKET` | `#00d4ff` | Cian — sparklines |
| `POSITIVE` | `#00ff88` | Variación positiva (▲) |
| `NEGATIVE` | `#ff4466` | Variación negativa (▼) |
| `ERROR` | `#ff2244` | Dato no disponible |

---

## Dependencias

| Paquete | Versión mín. | Uso |
|---|---|---|
| `requests` | 2.31.0 | HTTP para CoinMarketCap y wttr.in |
| `yfinance` | 0.2.40 | Historial y precios Yahoo Finance |
| `matplotlib` | 3.7.0 | Sparklines embebidos en Tkinter |
| `pyyaml` | 6.0 | Lectura y escritura de config.yaml |
| `flask` | 3.0.0 | Webapp de configuración local |
| `tkinter` | stdlib | UI dashboard (incluido en Python) |

---

## Scripts de utilidad

```bash
bash scripts/install.sh          # Instalacion Linux/Raspberry Pi
scripts\install.bat              # Instalacion Windows

bash scripts/clean_pycache.sh    # Limpia __pycache__ antes de copiar al servidor
```

---

## Atajos de teclado (dashboard)

| Tecla | Acción |
|---|---|
| `Escape` | Cierra la aplicación |
| `F11` | Alterna fullscreen |

---

## Autor

**Luis M. Caldeiro**
Proyecto iniciado en marzo de 2026.
