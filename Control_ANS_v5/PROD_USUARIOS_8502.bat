@echo off
cd /d "%~dp0"

REM 1) Activar entorno virtual (solo en este .bat)
call venv\Scripts\activate

REM 2) Levantar Streamlit para la red (IP:8502)
start "ENRUTAMIENTO_8502" cmd /k streamlit run routing_app\app.py --server.address 0.0.0.0 --server.port 8502 --server.runOnSave false

REM 3) Abrir el Panel (elige UNA)
REM --- Si tu panel es .exe:
REM start "" "PanelControlANS.exe"

REM --- Si tu panel es python:
REM start "PANEL" cmd /k python panel.py

echo.
echo ✅ Listo: Streamlit en http://TU_IP:8502
echo.
pause