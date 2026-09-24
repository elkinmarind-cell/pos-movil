@echo off
chcp 65001 >nul
title Modo desarrollo (Vite con recarga automatica)
if not exist "%~dp0frontend\node_modules" (
  echo Faltan las dependencias de la interfaz. Instalandolas ahora...
  cd /d "%~dp0frontend"
  call npm install
  if not exist "%~dp0frontend\node_modules" (
    echo.
    echo [ERROR] npm install no funciono. Copia el mensaje de arriba.
    echo Mientras tanto puedes usar 2-INICIAR.bat, que no necesita Node.
    pause & exit /b 1
  )
)
start "API del POS" "%~dp0_api.bat"
start "Vite - interfaz" "%~dp0_web.bat"
timeout /t 8 >nul
start http://localhost:5173
exit
