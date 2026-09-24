@echo off
chcp 65001 >nul
title Instalacion del POS Movil
echo ============================================
echo   POS Movil - Instalacion (solo la 1a vez)
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro Python.
  echo Instalalo desde python.org y marca la casilla "Add Python to PATH".
  pause & exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro Node.js / npm.
  echo Instalalo desde nodejs.org.
  pause & exit /b 1
)

cd /d "%~dp0backend"
echo [1/4] Creando el entorno virtual...
python -m venv .venv || (echo [ERROR] No se pudo crear el entorno virtual. & pause & exit /b 1)

echo [2/4] Instalando dependencias de Python...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt || (echo [ERROR] Fallo la instalacion de dependencias. & pause & exit /b 1)

echo [3/4] Creando la base de datos y los datos de prueba...
".venv\Scripts\python.exe" -m app.seed || (echo [ERROR] Fallo la carga de datos. & pause & exit /b 1)

cd /d "%~dp0frontend"
echo [4/4] Instalando dependencias de la interfaz...
call npm install || (echo [ERROR] Fallo npm install. & pause & exit /b 1)

echo.
echo ============================================
echo   LISTO. Ahora ejecuta  2-INICIAR.bat
echo ============================================
pause
