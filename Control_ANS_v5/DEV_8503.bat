@echo off
cd /d "%~dp0"
call venv\Scripts\activate

REM Desarrollo: solo local + SI se reinicia al guardar
streamlit run routing_app\app.py --server.address 127.0.0.1 --server.port 8503 --server.runOnSave true