@echo off
chcp 65001 >nul
title Iniciando POS Movil
set RAIZ=%~dp0

if not exist "%RAIZ%backend\.venv\Scripts\python.exe" (
  echo [ERROR] Falta el entorno virtual. Ejecuta primero 1-INSTALAR.bat
  pause & exit /b 1
)
if not exist "%RAIZ%frontend\dist\index.html" (
  echo [ERROR] Falta la interfaz compilada en frontend\dist.
  pause & exit /b 1
)

echo Liberando el puerto 8000 por si quedo ocupado...
set LIBERADOS=0
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do (
  taskkill /f /pid %%p >nul 2>&1
  set /a LIBERADOS+=1
)
timeout /t 2 >nul

start "POS Movil - servidor" "%RAIZ%_api.bat"
echo Esperando a que el servidor responda...

set INTENTOS=0
:esperar
set /a INTENTOS+=1
timeout /t 1 >nul
curl -s -o nul http://127.0.0.1:8000/api/salud
if not errorlevel 1 goto listo
if %INTENTOS% lss 30 goto esperar

echo.
echo ============================================================
echo   [ERROR] El servidor no respondio en 30 segundos.
echo   Mira la ventana titulada "POS Movil - servidor": ahi esta
echo   el error. Si se cerro sola, ejecuta 0-DIAGNOSTICO.bat
echo ============================================================
pause
exit /b 1

:listo
echo.
echo ============================================================
echo   POS Movil en marcha
echo   Interfaz:      http://127.0.0.1:8000
echo   Documentacion: http://127.0.0.1:8000/docs
echo.
echo   Para detenerlo: cierra la ventana del servidor
echo   o ejecuta 9-DETENER.bat
echo ============================================================
start "" http://127.0.0.1:8000
timeout /t 3 >nul
exit
