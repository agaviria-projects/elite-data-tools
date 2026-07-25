from pathlib import Path

import pandas as pd

from ..config.columnas import COLUMNAS_REQUERIDAS
from ..config.parametros import ARCHIVO_FENIX


# ==========================================================
# VALIDAR EXISTENCIA DEL ARCHIVO
# ==========================================================

def validar_archivo() -> None:
    """
    Verifica que el archivo FENIX_ANS.xlsx exista
    en la carpeta de entrada.
    """

    if not ARCHIVO_FENIX.exists():

        raise FileNotFoundError(

            f"\n❌ No se encontró el archivo:\n\n{ARCHIVO_FENIX}"

        )


# ==========================================================
# VALIDAR COLUMNAS
# ==========================================================

def validar_columnas() -> None:
    """
    Verifica que el archivo contenga todas las
    columnas obligatorias.
    """

    columnas_excel = pd.read_excel(

        ARCHIVO_FENIX,

        sheet_name=0,

        nrows=0,

    ).columns.tolist()

    columnas_faltantes = [

        columna

        for columna in COLUMNAS_REQUERIDAS

        if columna not in columnas_excel

    ]

    if columnas_faltantes:

        raise ValueError(

            "\n❌ El archivo no contiene las siguientes columnas:\n\n"
            + "\n".join(columnas_faltantes)

        )


# ==========================================================
# VALIDAR ARCHIVO VACÍO
# ==========================================================

def validar_registros() -> None:
    """
    Verifica que el archivo contenga registros.
    """

    df = pd.read_excel(

        ARCHIVO_FENIX,

        sheet_name=0,

        usecols=["PEDIDO"],

    )

    if df.empty:

        raise ValueError(

            "\n❌ El archivo FENIX_ANS.xlsx no contiene registros."

        )


# ==========================================================
# VALIDACIÓN GENERAL
# ==========================================================

def validar_archivo_fenix() -> None:
    """
    Ejecuta todas las validaciones del archivo.
    """

    validar_archivo()

    validar_columnas()

    validar_registros()