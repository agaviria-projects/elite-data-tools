import pandas as pd

from config.columnas import COLUMNAS_REQUERIDAS
from config.parametros import (
    ARCHIVO_FENIX,
    SUBZONA_PROCESAR,
)


# ==========================================================
# LEER ARCHIVO FENIX
# ==========================================================

def leer_excel() -> pd.DataFrame:
    """
    Lee el archivo FENIX_ANS.xlsx ubicado en la carpeta
    entrada y retorna únicamente los registros de la
    subzona configurada y las columnas requeridas.
    """

    df = pd.read_excel(
        ARCHIVO_FENIX,
        sheet_name=0,
    )

    # ------------------------------------------------------
    # FILTRAR SUBZONA
    # ------------------------------------------------------

    df = df[
        df["SUBZONA"].astype(str).str.strip().eq(SUBZONA_PROCESAR)
    ].copy()

    # ------------------------------------------------------
    # RETORNAR COLUMNAS REQUERIDAS
    # ------------------------------------------------------

    return df[COLUMNAS_REQUERIDAS].copy()