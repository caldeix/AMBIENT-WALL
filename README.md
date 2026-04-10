# Crypto Wall Dashboard

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%204-red?logo=raspberry-pi&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Last update](https://img.shields.io/badge/last%20update-2026--04--10-lightgrey)

> Dashboard de pared en tiempo real para Raspberry Pi 4 con pantalla 1024x768.
> Cryptos, mercados tradicionales y meteorología en modo kiosk fullscreen.

---

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│  14:35:22   Sábado, 10 de abril de 2026   ☀ 22°C Barcelona  │  ← Top bar (5%)
├──────────────────┬──────────────────┬──────────────────────┤
│  #1 BTC          │  #2 ETH          │  ORO                 │
│  $73.234,12      │  $3.480,50       │  $2.321,40 /oz       │
│  ▲ 1,36%         │  ▲ 2,10%         │  ▲ 0,42%             │
│  [sparkline 7d]  │  [sparkline 7d]  │  [sparkline 1mo]     │
├──────────────────┼──────────────────┼──────────────────────┤
│  S&P500          │  PLATA           │  IBEX35              │
│  5.102,45 pts    │  $32,10 /oz      │  11.234 pts          │
│  ▼ 0,18%         │  ▲ 0,80%         │  ▲ 1,12%             │
│  [sparkline 1mo] │  [sparkline 1mo] │  [sparkline 1mo]     │
├──────────────────┴──────────────────┴──────────────────────┤
│  #5 SOL  $178,50  (€165,28)   │  #55 JUP  $0,7500  (€0,6944) │  #14 DOT  $8,20  (€7,59)   │
│  #65 WIF  $2,1000 (€1,9444)   │  #110 STRK $0,3800 (€0,3519) │  #180 POPCAT $0,4200 ...   │
│  #95 ALI  $0,0180 (€0,0167)   │  #150 ROSE $0,0550 (€0,0509) │  #210 GPU  $0,0950 ...     │
│  #190 RAIL $1,2000 (€1,1111)  │  #320 AURA $0,0035 (€0,0032) │  #450 HSUITE $0,0082 ...  │
└────────────────────────────────────────────────────────────┘
```

---

## Características

- **Cryptos configurables** desde `config.yaml` — sin tocar código. Añade o quita símbolos y reinicia.
- **CMC Rank** visible en cada crypto: `#1 BTC`, `#2 ETH`, `#5 SOL`...
- **6 bloques con sparkline** (Matplotlib): BTC 7d, ETH 7d, Oro 1mo, S&P500 1mo, Plata 1mo, IBEX35 1mo
- **Precios en USD y EUR** para todas las cryptos (conversión via EUR/USD de Yahoo Finance)
- **3 entornos**: `mockup` (sin API, datos inventados), `test`, `pro`
- **Modo kiosk**: fullscreen sin cursor ni barra de tareas — Linux y Windows
- **Sin bloqueos**: daemon threads + cache en memoria + polling Tkinter

---

## Arquitectura

```
crypto_wall/
├── config.example.yaml         # Plantilla — copiar a config.yaml
├── config.yaml                 # Tu configuracion real (en .gitignore)
├── requirements.txt
└── src/
    ├── main.py                 # Punto de entrada
    ├── services/
    │   ├── coinmarketcap.py    # Precios + rank via CMC API (dinamico + mockup)
    │   ├── market_data.py      # Sparklines BTC/ETH + Oro/Plata/SP500/IBEX (Yahoo Finance)
    │   └── weather.py          # Meteorologia Barcelona (wttr.in, sin API key)
    ├── ui/
    │   ├── app.py              # Ventana principal, layout, fullscreen
    │   ├── theme.py            # Paleta oscura y fuentes centralizadas
    │   └── widgets/
    │       ├── top_bar.py      # Barra superior: hora, fecha, resumen del tiempo
    │       └── market_panel.py # Bloques de grafica + rejilla altcoins dinamica
    └── utils/
        └── formatting.py       # Formatos numericos en locale espanol
```

### Patrón de datos

```
Daemon thread  →  fetch HTTP  →  cache (Lock)  →  Tkinter after()  →  UI labels
```

1. Cada servicio corre en un **daemon thread** independiente.
2. Los datos se guardan en un **dict en memoria** protegido por `threading.Lock`.
3. La UI usa `widget.after(N, callback)` para leer la cache sin bloquear el hilo principal.
4. Si una petición falla, la cache conserva el último dato válido.

---

## Instalación

### Requisitos

- Python 3.11+
- Raspberry Pi 4 (o cualquier Linux/Windows con pantalla)
- API key gratuita de [CoinMarketCap](https://coinmarketcap.com/api/) *(no necesaria en modo mockup)*

### Pasos

```bash
git clone <repo-url>
cd crypto_wall

python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

pip install -r requirements.txt

cp config.example.yaml config.yaml
# Editar config.yaml y ajustar entorno, API key y symbols
```

### Ejecutar

```bash
python src/main.py                        # Windows / desarrollo
DISPLAY=:0 python src/main.py             # Linux con display X11
```

### Autoarranque en Raspberry Pi

```
# crontab -e
@reboot sleep 15 &&  DISPLAY=:0 XAUTHORITY=/home/{{user}}/.Xauthority /home/crypto-wall/venv/bin/python /home/crypto-wall/src/main.py
```

> Usar siempre la ruta absoluta al Python del virtualenv. `source venv/bin/activate` no funciona en crontab (`/bin/sh`).

### Resolución 1024×600 en `/boot/config.txt`

```ini
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0
```

---

## Configuración (`config.yaml`)

```yaml
# ---------------------------------------------------------------------------
# Entorno
# ---------------------------------------------------------------------------
environment: pro          # mockup | test | pro
                          # mockup → datos inventados para CMC (sin API key ni llamadas)
                          # test   → llamadas reales, fullscreen desactivado en pantalla
                          # pro    → produccion completa (Raspberry Pi, kiosk)

# ---------------------------------------------------------------------------
# Pantalla
# ---------------------------------------------------------------------------
display:
  fullscreen: true        # true en produccion
  hide_cursor: true       # true en produccion (sin raton)
  sim_resolution: 1024x768  # opcional — simula resolucion en modo ventana (desarrollo)

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
api_keys:
  coinmarketcap: "TU_API_KEY"   # Plan gratuito de CoinMarketCap es suficiente
                                 # No necesaria si environment: mockup

# ---------------------------------------------------------------------------
# Cryptos a mostrar
# ---------------------------------------------------------------------------
cryptos:
  symbols:              # Orden de aparicion en pantalla
    - BTC               # BTC y ETH siempre en los bloques superiores con grafica
    - ETH
    - SOL               # El resto aparecen en la rejilla de altcoins (3 columnas)
    - DOT
    - POPCAT
    # ... anadir o quitar symbols aqui. Sin tocar codigo.

# ---------------------------------------------------------------------------
# Intervalos de refresco (segundos, minimo 60)
# ---------------------------------------------------------------------------
refresh:
  cryptos: 300          #  5 min — CoinMarketCap (precios + rank)
  charts:  300          #  5 min — Yahoo Finance (sparklines BTC/ETH)
  market:  1800         # 30 min — Yahoo Finance (Oro, Plata, S&P500, IBEX35, EUR/USD)
  weather: 1800         # 30 min — wttr.in Barcelona

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging:
  level: "INFO"         # DEBUG | INFO | WARNING | ERROR
  file: "app.log"       # rotativo, se crea en el directorio de trabajo
  max_bytes: 5242880    # 5 MB por fichero
  backup_count: 3       # maximos 3 ficheros de backup
```

> `config.yaml` está en `.gitignore` — **nunca commitear la API key**.

---

## Referencia de servicios

### `CoinMarketCapService`

- **Endpoint:** `GET /v1/cryptocurrency/quotes/latest`
- **Símbolos:** leídos de `config.yaml → cryptos.symbols`
- **Cache dinámica:** se genera automáticamente al instanciar el servicio según los símbolos configurados. No hay código hardcodeado por moneda.
- **Mockup:** en `environment: mockup` rellena la cache con datos inventados (jitter pequeño en cada ciclo para simular movimiento) sin hacer ninguna llamada a la API.
- **Errores:** HTTP 429 mantiene cache sin marcar fallo; timeout y errores generales mantienen el último dato válido y registran en log.

### `MarketDataService`

Dos threads paralelos via **yfinance** (Yahoo Finance, sin API key):

| Thread | Qué obtiene | Intervalo |
|---|---|---|
| `svc-charts` | Historial BTC 7d + ETH 7d (sparklines) | `refresh.charts` |
| `svc-market` | Oro, Plata, S&P500, IBEX35, EUR/USD | `refresh.market` |

### `WeatherService`

- **Fuente:** `https://wttr.in/Barcelona?format=j1` (gratuito, sin API key)
- Extrae: temperatura, sensación térmica, humedad, viento (km/h + dirección cardinal), código de condición
- Los códigos numéricos de wttr.in se mapean a descripciones en español (`WEATHER_DESC`)

---

## Tema visual

Paleta oscura estilo ambient display:

| Constante | Color | Uso |
|---|---|---|
| `BG_GLOBAL` | `#0a0a1a` | Fondo ventana raíz |
| `BG_PANEL` | `#0f0f23` | Fondo paneles |
| `BORDER` | `#1a1a2e` | Separadores |
| `TEXT_PRIMARY` | `#e0e0e0` | Precios y valores |
| `TEXT_SECONDARY` | `#8888aa` | Labels y metadatos |
| `ACCENT_MARKET` | `#00d4ff` | Cian — sparklines |
| `POSITIVE` | `#00ff88` | Variación positiva |
| `NEGATIVE` | `#ff4466` | Variación negativa |
| `ERROR` | `#ff2244` | Dato no disponible |

---

## Dependencias

| Paquete | Versión mín. | Uso |
|---|---|---|
| `requests` | 2.31.0 | HTTP para CoinMarketCap y wttr.in |
| `yfinance` | 0.2.40 | Historial y precios Yahoo Finance |
| `matplotlib` | 3.7.0 | Sparklines embebidos en Tkinter |
| `pyyaml` | 6.0 | Lectura de config.yaml |
| `tkinter` | stdlib | UI (incluido en Python estándar) |

---

## Scripts de utilidad

```bash
# Limpiar __pycache__ antes de copiar/subir al servidor
bash scripts/clean_pycache.sh
```

---

## Atajos de teclado (desarrollo)

| Tecla | Acción |
|---|---|
| `Escape` | Cierra la aplicación |
| `F11` | Alterna fullscreen |


## Créditos IA

Este proyecto fue diseñado e implementado íntegramente con asistencia de IA:

> 🤖 Built with **[Claude Code](https://claude.ai/code)** — *Claude Sonnet 4.6* by Anthropic
> Arquitectura, servicios, widgets, formateo, layout y documentación generados en sesiones
> de pair-programming con Claude Code en el IDE.

---

*Crypto Wall Dashboard — ambient display para hodlers 24/7*
