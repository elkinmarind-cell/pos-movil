@echo off
chcp 65001 >nul
title Pruebas del POS Movil
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta primero 1-INSTALAR.bat
  pause & exit /b 1
)
".venv\Scripts\python.exe" -m tests.test_flujo
pause
