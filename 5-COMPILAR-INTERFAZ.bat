@echo off
chcp 65001 >nul
title Recompilar la interfaz
cd /d "%~dp0frontend"
if not exist node_modules ( call npm install )
call npm run build
echo.
echo Interfaz recompilada en frontend\dist.
pause
