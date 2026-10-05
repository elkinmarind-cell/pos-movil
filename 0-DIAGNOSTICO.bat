@echo off
chcp 65001 >nul
title Diagnostico POS Movil
set LOG=%~dp0diagnostico.txt
set RAIZ=%~dp0

echo ============================================================
echo   Diagnostico del POS Movil
echo   Escribe el resultado en diagnostico.txt
echo ============================================================
echo.

echo === DIAGNOSTICO POS MOVIL === > "%LOG%"
echo. >> "%LOG%"

echo [1/7] Python del sistema...
echo --- 1. Python del sistema --- >> "%LOG%"
python --version >> "%LOG%" 2>&1

echo [2/7] Entorno virtual...
echo. >> "%LOG%" & echo --- 2. Entorno virtual --- >> "%LOG%"
if exist "%RAIZ%backend\.venv\Scripts\python.exe" (
  "%RAIZ%backend\.venv\Scripts\python.exe" --version >> "%LOG%" 2>&1
) else (
  echo FALTA el entorno virtual >> "%LOG%"
  goto :fin
)

echo [3/7] Paquetes instalados...
echo. >> "%LOG%" & echo --- 3. Paquetes --- >> "%LOG%"
"%RAIZ%backend\.venv\Scripts\python.exe" -m pip list >> "%LOG%" 2>&1

echo [4/7] Archivo .env...
echo. >> "%LOG%" & echo --- 4. Configuracion --- >> "%LOG%"
if exist "%RAIZ%backend\.env" (
  echo .env existe >> "%LOG%"
) else (
  echo FALTA backend\.env >> "%LOG%"
)

echo [5/7] Importando la aplicacion...
echo. >> "%LOG%" & echo --- 5. Importacion de la aplicacion --- >> "%LOG%"
cd /d "%RAIZ%backend"
"%RAIZ%backend\.venv\Scripts\python.exe" -c "from app.main import app; print('la aplicacion importa bien')" >> "%LOG%" 2>&1

echo [6/7] Conexion a PostgreSQL...
echo. >> "%LOG%" & echo --- 6. Base de datos --- >> "%LOG%"
"%RAIZ%backend\.venv\Scripts\python.exe" -c "from app.database import engine; from sqlalchemy import text; cx=engine.connect(); print('conectado a PostgreSQL', cx.execute(text('show server_version')).scalar()); print('tablas en el esquema:', cx.execute(text(chr(34)+'select count(*) from information_schema.tables where table_schema=' + chr(39) + 'public' + chr(39) + ' and table_type=' + chr(39) + 'BASE TABLE' + chr(39)+chr(34))).scalar())" >> "%LOG%" 2>&1

echo [7/7] Levantando el servidor 12 segundos...
echo. >> "%LOG%" & echo --- 7. Puerto 8000 antes de arrancar --- >> "%LOG%"
netstat -ano | findstr ":8000" >> "%LOG%" 2>&1
echo. >> "%LOG%" & echo --- 8. Arranque del servidor --- >> "%LOG%"
start /b "" "%RAIZ%backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --port 8000 > "%RAIZ%salida_servidor.txt" 2>&1
timeout /t 12 >nul
type "%RAIZ%salida_servidor.txt" >> "%LOG%"
echo. >> "%LOG%" & echo --- 9. Respuesta del servidor --- >> "%LOG%"
curl -s http://127.0.0.1:8000/api/salud >> "%LOG%" 2>&1
echo. >> "%LOG%"
curl -s -o nul -w "pagina principal: HTTP %%{http_code}" http://127.0.0.1:8000/ >> "%LOG%" 2>&1
echo. >> "%LOG%"

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do taskkill /f /pid %%p >nul 2>&1

:fin
echo.
echo ============================================================
echo   Listo. Se creo el archivo:
echo   %LOG%
echo   Avisale a Claude que ya quedo el diagnostico.
echo ============================================================
echo.
notepad "%LOG%"
pause
