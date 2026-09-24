@echo off
title Iniciando POS Movil
if not exist "%~dp0backend\.venv\Scripts\python.exe" (
  echo [ERROR] Falta el entorno virtual. Ejecuta primero 1-INSTALAR.bat
  pause & exit /b 1
)
if not exist "%~dp0frontend\dist\index.html" (
  echo [ERROR] Falta la interfaz compilada en frontend\dist.
  pause & exit /b 1
)
start "POS Movil" "%~dp0_api.bat"
echo Iniciando el sistema...
timeout /t 6 >nul
start http://127.0.0.1:8000
exit
