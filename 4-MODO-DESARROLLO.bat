@echo off
chcp 65001 >nul
title Modo desarrollo (recarga automatica)
set RAIZ=%~dp0
if not exist "%RAIZ%frontend\node_modules" (
  echo Faltan las dependencias de la interfaz. Instalandolas...
  cd /d "%RAIZ%frontend"
  call npm install
  if not exist "%RAIZ%frontend\node_modules" (
    echo [ERROR] npm install no funciono. Usa 2-INICIAR.bat, que no necesita Node.
    pause & exit /b 1
  )
)
echo Liberando los puertos 8000 y 5173...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do taskkill /f /pid %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5173" ^| findstr LISTENING') do taskkill /f /pid %%p >nul 2>&1
timeout /t 2 >nul
start "POS Movil - servidor (recarga)" cmd /k "cd /d %RAIZ%backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
start "POS Movil - interfaz (Vite)" cmd /k "cd /d %RAIZ%frontend && npm run dev"
timeout /t 10 >nul
start "" http://localhost:5173
exit
