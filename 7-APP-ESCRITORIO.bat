@echo off
chcp 65001 >nul
title POS Movil - Aplicacion de escritorio
echo ============================================================
echo   POS Movil - Aplicacion de escritorio (Flet)
echo ============================================================
echo.

if not exist "%~dp0backend\.venv\Scripts\python.exe" (
  echo [ERROR] Falta el entorno virtual. Ejecuta primero 1-INSTALAR.bat
  pause & exit /b 1
)

rem El escritorio consume la misma API que la interfaz web, asi que el servidor
rem tiene que estar encendido. Si no responde, se avisa en lugar de abrir una
rem ventana que no va a poder iniciar sesion.
curl -s -o nul http://127.0.0.1:8000/api/salud
if errorlevel 1 (
  echo [AVISO] El servidor no responde en http://127.0.0.1:8000
  echo         Abre 2-INICIAR.bat en otra ventana y vuelve a intentarlo.
  echo.
  set /p SEGUIR=Abrir la aplicacion de todas formas [s/N]:
  if /i not "%SEGUIR%"=="s" exit /b 0
)

cd /d "%~dp0escritorio"
echo Abriendo la aplicacion...
echo.
"%~dp0backend\.venv\Scripts\python.exe" app.py
echo.
echo ============================================================
echo   La aplicacion se cerro. Si fue por un error, el mensaje
echo   esta arriba. Esta ventana no se cierra sola.
echo ============================================================
pause
