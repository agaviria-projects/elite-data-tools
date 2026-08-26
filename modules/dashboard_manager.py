from pathlib import Path

import socket
import subprocess
import sys
import time
import tkinter as tk
import webbrowser

import requests

from ttkbootstrap.dialogs import Messagebox


# ==========================================================
# RUTAS
# ==========================================================

BASE = Path(__file__).resolve().parent.parent

APP_STREAMLIT = (
    BASE
    / "analizador_costos_servitravel"
    / "app.py"
)

PUERTO = 8501

URL_LOCAL = f"http://localhost:{PUERTO}"


# ==========================================================
# OBTENER IP LOCAL
# ==========================================================

def obtener_ip():

    try:

        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        s.connect(
            ("8.8.8.8", 80)
        )

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception:

        return "localhost"


URL_RED = f"http://{obtener_ip()}:{PUERTO}"


# ==========================================================
# PROCESO
# ==========================================================

_proceso = None


# ==========================================================
# DASHBOARD ACTIVO
# ==========================================================

def dashboard_activo():

    try:

        respuesta = requests.get(
            URL_LOCAL,
            timeout=1
        )

        return respuesta.status_code == 200

    except Exception:

        return False


# ==========================================================
# ESPERAR DASHBOARD
# ==========================================================

def esperar_dashboard(timeout=15):

    inicio = time.time()

    while time.time() - inicio < timeout:

        if dashboard_activo():

            return True

        time.sleep(0.5)

    return False


# ==========================================================
# INICIAR DASHBOARD
# ==========================================================

def iniciar_dashboard():

    global _proceso

    # ======================================================
    # SI YA ESTÁ EJECUTÁNDOSE
    # ======================================================

    if dashboard_activo():

        webbrowser.open(
            URL_LOCAL,
            new=1
        )

        return URL_RED

    # ======================================================
    # VALIDAR EXISTENCIA
    # ======================================================

    if not APP_STREAMLIT.exists():

        raise FileNotFoundError(
            f"No existe:\n\n{APP_STREAMLIT}"
        )

    # ======================================================
    # EJECUTAR STREAMLIT
    #
    # IMPORTANTE:
    # --server.headless=true evita que Streamlit
    # abra automáticamente una pestaña del navegador.
    #
    # DataSuite será quien abra la URL una sola vez.
    # ======================================================

    _proceso = subprocess.Popen(

        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",

            "--server.address",
            "0.0.0.0",

            "--server.port",
            str(PUERTO),

            "--server.headless",
            "true",
        ],

        cwd=APP_STREAMLIT.parent,

        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # ======================================================
    # ESPERAR A QUE STREAMLIT RESPONDA
    # ======================================================

    if esperar_dashboard():

        webbrowser.open(
            URL_LOCAL,
            new=1
        )

        return URL_RED

    raise RuntimeError(
        "No fue posible iniciar el Dashboard de Streamlit."
    )


# ==========================================================
# COPIAR URL
# ==========================================================

def copiar_url():

    root = tk.Tk()

    root.withdraw()

    root.clipboard_clear()

    root.clipboard_append(
        URL_RED
    )

    root.update()

    root.destroy()

    Messagebox.show_info(

        title="Dashboard Streamlit",

        message=(
            "✅ URL copiada correctamente.\n\n"
            f"{URL_RED}"
        ),
    )

    return URL_RED