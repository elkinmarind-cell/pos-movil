@echo off
chcp 65001 >nul
title POS Movil - Aplicacion de escritorio en Kotlin
echo ============================================================
echo   POS Movil - Aplicacion en Kotlin (Compose Desktop)
echo ============================================================
echo.

cd /d "%~dp0kotlin"

rem --- Java ---------------------------------------------------------------
where java >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro Java.
  echo         Instala un JDK 17 o superior desde https://adoptium.net/
  echo         y vuelve a abrir esta ventana.
  echo.
  echo         Tambien puedes abrir la carpeta "kotlin" con IntelliJ IDEA
  echo         Community, que descarga Java y Gradle por su cuenta.
  pause & exit /b 1
)

rem --- Gradle: primero el wrapper del proyecto, si existe ------------------
set GRADLE=
if exist "gradlew.bat" set GRADLE=gradlew.bat
if not defined GRADLE (
  where gradle >nul 2>&1 && set GRADLE=gradle
)
if not defined GRADLE (
  echo [ERROR] No se encontro Gradle ni el wrapper del proyecto.
  echo.
  echo         Opcion 1: abre la carpeta "kotlin" con IntelliJ IDEA Community.
  echo         Opcion 2: instala Gradle ^(winget install Gradle.Gradle^) y
  echo                   ejecuta una sola vez, dentro de la carpeta kotlin:
  echo                       gradle wrapper --gradle-version 8.10
  echo                   Despues este archivo ya funciona solo.
  echo.
  echo         Lee kotlin\COMO-COMPILAR.md para el paso a paso.
  pause & exit /b 1
)
echo Usando: %GRADLE%
echo.

rem --- El servidor tiene que estar arriba ---------------------------------
curl -s -o nul http://127.0.0.1:8000/api/salud
if errorlevel 1 (
  echo [AVISO] El servidor no responde en http://127.0.0.1:8000
  echo         Abre 2-INICIAR.bat en otra ventana y vuelve a intentarlo.
  echo.
  set /p SEGUIR=Continuar de todas formas [s/N]:
  if /i not "%SEGUIR%"=="s" exit /b 0
)

echo Compilando y abriendo la aplicacion...
echo (la primera vez descarga Compose; puede tardar varios minutos)
echo.
call %GRADLE% run
echo.
echo ============================================================
echo   La aplicacion se cerro. Si fue por un error de compilacion,
echo   el mensaje esta arriba. Esta ventana no se cierra sola.
echo ============================================================
pause
