@echo off
chcp 65001 >nul
title Detener el POS Movil
echo Buscando servidores en el puerto 8000...
set ENCONTRADOS=0
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do (
  echo   deteniendo proceso %%p
  taskkill /f /pid %%p >nul 2>&1
  set /a ENCONTRADOS+=1
)
timeout /t 1 >nul
netstat -ano | findstr ":8000" | findstr LISTENING >nul 2>&1
if errorlevel 1 (
  echo.
  echo El puerto 8000 quedo libre.
) else (
  echo.
  echo [AVISO] Todavia hay algo escuchando en el puerto 8000.
)
echo.
pause
