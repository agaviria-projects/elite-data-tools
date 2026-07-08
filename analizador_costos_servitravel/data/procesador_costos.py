import pandas as pd

from analizador_costos_servitravel.data.lector_excel import leer_hoja


# ==========================================
# CARGAR AÑO
# ==========================================

def cargar_anio():

    return leer_hoja("AÑO 2026")


# ==========================================
# CARGAR VIÁTICOS
# ==========================================

def cargar_viaticos():

    return leer_hoja("VIATICOS")


# ==========================================
# CARGAR PARQUEADEROS
# ==========================================

def cargar_parqueaderos():

    return leer_hoja("PARQUEADEROS")


# ==========================================
# CARGAR PEAJES
# ==========================================

def cargar_peajes():

    return leer_hoja("PEAJES")


# ==========================================
# RESUMEN
# ==========================================

def resumen_general():

    return {

        "AÑO 2026": cargar_anio(),

        "VIATICOS": cargar_viaticos(),

        "PARQUEADEROS": cargar_parqueaderos(),

        "PEAJES": cargar_peajes()

    }