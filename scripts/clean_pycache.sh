#!/bin/bash
# Elimina todos los __pycache__ y archivos .pyc del proyecto
# Ejecutar desde la raiz del proyecto antes de copiar al servidor:
#   bash scripts/clean_pycache.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo "Limpiando pycache en: $ROOT"

find "$ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find "$ROOT" -type f -name "*.pyc" -delete 2>/dev/null
find "$ROOT" -type f -name "*.pyo" -delete 2>/dev/null

echo "Listo. Puedes arrastrar la carpeta al servidor."
