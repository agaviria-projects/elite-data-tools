from pathlib import Path
from datetime import datetime
import uuid
import streamlit as st

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "atlas360_accesos.log"


def obtener_sesion():
    if "session_id_atlas360" not in st.session_state:
        st.session_state["session_id_atlas360"] = str(uuid.uuid4())[:8]
    return st.session_state["session_id_atlas360"]


def registrar_evento(evento, detalle=""):
    session_id = obtener_sesion()
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"{fecha_hora} | sesion={session_id} | evento={evento} | detalle={detalle}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linea)