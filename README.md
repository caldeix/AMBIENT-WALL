# Crypto Wall Dashboard

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%204-red?logo=raspberry-pi&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Built with Claude](https://img.shields.io/badge/built%20with-Claude%20Code%20Sonnet%204.6-blueviolet?logo=anthropic)
![Last update](https://img.shields.io/badge/last%20update-2026--03--08-lightgrey)

> Dashboard de pared en tiempo real para Raspberry Pi 4 con pantalla 1024×600.
> Muestra cryptos, mercados tradicionales, meteorología, noticias RSS y reloj en modo kiosk.

---

## Captura de pantalla

```
┌──────────────────┬──────────────────┬──────────────────┐
│  HORA & TIEMPO   │    MERCADOS      │   NODO DePIN     │
│                  │                  │                  │
│  14:35 :22       │  BTC $84.231,00  │  [placeholder]   │
│  Dom, 8 marzo    │  [sparkline 7d]  │                  │
│                  │  ETH  $2.100,00  │                  │
│  ☀  23°C         │  SOL  $130,00    │                  │
│  Sensacion: 21°C │  XRP  $0,52      │                  │
│  → 12 km/h (W)   │  DOT  $5,80      │                  │
│  Humedad: 58%    │  POPCAT $0,3200  │                  │
│                  │  WIF  $1,2300    │                  │
│                  │  ALI  $0,0210    │                  │
│                  │  AURA $0,0045    │                  │
│                  │  ORO  $2.051/oz  │                  │
│                  │  PLATA $32,10/oz │                  │
│                  │  S&P500 5.102pts │                  │
│                  │  IBEX35 11.234pts│                  │
├──────────────────┴──────────────────┴──────────────────┤
│  NOTICIAS  COINTELEGRAPH · hace 3m                     │
│  Bitcoin surpasses $84,000 as institutional demand...  │
│  COINDESK · hace 12m                                   │
│  Solana DeFi volume hits record high amid rally...     │
└─────────────────────────────────────────────────────────┘
```

---

## Características

- **9 criptomonedas** en tiempo real: BTC, ETH, SOL, XRP, DOT, POPCAT, WIF, ALI, AURA
  — precio USD y EUR en una sola llamada a CoinMarketCap API
- **Sparkline BTC 7 días** con Matplotlib embebido en Tkinter
- **Mercados tradicionales**: Oro, Plata, S&P500, IBEX35 con conversión EUR vía Yahoo Finance
- **Meteorología Barcelona** con iconos Unicode (☀ ⛅ ☁ ☂ ❄ ⛈) y flecha de dirección del viento
- **Noticias RSS** de Cointelegraph y CoinDesk — rotación automática cada 6 segundos
- **Reloj digital** HH:MM:SS centrado, fecha en español
- **Modo kiosk** fullscreen sin cursor, sin barra de tareas — Linux y Windows
- **Arquitectura sin bloqueos**: daemon threads + cache en memoria + polling Tkinter

---

## Arquitectura

```
crypto_wall/
├── config.example.yaml          # Plantilla de configuracion (copiar a config.yaml)
├── requirements.txt
└── src/
    ├── main.py                  # Punto de entrada
    ├── services/
    │   ├── coinmarketcap.py     # 9 cryptos en una llamada (CMC API)
    │   ├── market_data.py       # Oro, Plata, S&P500, IBEX35, EUR/USD (Yahoo Finance)
    │   ├── weather.py           # Meteorologia Barcelona (wttr.in, sin API key)
    │   └── rss.py               # Noticias RSS (feedparser + requests)
    ├── ui/
    │   ├── app.py               # Ventana principal, grid 3+1, kiosk fullscreen
    │   ├── theme.py             # Paleta oscura y fuentes centralizadas
    │   └── widgets/
    │       ├── clock_weather_panel.py   # Cajón 1: reloj + meteorologia
    │       ├── market_panel.py          # Cajón 2: cryptos + commodities
    │       ├── placeholder_panel.py     # Cajón 3: DePIN (en desarrollo)
    │       └── news_panel.py            # Fila inferior: ticker de noticias
    └── utils/
        └── formatting.py        # Formatos numericos en locale español
```

### Patrón de datos

Todos los servicios siguen el mismo patrón:

1. **Daemon thread** independiente hace peticiones HTTP cada N segundos
2. Resultado guardado en **cache en memoria** protegida por `threading.Lock`
3. La UI **nunca bloquea**: usa `widget.after(N, callback)` para leer la cache
4. Si una petición falla, la cache conserva el último dato válido

---

## Instalación

### Requisitos

- Python 3.11+
- Raspberry Pi 4 (o cualquier Linux/Windows con pantalla)
- API key gratuita de [CoinMarketCap](https://coinmarketcap.com/api/)

### Pasos

```bash
git clone <repo-url>
cd crypto_wall

python3 -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

pip install -r requirements.txt

cp config.example.yaml config.yaml
# Editar config.yaml y añadir tu API key de CoinMarketCap
```

### Ejecutar

```bash
DISPLAY=:0 python src/main.py     # Linux (con display X)
python src/main.py                # Windows / desarrollo
```

### Autoarranque en Raspberry Pi (crontab)

```
@reboot sleep 15 && DISPLAY=:0 XAUTHORITY=/home/pi/.Xauthority /home/pi/crypto_wall/venv/bin/python /home/pi/crypto_wall/src/main.py
```

> **Nota:** No usar `source venv/bin/activate` en crontab — crontab usa `/bin/sh` y `source`
> es un builtin de bash. Usar siempre la ruta absoluta al Python del virtualenv.

### Configuración de pantalla 1024×600 en `/boot/config.txt`

```ini
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0
```

---

## Configuración

Copia `config.example.yaml` a `config.yaml` y ajusta los valores:

```yaml
display:
  fullscreen: true        # true en produccion
  hide_cursor: true       # true en produccion (sin raton)

api_keys:
  coinmarketcap: "TU_API_KEY"   # Plan gratuito suficiente

refresh:
  btc_price: 300          # segundos (5 min — CoinMarketCap)
  btc_chart: 300          # segundos (5 min — Yahoo Finance sparkline)
  gold:      1800         # segundos (30 min — Yahoo Finance)
  sp500:     1800         # segundos (30 min — Yahoo Finance)
  weather:   1800         # segundos (30 min — wttr.in)
  news:      1800         # segundos (30 min — RSS)
```

> `config.yaml` está en `.gitignore` — **nunca se commitea** la API key.

---

## Dependencias

| Paquete | Versión | Uso |
|---|---|---|
| `requests` | ≥2.31 | HTTP para CMC y wttr.in |
| `yfinance` | ≥0.2.40 | Yahoo Finance (oro, índices, EUR/USD) |
| `matplotlib` | ≥3.7 | Sparkline BTC embebido en Tkinter |
| `feedparser` | ≥6.0 | Parseo de feeds RSS |
| `pyyaml` | ≥6.0 | Lectura de config.yaml |
| `tkinter` | stdlib | UI (incluido en Python estándar) |

---

## Desarrollo

Para ejecutar en modo ventana (sin fullscreen):

```yaml
# config.yaml
display:
  fullscreen: false
  hide_cursor: false
```

Atajos de teclado en modo desarrollo:
- `Escape` — cierra la aplicación
- `F11` — alterna fullscreen

---

## Fases pendientes

| Fase | Descripción |
|------|-------------|
| 7 | Monitor Nodo DePIN (Filecoin / Storj) — reemplaza el placeholder del Cajón 3 |
| 8 | Test de estabilidad 72h en hardware real |
| 9 | Alertas de precio (notificaciones visuales en pantalla) |

---

## Autor

**Luis M. Caldeiro**
Proyecto iniciado en marzo de 2026.

---

## Créditos IA

Este proyecto fue diseñado e implementado íntegramente con asistencia de IA:

> 🤖 Built with **[Claude Code](https://claude.ai/code)** — *Claude Sonnet 4.6* by Anthropic
> Arquitectura, servicios, widgets, formateo, layout y documentación generados en sesiones
> de pair-programming con Claude Code en el IDE.

---

*Crypto Wall Dashboard — ambient display para hodlers 24/7*
