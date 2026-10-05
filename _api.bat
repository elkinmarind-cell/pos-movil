@echo off
chcp 65001 >nul
title POS Movil - servidor   (no cierres esta ventana)
cd /d "%~dp0backend"
echo ============================================================
echo   Servidor del POS Movil
echo   Interfaz:      http://127.0.0.1:8000
echo   Documentacion: http://127.0.0.1:8000/docs
echo.
echo   Cierra esta ventana para detener el sistema.
echo ============================================================
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
echo.
echo ============================================================
echo   El servidor se detuvo. Si fue por un error, el mensaje
echo   esta arriba. Esta ventana no se cierra sola.
echo ============================================================
pause
