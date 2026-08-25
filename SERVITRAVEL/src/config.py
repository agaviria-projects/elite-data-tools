from pathlib import Path

# ==========================================================
# RUTAS DEL PROYECTO
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CARPETA_ENTRADA = BASE_DIR / "entrada"
CARPETA_SALIDA = BASE_DIR / "salida"
CARPETA_BACKUP = BASE_DIR / "backup"
CARPETA_PROCESADOS = BASE_DIR / "procesados"
CARPETA_LOGS = BASE_DIR / "logs"

# ==========================================================
# ARCHIVOS
# ==========================================================

ARCHIVO_CONSOLIDADO = (
    CARPETA_SALIDA
    / "INFORME_LIQUIDACION.xlsb"
)

# ==========================================================
# ARCHIVO FACTURACION
# ==========================================================

ARCHIVO_FACTURACION = Path(
    r"C:\Users\hector.gaviria\Elite Ingenieros SAS"
    r"\Alejandra Lopez Arango - 7.FACTURACIÓN"
    r"\Seguimiento facturas.xlsx"
)

# ==========================================================
# HOJAS DEL CONSOLIDADO
# ==========================================================

HOJA_RODAMIENTOS = "RODAMIENTOS"
HOJA_VIATICOS = "VIATICOS"
HOJA_PARQUEADEROS = "PARQUEADEROS"
HOJA_PEAJES = "PEAJES"
HOJA_FACTURACION = "FACTURACION"

# ==========================================================
# HOJA ORIGEN FACTURACION
# ==========================================================

HOJA_ORIGEN_FACTURACION = "Vinculaciones"

# ==========================================================
# NORMALIZACION FUTURA
# ==========================================================
# Todavía NO se aplica.
#
# Más adelante:
#
# CAMION
# CAMIONETA
# VANS
#
#          ↓
#
# SERVICIOS TEMPORALES
# ==========================================================

CONCEPTOS_SERVICIOS_TEMPORALES = {
    "CAMION",
    "CAMIONETA",
    "VANS",
}

CONCEPTO_SERVICIOS_TEMPORALES = "SERVICIOS TEMPORALES"