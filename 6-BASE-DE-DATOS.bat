@echo off
chcp 65001 >nul
title Base de datos POS Movil - PostgreSQL
setlocal enabledelayedexpansion
echo ============================================================
echo   POS Movil - Instalacion de la base de datos PostgreSQL
echo ============================================================
echo.

rem --- Buscar psql.exe ---
set PSQL=
where psql.exe >nul 2>&1 && set PSQL=psql.exe
if not defined PSQL (
  for %%V in (18 17 16 15 14) do (
    if exist "C:\Program Files\PostgreSQL\%%V\bin\psql.exe" set PSQL=C:\Program Files\PostgreSQL\%%V\bin\psql.exe
  )
)
if not defined PSQL (
  echo [ERROR] No se encontro psql.exe.
  echo Instala PostgreSQL o agrega su carpeta bin al PATH.
  pause & exit /b 1
)
echo Usando: %PSQL%
echo.

set /p PGUSER=Usuario de PostgreSQL [postgres]: 
if "%PGUSER%"=="" set PGUSER=postgres
set /p PGPASSWORD=Contrasena de %PGUSER%: 
set PGCLIENTENCODING=UTF8
set BD=pos_movil
echo.

echo Verificando la conexion...
"%PSQL%" -U %PGUSER% -h localhost -d postgres -tAc "select 1" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se pudo conectar. Revisa el usuario, la contrasena o que el servicio este arriba.
  pause & exit /b 1
)

echo Creando la base %BD% si no existe...
"%PSQL%" -U %PGUSER% -h localhost -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='%BD%'" | findstr /r "1" >nul || "%PSQL%" -U %PGUSER% -h localhost -d postgres -q -c "CREATE DATABASE %BD%"
echo.

echo ATENCION: los scripts borran y recrean el esquema public de %BD%.
set /p SEGURO=Escribe SI para continuar: 
if /i not "%SEGURO%"=="SI" ( echo Cancelado. & pause & exit /b 0 )
echo.

for %%S in (01_esquema 02_programacion 03_datos_prueba) do (
  echo [%%S] ejecutando...
  "%PSQL%" -U %PGUSER% -h localhost -d %BD% -v ON_ERROR_STOP=1 -q -f "%~dp0database\%%S.sql"
  if errorlevel 1 ( echo [ERROR] Fallo %%S. & pause & exit /b 1 )
)
echo.
echo Ejecutando las pruebas de la base...
"%PSQL%" -U %PGUSER% -h localhost -d %BD% -v ON_ERROR_STOP=1 -f "%~dp0database\04_pruebas.sql"
if errorlevel 1 ( echo [ERROR] Las pruebas no pasaron. & pause & exit /b 1 )
echo.
echo ============================================================
echo   LISTO: 37 tablas, 8 vistas, 3 funciones, 3 procedimientos
echo   y 9 triggers, con datos de prueba cargados.
echo ============================================================
pause
