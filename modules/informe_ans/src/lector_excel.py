import pandas as pd

from ..config.columnas import COLUMNAS_REQUERIDAS
from ..config.parametros import ARCHIVO_FENIX


# ==========================================================
# LEER ARCHIVO FENIX
# ==========================================================

def leer_excel() -> pd.DataFrame:
    """
    Lee FENIX_ANS.xlsx y retorna la información necesaria
    para Seguimiento ANS.

    No filtra la subzona.

    La selección de METROPOLITANA, SUROESTE, OCCIDENTE
    o TODAS se realiza posteriormente desde runner.py.
    """

    df = pd.read_excel(
        ARCHIVO_FENIX,
        sheet_name=0,
    )

    # ------------------------------------------------------
    # VALIDAR SUBZONA
    # ------------------------------------------------------

    if "SUBZONA" not in df.columns:
        raise ValueError(
            "El archivo FENIX no contiene la columna SUBZONA."
        )

    # ------------------------------------------------------
    # CONSERVAR COLUMNAS REQUERIDAS + SUBZONA
    # ------------------------------------------------------

    columnas_salida = list(
        dict.fromkeys(
            COLUMNAS_REQUERIDAS
            + ["SUBZONA"]
        )
    )

    return df[
        columnas_salida
    ].copy()