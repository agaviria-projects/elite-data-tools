import ttkbootstrap as ttk

from pathlib import Path
from datetime import datetime

from ui.base_view import crear_vista

from analizador_costos_servitravel.pages.explorador_costos import ExploradorCostos


# ==========================================
# RUTAS
# ==========================================

BASE = Path(__file__).resolve().parent.parent

ARCHIVO = BASE / "SERVITRAVEL" / "salida" / "INFORME_LIQUIDACION.xlsb"


# ==========================================
# FORMATEAR TAMAÑO
# ==========================================

def formatear_tamano(bytes_size):

    if bytes_size < 1024:
        return f"{bytes_size} Bytes"

    elif bytes_size < 1024 ** 2:
        return f"{bytes_size / 1024:.1f} KB"

    elif bytes_size < 1024 ** 3:
        return f"{bytes_size / (1024 ** 2):.2f} MB"

    return f"{bytes_size / (1024 ** 3):.2f} GB"

# ==========================================
# ABRIR EXPLORADOR
# ==========================================

def abrir_explorador(vista):

    for widget in vista.winfo_children():

        widget.destroy()

    ExploradorCostos(vista)

# ==========================================
# ANALIZADOR COSTOS
# ==========================================

def crear_analizador_costos(panel):

    vista = crear_vista(panel)

    ttk.Label(
        vista,
        text="📈 Analizador de Costos Operativos",
        font=("Segoe UI", 24, "bold"),
        bootstyle="success"
    ).pack(anchor="w", pady=(0, 15))

    ttk.Label(
        vista,
        text="Prueba ExploradorCostos"
    ).pack(anchor="w", pady=(0, 10))

    ExploradorCostos(vista)