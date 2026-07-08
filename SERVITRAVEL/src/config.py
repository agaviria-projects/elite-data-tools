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

ARCHIVO_CONSOLIDADO = CARPETA_SALIDA / "INFORME_LIQUIDACION.xlsb"

# ==========================================================
# HOJAS DEL CONSOLIDADO
# ==========================================================

HOJA_ANIO = "AÑO 2026"
HOJA_VIATICOS = "VIATICOS"
HOJA_PARQUEADEROS = "PARQUEADEROS"
HOJA_PEAJES = "PEAJES"
