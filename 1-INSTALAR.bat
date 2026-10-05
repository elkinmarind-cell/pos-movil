@echo off
chcp 65001 >nul
title Instalacion del POS Movil
echo ============================================================
echo   POS Movil - Instalacion (solo la primera vez)
echo ============================================================
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
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv || (echo [ERROR] No se pudo crear el entorno virtual. & pause & exit /b 1)
) else (
  echo       ya existia, se reutiliza.
)

echo [2/4] Instalando las dependencias del servidor...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt || (echo [ERROR] Fallo la instalacion del servidor. & pause & exit /b 1)

echo [3/4] Instalando las dependencias de la app de escritorio...
".venv\Scripts\python.exe" -m pip install -r "%~dp0escritorio\requirements.txt" || (echo [ERROR] Fallo la instalacion del escritorio. & pause & exit /b 1)

cd /d "%~dp0frontend"
echo [4/4] Instalando las dependencias de la interfaz web...
call npm install || (echo [ERROR] Fallo npm install. & pause & exit /b 1)

echo.
echo ============================================================
echo   LISTO.
echo.
echo   Siguiente paso: ejecuta  6-BASE-DE-DATOS.bat
echo   para crear el esquema y los datos en PostgreSQL.
echo   Despues ya puedes usar  2-INICIAR.bat
echo ============================================================
pause
