# CHANGELOG — Financial Wall Dashboard

> Registro de cambios siguiendo [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).
> Versiones en orden cronológico inverso. La documentación de arquitectura y configuración
> completa está en el [README](README.md).

---

## [1.4.1] — 2026-06-07

### Ajuste de colores de tinte dinámico de precio.

#### Cambiado

- **`BG_CHANGE_DOWN`** `#150a08` → `#1f0808`: rojo oscuro más visible en pantalla física.
- **`BG_CHANGE_UP`** `#091409` → `#0a1f0a`: verde oscuro con mayor brillo.
- **`CLAUDE.md`**: añadidas normas de git — no hacer commit/push autónomo,
  usar `/actualiza-master` para subir cambios.

---

## [1.4.0] — 2026-06-07

### Velas japonesas, precio EUR, rediseño dark premium y ordenación de altcoins.

#### Añadido

- **Velas japonesas en los 6 chart blocks:** reemplazo completo de los sparklines lineales
  por gráficos de candlestick. Máximo 35 velas con submuestreo automático si el historial
  es más largo.
  - `market_data.py`: nueva función `_extract_ohlc()` extrae tuplas `(open, high, low, close)`
    del DataFrame de yfinance.
  - `market_panel.py`: `_draw_candles()` dibuja cuerpos con `mpatches.Rectangle` y mechas
    con `ax.plot` (linewidth 0.7). Verde (`POSITIVE`) si cierre ≥ apertura, rojo (`NEGATIVE`)
    si cierre < apertura. Doji (variación < 0,15% del rango) se representa como guión horizontal.
  - Fallback automático a gráfico lineal si los datos OHLC no están disponibles.

- **Precio EUR en el header de cada chart block:** etiqueta pequeña debajo del precio USD
  principal, calculada con el tipo EUR/USD en tiempo real. Solo se muestra en bloques con
  `cmc_symbol` (cryptos); commodities e índices quedan en blanco.

- **Fondo dinámico por dirección de precio (24h):** tinte sutil aplicado tanto a los
  chart blocks como a cada celda de la rejilla de altcoins según el cambio porcentual de
  las últimas 24 horas:
  - Subida → `BG_CHANGE_UP = #091409` (verde muy oscuro)
  - Bajada → `BG_CHANGE_DOWN = #150a08` (cálido oscuro)
  - Sin dato → fondo neutro por tipo de activo

- **Ordenación de altcoins en la webapp:** dos botones encima de la lista de drag & drop:
  - *Az nombre* — ordena alfabéticamente por nombre
  - *# rank* — ordena por posición en CoinMarketCap (ascendente; sin rank al final)
  - Nuevo endpoint `GET /api/cmc/ranks?symbols=BTC,ETH,...` devuelve `{SYMBOL: {rank, name}}`
    consultando el mapa local CMC. Se llama al arrancar la webapp para enriquecer los ítems
    cargados desde `config.yaml` (que solo tienen el símbolo, sin rank).

- **Rank badge de ancho fijo en la rejilla de altcoins:** la etiqueta del rank usa
  `width=5, anchor='center'` para que `#1`, `#55` y `#1234` ocupen el mismo espacio
  horizontal y la columna quede alineada visualmente.

- **`CLAUDE.md`:** documento de contexto para Claude Code en la raíz del proyecto.
  Incluye árbol de archivos, diagrama de flujo de datos, config system, theme system,
  estructura interna de `market_panel.py` y patrones a seguir al modificar el código.

- **Skill `/actualiza-master`:** comando personalizado de Claude Code en
  `.claude/commands/actualiza-master.md`. Agrupa los cambios pendientes por área lógica,
  crea commits descriptivos sin líneas `Co-Authored-By`, hace merge a master y push a GitHub.

#### Cambiado

- **Rediseño visual completo (dark terminal premium):**
  - `theme.py` reescrito con paleta inspirada en Bloomberg + exchanges crypto: fondos
    diferenciados por tipo de activo (`BG_PANEL_CRYPTO`, `BG_PANEL_COMMODITY`,
    `BG_PANEL_INDEX`), colores de acento eléctrico por tipo (cian / ámbar / menta),
    separadores de doble línea con efecto glow.
  - `top_bar.py`: tres labels independientes con colores distintos (reloj blanco,
    fecha gris-azul, clima cian) en lugar de un label combinado. Separador inferior
    doble `SEP_BRIGHT` + `SEP_DARK`.
  - `market_panel.py`: stripe de color de 4 px en el borde izquierdo de cada chart block
    según tipo de activo; rank badge como píldora con fondo `RANK_OTHER_BG` uniforme
    (sin distinción por tier); zebra en la rejilla de altcoins (`BG_ALT_ROW_ODD` /
    `BG_ALT_ROW_EVEN`); indicadores ▲/▼ en los cambios 24h con `POSITIVE` / `NEGATIVE`.

- **`app.py`:** eliminado `bg='#000000'` hardcodeado en la instanciación de `TopBar`;
  ahora hereda `TOPBAR_BG` del theme.

- **`.gitignore`:** cambiado `.claude` (directorio completo ignorado) por `.claude/*`
  con excepción `!.claude/commands/` para que los comandos personalizados se versionen.

#### Corregido

- **Ordenación por rank en la webapp no funcionaba:** los ítems cargados desde `config.yaml`
  tenían `rank: null` porque el config solo almacena símbolos. Corregido enriqueciendo los
  ranks al arrancar la webapp con el nuevo endpoint `/api/cmc/ranks`.

---

## [1.3.3] — 2026-04-12

### Renombrado a Financial Wall, mejoras de documentación.

#### Cambiado

- **Nombre del producto:** "Crypto Wall" → "Financial Wall" en todos los ficheros
  (títulos, logs, scripts de instalación, webapp de configuración, README, CHANGELOG).
  El nombre del directorio (`crypto_wall/`) no cambia.

- **README — sección webapp:** descripción detallada de las funciones de la webapp de
  configuración (bloques sparkline, altcoin grid, refresco, entorno, hot-reload).
  Añadida captura de pantalla (`resources/img/screenshot_appconfig.png`).

- **README — crontab:** añadida la línea de autoarranque de la webapp (`server.py`)
  junto a la del dashboard. La webapp arranca 1 segundo después (`sleep 16`) para
  evitar conflictos de escritura en `config.yaml`.

- **README — sección autor:** restaurados los créditos IA (Claude Code / Claude Sonnet 4.6)
  junto a los datos del autor.

---

## [1.3.2] — 2026-04-12

### Mínimos de refresco por intervalo.

#### Cambiado

- **Validación de intervalos de refresco:** cada clave tiene ahora su propio mínimo
  en lugar del genérico de 60s. Si el usuario configura un valor inferior, la app
  lo ignora con un warning en el log y aplica el mínimo:

  | Clave | Mínimo | Razón |
  |---|---|---|
  | `cryptos` | 300 s (5 min) | Cuota API gratuita de CoinMarketCap |
  | `charts` | 300 s (5 min) | Yahoo Finance sparklines |
  | `market` | 1800 s (30 min) | Yahoo Finance mercado (Oro, Plata, S&P, IBEX) |
  | `weather` | 1800 s (30 min) | wttr.in meteorología |

- **`config.example.yaml`:** comentarios actualizados indicando el mínimo de cada clave.
- **README:** tabla de configuración actualizada con los mínimos por clave.

---

## [1.3.1] — 2026-04-12

### Ciudad dinámica en top bar.

#### Corregido

- **`top_bar.py` — ciudad hardcodeada:** los tres estados del widget de tiempo
  (`temp + desc`, solo `temp`, sin dato) mostraban `"Barcelona"` fijo en el string.
  Corregido a `self._weather.city` para respetar `weather.city` del `config.yaml`.

---

## [1.3.0] — 2026-04-12

### Instalación automática, hot-reload completo, mejoras de webapp y consolidación.

#### Añadido

- **Scripts de instalación:**
  - `scripts/install.sh` — automatiza la instalación en Linux / Raspberry Pi: localiza
    Python 3, crea entorno virtual, instala dependencias, copia `config.example.yaml` si no
    existe e imprime las instrucciones de crontab con ruta absoluta al virtualenv.
  - `scripts/install.bat` — equivalente para Windows.

- **Hot-reload en `CoinMarketCapService`:** el servicio acepta un `config_manager` opcional
  y registra un listener. Al guardar cambios en `config.yaml` (desde la webapp o a mano),
  el thread de datos se despierta y aplica la nueva configuración sin reiniciar el dashboard.
  El ciclo de espera usa `threading.Event.wait(timeout)` para ser interruptible.

- **`shared/config_manager.py`:** `ConfigManager` compartido entre el dashboard (Tkinter) y
  la webapp de configuración (Flask). File watcher con polling de 2 segundos, sistema de
  listeners via `threading.Event`, lectura thread-safe con `threading.Lock`.

#### Corregido

- **Bloques con sparkline — ancho 1/3 fijo:** los 6 bloques (filas 1 y 2) ahora ocupan
  exactamente 1/3 del ancho disponible, independientemente del contenido. Causa: Tkinter
  `grid` con `weight=1` no garantiza igualdad cuando una columna no tiene contenido.
  Solución: `grid_columnconfigure(c, weight=1, uniform='chart_cols')`.

- **Drag & drop webapp (CMC → lista de altcoins):** los items del buscador CMC usan el
  sistema nativo de HTML5 drag & drop (`dragstart` + `dataTransfer`). La lista de altcoins
  usaba SortableJS, que no procesa eventos nativos de arrastre entre listas externas.
  Solución: `attachAltNativeDrop()` registra listeners `dragover`/`dragleave`/`drop`
  directamente en el contenedor, sin interferir con el reorden interno de SortableJS.

#### Cambiado

- **Labels de refresco en la webapp:** los cuatro campos muestran ahora la fuente y los
  activos que cubren, evitando confusión entre intervalos:
  - "Cryptos — precios CMC (seg)"
  - "Gráficos BTC/ETH — Yahoo (seg)"
  - "Mercado — Oro, Plata, S&P, IBEX (seg)"
  - "Tiempo meteorológico — wttr.in (seg)"

- **`config.example.yaml` reescrito:** incluye la sección `chart_blocks` completa con los
  6 bloques por defecto (BTC, ETH, ORO, S&P500, PLATA, IBEX35), documentación inline de
  todos los campos (`label`, `ticker`, `period`, `cmc_symbol`, `format`) y comentarios
  explicativos para cada sección.

- **README reescrito** (v1.3.0): layout ASCII actualizado, instalación por script y manual,
  sección de webapp de configuración, tablas de referencia completas para `config.yaml` y
  `chart_blocks`, atajos de teclado y configuraciones de resolución para Raspberry Pi.

#### Eliminado

- **`app-config/requirements.txt`:** archivo redundante. Todas las dependencias (dashboard +
  webapp) están en el `requirements.txt` raíz.

- **Duplicados en `requirements.txt`:** `pyyaml`, `requests` y `yfinance` aparecían dos
  veces. Consolidado en 5 dependencias únicas.

---

## [1.2.1] — 2026-04-10

### Ciudad del tiempo configurable desde config.yaml.

#### Cambiado

- **`weather.city` en config:** la ciudad para el servicio meteorológico pasa de estar
  hardcodeada en `main.py` a leerse de `config.yaml → weather.city`.
  Valor por defecto: `Barcelona`. Cualquier ciudad soportada por wttr.in es válida.

  ```yaml
  weather:
    city: "Barcelona"
  ```

- `_default_config()` actualizado para incluir la sección `weather`.

---

## [1.2.0] — 2026-04-10

### Config por entornos, modo mockup, cryptos dinámicas desde YAML, CMC rank y limpieza de código.

#### Añadido

- **Entornos de ejecución (`environment`):** nuevo campo en `config.yaml` con tres valores:
  - `mockup` — sin llamadas a CoinMarketCap; datos inventados realistas con jitter ±0,5%
    por ciclo para simular movimiento. Para desarrollo sin consumir créditos de API.
  - `test` — llamadas reales, pantalla en modo ventana.
  - `pro` — producción completa (Raspberry Pi, fullscreen, sin cursor).

- **Cryptos configurables desde YAML:** `config.yaml → cryptos.symbols` define la lista
  de monedas. La cache de `CoinMarketCapService` se genera por dict comprehension a partir
  de los símbolos configurados. Añadir o quitar una moneda no requiere cambios en el código.

- **CMC Rank visible:** cada crypto muestra su posición: `#1 BTC`, `#2 ETH`, `#5 SOL`.
  Obtenido del campo `cmc_rank` de la API, actualizado en cada ciclo de refresco.

- **Rejilla de altcoins dinámica:** `market_panel.py` construye la rejilla inferior en
  tiempo de ejecución según los símbolos del config. 3 columnas, filas calculadas
  automáticamente.

- **Decimales automáticos (`_auto_decimals`):** ≥$100 → 2 dec., ≥$0,01 → 4 dec.,
  <$0,01 → 6 dec.

#### Cambiado

- **Layout simplificado a panel único:**
  - Top bar (5%): hora, fecha y resumen del tiempo en una sola línea.
  - Market panel (95%): filas 1–2 con sparklines, fila 3+ altcoin grid.

- **`CoinMarketCapService`:** constructor recibe `symbols` y `environment`. Cache generada
  dinámicamente. `_fetch_mockup()` y `_fetch_real()` separados con lógica limpia.

- **`MarketDataService`:** constructor simplificado a `interval_charts` e `interval_market`.

- **Claves de refresco renombradas:**
  - `btc_price` → `cryptos`
  - `btc_chart` → `charts`
  - `gold` + `sp500` → `market` (mismo intervalo para todos los activos Yahoo Finance)

#### Eliminado

- Archivos sin uso: `src/clock/clock.py`, `src/ui/widgets/placeholder_panel.py`,
  `src/ui/widgets/clock_weather_panel.py`.
- `_run_gold` + `_run_sp500` fusionados en un único thread `_run_market`.
- `fmt_change()` de `formatting.py` (importada pero nunca llamada).
- `WEATHER_EMOJI`, `_fetch_art()`, `art_text` de `weather.py` (solo los usaba
  `clock_weather_panel`, que fue eliminado).
- `display.width`, `display.height`, `refresh.news` de `config.example.yaml`.

---

## [1.1.0] — 2026-03-08

### Nuevos activos, rediseño del panel de tiempo, layout 3+1 y feed RSS.

#### Añadido

- **Layout 3+1:** grid de 3 columnas superiores + barra de noticias a ancho completo.
- **Nuevas criptomonedas:** DOT, POPCAT, WIF, ALI, AURA con precio USD + EUR.
- **ETH, SOL, XRP** integrados en `CoinMarketCapService` (misma llamada que BTC).
- **Plata (SI=F)** e **IBEX35 (^IBEX)** en `MarketDataService`, con precio EUR via
  conversión EUR/USD.
- **Panel de reloj rediseñado:** icono Unicode del tiempo (28px), flecha de viento,
  layout vertical con espaciadores flexibles.
- **Feed RSS** (Cointelegraph + CoinDesk): ticker rotativo en fila inferior, intervalo
  30 min, rotación automática cada 6 segundos.

#### Corregido

- **Fullscreen Linux:** `attributes("-fullscreen", True) + wm_attributes('-type', 'splash')`
  reemplaza `overrideredirect + geometry()` para evitar offset en LXDE/X11.
- **`fmt_eur(value, 0)` IndexError:** al formatear valores sin decimales, `split('.')` sobre
  `f"{n:,.0f}"` no genera parte decimal. Corregido.
- **RSS timeout:** `feedparser.parse()` podía colgar indefinidamente. Corregido usando
  `requests.get(url, timeout=8)` y pasando `resp.content` a feedparser.

---

## [1.0.0] — 2026-03-07

### Primera versión estable. Dashboard funcional para Raspberry Pi 4 con pantalla 1024×600.

- Grid 2×2: Mercados | DePIN | Noticias | Hora & Tiempo.
- Precios BTC en tiempo real via CoinMarketCap.
- Sparkline BTC 7 días via Yahoo Finance.
- Oro (GC=F) y S&P500 (^GSPC) via Yahoo Finance.
- Tiempo meteorológico via wttr.in (sin API key).
- Modo kiosk fullscreen sin cursor ni decoraciones.
- Daemon threads + cache en memoria + polling Tkinter.
