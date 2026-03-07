import time


def fmt_usd(value, decimals=2):
    """Formato espanol: $67.234,12"""
    if value is None:
        return "—"
    parts = f"{abs(value):,.{decimals}f}".split('.')
    integer_part = parts[0].replace(',', '.')
    decimal_part = parts[1]
    sign = "-" if value < 0 else ""
    return f"{sign}${integer_part},{decimal_part}"


def fmt_change(value):
    """Retorna (texto, color) para variacion 24h: ('+2,34%', '#00ff88')"""
    if value is None:
        return "—", "#8888aa"
    arrow = "▲" if value >= 0 else "▼"
    sign = "+" if value >= 0 else ""
    color = "#00ff88" if value >= 0 else "#ff4466"
    decimal_str = f"{abs(value):.2f}".replace('.', ',')
    return f"{arrow} {sign}{decimal_str}%", color


def fmt_gold(value):
    """Formato oro: $2.051,30 /oz"""
    if value is None:
        return "Dato no disponible"
    return fmt_usd(value) + " /oz"


def fmt_sp500(value):
    """Formato S&P500: 5.102,45 pts"""
    if value is None:
        return "Dato no disponible"
    parts = f"{value:,.2f}".split('.')
    integer_part = parts[0].replace(',', '.')
    decimal_part = parts[1]
    return f"{integer_part},{decimal_part} pts"


def time_ago(timestamp):
    """Tiempo transcurrido desde timestamp en formato legible."""
    if timestamp is None:
        return "nunca"
    elapsed = time.time() - timestamp
    if elapsed < 60:
        return f"{int(elapsed)}s"
    elif elapsed < 3600:
        return f"{int(elapsed / 60)}m"
    else:
        return f"{int(elapsed / 3600)}h"


def fmt_eur(value, decimals=2):
    """Formato espanol euros: €2.051,30  (decimals=0 -> €4.724)"""
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    if decimals == 0:
        integer_str = f"{abs(value):,.0f}".replace(',', '.')
        return f"{sign}€{integer_str}"
    parts = f"{abs(value):,.{decimals}f}".split('.')
    integer_part = parts[0].replace(',', '.')
    decimal_part = parts[1]
    return f"{sign}€{integer_part},{decimal_part}"


def usd_to_eur(usd_value, eurusd_rate):
    """Convierte USD a EUR. eurusd_rate = cuantos USD vale 1 EUR (ej: 1.08)."""
    if usd_value is None or not eurusd_rate:
        return None
    return usd_value / eurusd_rate


def fmt_ibex(value):
    """Formato IBEX35: 11.234 pts (entero, ya en EUR)"""
    if value is None:
        return "Dato no disponible"
    integer_str = f"{int(round(value)):,}".replace(',', '.')
    return f"{integer_str} pts"


def freshness_color(timestamp, interval):
    """Color del indicador de frescura segun antiguedad relativa al intervalo."""
    if timestamp is None:
        return "#ff2244"
    elapsed = time.time() - timestamp
    if elapsed <= interval * 1.5:
        return "#00ff88"   # verde: dato reciente
    elif elapsed <= interval * 2.5:
        return "#ffcc00"   # amarillo: un ciclo perdido
    else:
        return "#ff2244"   # rojo: dato muy antiguo o offline
