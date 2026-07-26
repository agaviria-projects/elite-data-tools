from pathlib import Path

# ==========================================================
# RUTA BASE
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# CARPETAS
# ==========================================================

CARPETA_ENTRADA = BASE_DIR / "entrada"

CARPETA_PROCESADOS = BASE_DIR / "procesados"

CARPETA_HISTORICO = (
    BASE_DIR
    / "data"
    / "historico"
)

CARPETA_SALIDA = BASE_DIR / "salida"

CARPETA_HTML = (
    CARPETA_SALIDA
    / "html"
)

CARPETA_EXCEL = (
    CARPETA_SALIDA
    / "excel"
)

CARPETA_CORREOS = (
    CARPETA_SALIDA
    / "correos"
)

CARPETA_LOG = BASE_DIR / "log"

# ==========================================================
# ARCHIVO DE ENTRADA
# ==========================================================

ARCHIVO_FENIX = (
    CARPETA_ENTRADA
    / "FENIX_ANS.xlsx"
)

# ==========================================================
# SUBZONA A PROCESAR
# ==========================================================

SUBZONA_PROCESAR = "METROPOLITANA SUR"