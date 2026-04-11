#!/bin/bash
# Crypto Wall Dashboard — Install script for Linux / Raspberry Pi
# Usage: bash scripts/install.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$REPO_DIR/venv"
CONFIG_SRC="$REPO_DIR/config.example.yaml"
CONFIG_DST="$REPO_DIR/config.yaml"

echo ""
echo "========================================"
echo "  Crypto Wall Dashboard — Instalación"
echo "========================================"
echo ""

# ── 1. Locate Python 3 ──────────────────────────────────────────
PYTHON=""
for candidate in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$candidate" &>/dev/null; then
    ver=$("$candidate" -c "import sys; print(sys.version_info.major)" 2>/dev/null)
    if [ "$ver" = "3" ]; then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "[ERROR] No se encontró Python 3. Instálalo con:"
  echo "        sudo apt install python3 python3-venv python3-pip"
  exit 1
fi

PYTHON_VERSION=$("$PYTHON" --version 2>&1)
echo "[OK] Python encontrado: $PYTHON_VERSION ($PYTHON)"

# ── 2. Create virtual environment ───────────────────────────────
if [ -d "$VENV_DIR" ]; then
  echo "[OK] Entorno virtual ya existe: $VENV_DIR"
else
  echo "[ ] Creando entorno virtual..."
  "$PYTHON" -m venv "$VENV_DIR"
  echo "[OK] Entorno virtual creado en $VENV_DIR"
fi

PIP="$VENV_DIR/bin/pip"
PYTHON_VENV="$VENV_DIR/bin/python"

# ── 3. Install dependencies ──────────────────────────────────────
echo "[ ] Instalando dependencias..."
"$PIP" install --upgrade pip --quiet
"$PIP" install -r "$REPO_DIR/requirements.txt" --quiet
echo "[OK] Dependencias instaladas"

# ── 4. Copy config if not present ───────────────────────────────
if [ -f "$CONFIG_DST" ]; then
  echo "[OK] config.yaml ya existe — no se sobreescribe"
else
  cp "$CONFIG_SRC" "$CONFIG_DST"
  echo "[OK] config.yaml creado desde config.example.yaml"
  echo ""
  echo "  ⚠  Edita config.yaml y añade tu API key de CoinMarketCap:"
  echo "     $CONFIG_DST"
fi

# ── 5. Done ──────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  Instalación completada"
echo "========================================"
echo ""
echo "  Ejecutar el dashboard:"
echo "    DISPLAY=:0 $PYTHON_VENV $REPO_DIR/src/main.py"
echo ""
echo "  ── Autoarranque con crontab ─────────────────────────────"
echo "  Para que el dashboard arranque solo al encender la Raspberry:"
echo ""
echo "    1. Abre el editor de crontab:"
echo "       crontab -e"
echo ""
echo "    2. Añade esta línea al final (ajusta el usuario si no es 'pi'):"
echo "       @reboot sleep 15 && DISPLAY=:0 XAUTHORITY=/home/\$USER/.Xauthority \\"
echo "           $PYTHON_VENV $REPO_DIR/src/main.py >> $REPO_DIR/src/app.log 2>&1"
echo ""
echo "    IMPORTANTE: Usa siempre la ruta absoluta al Python del venv."
echo "    NO uses 'source venv/bin/activate' en crontab — no funciona en /bin/sh."
echo ""
