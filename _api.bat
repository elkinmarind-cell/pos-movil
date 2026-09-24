@echo off
title POS Movil  -  http://127.0.0.1:8000   (documentacion: /docs)
cd /d "%~dp0backend"
echo ============================================
echo   POS Movil en marcha
echo   Interfaz:      http://127.0.0.1:8000
echo   Documentacion: http://127.0.0.1:8000/docs
echo   Usuario: admin / admin123
echo.
echo   Cierra esta ventana para detener el sistema.
echo ============================================
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
pause
