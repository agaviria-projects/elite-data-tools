import ttkbootstrap as ttk

from pathlib import Path

from ui.base_view import crear_vista

from modules.dashboard_manager import (
    iniciar_dashboard,
    dashboard_activo,
    URL_RED,
    copiar_url
)

# ==========================================
# RUTAS DEL PROYECTO
# ==========================================

BASE = Path(__file__).resolve().parent.parent

# ==========================================
# VARIABLES DE LA INTERFAZ
# ==========================================

lbl_estado = None
lbl_url = None


# ==========================================
# INICIAR DASHBOARD
# ==========================================

def ejecutar_dashboard():

    global lbl_estado
    global lbl_url

    try:

        url = iniciar_dashboard()

        lbl_estado.configure(
            text="🟢 En ejecución",
            bootstyle="success"
        )

        lbl_url.configure(
            text=url
        )

    except Exception as e:

        lbl_estado.configure(
            text="🔴 Error",
            bootstyle="danger"
        )

        lbl_url.configure(
            text=str(e))


# ==========================================
# ANALIZADOR DE COSTOS
# ==========================================

def crear_analizador_costos(panel):

    global lbl_estado
    global lbl_url

    vista = crear_vista(panel)

    # ======================================================
    # VALIDAR ESTADO ACTUAL DEL DASHBOARD
    # ======================================================

    if dashboard_activo():

        estado = "🟢 En ejecución"
        estilo = "success"
        url = URL_RED

    else:

        estado = "🔴 Detenido"
        estilo = "danger"
        url = "No disponible"

    # ======================================================
    # ENCABEZADO
    # ======================================================

    ttk.Label(
        vista,
        text="💰 Analizador de Costos Operativos",
        font=("Segoe UI", 24, "bold"),
        bootstyle="success"
    ).pack(anchor="w", pady=(0, 5))

    ttk.Label(
        vista,
        text="Administración del Dashboard Streamlit",
        font=("Segoe UI", 10)
    ).pack(anchor="w", pady=(0, 20))

    # ======================================================
    # DASHBOARD
    # ======================================================

    panel_dashboard = ttk.Labelframe(
        vista,
        text=" Dashboard ",
        padding=20
    )

    panel_dashboard.pack(
        fill="x",
        pady=(0, 15)
    )

    ttk.Label(
        panel_dashboard,
        text="Estado del Dashboard",
        font=("Segoe UI", 10, "bold")
    ).pack(anchor="w")

    lbl_estado = ttk.Label(
        panel_dashboard,
        text=estado,
        bootstyle=estilo
    )

    lbl_estado.pack(
        anchor="w",
        pady=(0, 15)
    )

    ttk.Label(
        panel_dashboard,
        text="URL",
        font=("Segoe UI", 10, "bold")
    ).pack(anchor="w")

    lbl_url = ttk.Label(
        panel_dashboard,
        text=url
    )

    lbl_url.pack(
        anchor="w",
        pady=(0, 20)
    )

    # ======================================================
    # BOTONES
    # ======================================================

    ttk.Button(
        panel_dashboard,
        text="🚀 Iniciar Dashboard",
        bootstyle="success",
        command=ejecutar_dashboard
    ).pack(fill="x", pady=5)

    ttk.Button(
        panel_dashboard,
        text="📋 Copiar URL",
        bootstyle="secondary",
        command=copiar_url
    ).pack(fill="x", pady=5)