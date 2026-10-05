@echo off
chcp 65001 >nul
title POS Movil - Crear el ejecutable
echo ============================================================
echo   POS Movil - Generacion de POS-Movil.exe
echo ============================================================
echo.
echo   Esto empaqueta la aplicacion de escritorio en un unico
echo   archivo .exe que funciona sin tener Python instalado.
echo   La primera vez tarda varios minutos: Flet descarga su
echo   cliente de escritorio y PyInstaller recorre todo el codigo.
echo.

set PY=%~dp0backend\.venv\Scripts\python.exe
if not exist "%PY%" (
  echo [ERROR] Falta el entorno virtual. Ejecuta primero 1-INSTALAR.bat
  pause & exit /b 1
)

"%PY%" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
  echo Instalando PyInstaller...
  "%PY%" -m pip install pyinstaller || (echo [ERROR] No se pudo instalar PyInstaller. & pause & exit /b 1)
)

cd /d "%~dp0escritorio"
echo Empaquetando...
echo.
"%PY%" -m flet pack app.py ^
  --name POS-Movil ^
  --icon assets\icono.ico ^
  --product-name "POS Movil" ^
  --product-version "1.0.0" ^
  --file-version "1.0.0.0" ^
  --file-description "Sistema POS para la gestion y venta de dispositivos moviles" ^
  --company-name "Corporacion Unificada Nacional - CUN" ^
  --copyright "Elkin Santiago Marin Duarte y Juan David Zabala Plata" ^
  -y

if errorlevel 1 (
  echo.
  echo [ERROR] El empaquetado fallo. El mensaje de PyInstaller esta arriba.
  pause & exit /b 1
)

echo.
echo ============================================================
echo   LISTO
echo.
echo   El ejecutable quedo en:
echo     %~dp0escritorio\dist\POS-Movil.exe
echo.
echo   Para usarlo, el servidor debe estar encendido (2-INICIAR.bat).
echo   Si la API esta en otro equipo, define antes la variable:
echo     set POS_SERVIDOR=http://IP-DEL-SERVIDOR:8000/api
echo ============================================================
pause
