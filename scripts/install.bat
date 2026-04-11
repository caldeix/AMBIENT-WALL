@echo off
REM Crypto Wall Dashboard — Install script for Windows
REM Usage: double-click or run from cmd: scripts\install.bat

setlocal enabledelayedexpansion

set "REPO_DIR=%~dp0.."
set "VENV_DIR=%REPO_DIR%\venv"
set "CONFIG_SRC=%REPO_DIR%\config.example.yaml"
set "CONFIG_DST=%REPO_DIR%\config.yaml"

echo.
echo ========================================
echo   Crypto Wall Dashboard - Instalacion
echo ========================================
echo.

REM ── 1. Locate Python 3 ──────────────────────────────────────
set "PYTHON="
for %%c in (python3.12 python3.11 python3.10 python3 python) do (
  if "!PYTHON!"=="" (
    where %%c >nul 2>&1
    if !errorlevel! == 0 (
      for /f "delims=" %%v in ('%%c -c "import sys; print(sys.version_info.major)" 2^>nul') do (
        if "%%v"=="3" set "PYTHON=%%c"
      )
    )
  )
)

if "!PYTHON!"=="" (
  echo [ERROR] No se encontro Python 3.
  echo         Descargalo desde https://www.python.org/downloads/
  echo         Asegurate de marcar "Add Python to PATH" durante la instalacion.
  pause
  exit /b 1
)

for /f "delims=" %%v in ('!PYTHON! --version 2^>^&1') do set "PYVER=%%v"
echo [OK] Python encontrado: !PYVER! ^(!PYTHON!^)

REM ── 2. Create virtual environment ───────────────────────────
if exist "!VENV_DIR!\Scripts\python.exe" (
  echo [OK] Entorno virtual ya existe
) else (
  echo [ ] Creando entorno virtual...
  !PYTHON! -m venv "!VENV_DIR!"
  echo [OK] Entorno virtual creado en !VENV_DIR!
)

set "PIP=!VENV_DIR!\Scripts\pip.exe"
set "PYTHON_VENV=!VENV_DIR!\Scripts\python.exe"

REM ── 3. Install dependencies ──────────────────────────────────
echo [ ] Instalando dependencias...
"!PIP!" install --upgrade pip --quiet
"!PIP!" install -r "!REPO_DIR!\requirements.txt" --quiet
echo [OK] Dependencias instaladas

REM ── 4. Copy config if not present ───────────────────────────
if exist "!CONFIG_DST!" (
  echo [OK] config.yaml ya existe - no se sobreescribe
) else (
  copy "!CONFIG_SRC!" "!CONFIG_DST!" >nul
  echo [OK] config.yaml creado desde config.example.yaml
  echo.
  echo   Edita config.yaml y anade tu API key de CoinMarketCap:
  echo   !CONFIG_DST!
)

REM ── 5. Done ──────────────────────────────────────────────────
echo.
echo ========================================
echo   Instalacion completada
echo ========================================
echo.
echo   Ejecutar el dashboard:
echo     "!PYTHON_VENV!" "!REPO_DIR!\src\main.py"
echo.
echo   Para desarrollo (modo ventana), edita config.yaml:
echo     environment: test
echo     display:
echo       fullscreen: false
echo       hide_cursor: false
echo.
pause
