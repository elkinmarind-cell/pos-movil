@echo off
chcp 65001 >nul
title Pruebas del POS Movil
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Ejecuta primero 1-INSTALAR.bat
  pause & exit /b 1
)
echo ============================================================
echo   Pruebas del sistema
echo   Requiere la base recien cargada con 6-BASE-DE-DATOS.bat
echo ============================================================
echo.
echo [1/3] El modelo ORM coincide con el esquema de PostgreSQL...
".venv\Scripts\python.exe" -m tests.consistencia
if errorlevel 1 ( echo [ERROR] El ORM y la base no coinciden. & pause & exit /b 1 )
echo.
echo [2/3] Los esquemas de la API coinciden con el modelo...
".venv\Scripts\python.exe" -m tests.esquemas
if errorlevel 1 ( echo [ERROR] Hay campos sin respaldo. & pause & exit /b 1 )
echo.
echo [3/3] Prueba de extremo a extremo de toda la API...
".venv\Scripts\python.exe" -m tests.test_api
if errorlevel 1 ( echo [ERROR] Fallaron verificaciones. & pause & exit /b 1 )
echo.
echo ============================================================
echo   TODAS LAS PRUEBAS PASARON
echo ============================================================
pause
