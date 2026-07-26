from datetime import datetime
from shutil import copy2, move

from config.parametros import (
    ARCHIVO_FENIX,
    CARPETA_HISTORICO,
    CARPETA_PROCESADOS,
)


# ==========================================================
# CREAR CARPETAS
# ==========================================================

def crear_carpetas():
    """
    Crea las carpetas necesarias del proyecto.
    """

    CARPETA_HISTORICO.mkdir(
        parents=True,
        exist_ok=True,
    )

    CARPETA_PROCESADOS.mkdir(
        parents=True,
        exist_ok=True,
    )


# ==========================================================
# GENERAR NOMBRE DEL CORTE
# ==========================================================

def generar_nombre_corte():
    """
    Genera el nombre del archivo utilizando
    la fecha y hora del procesamiento.
    """

    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"FENIX_ANS_{fecha}.xlsx"


# ==========================================================
# GUARDAR HISTÓRICO
# ==========================================================

def guardar_historico():
    """
    Guarda una copia del archivo de entrada
    en la carpeta data/historico.
    """

    crear_carpetas()

    nombre = generar_nombre_corte()

    destino = CARPETA_HISTORICO / nombre

    copy2(
        ARCHIVO_FENIX,
        destino,
    )

    return destino


# ==========================================================
# MOVER A PROCESADOS
# ==========================================================

def mover_a_procesados():
    """
    Mueve el archivo procesado a la carpeta
    procesados conservando la fecha del corte.
    """

    crear_carpetas()

    nombre = generar_nombre_corte()

    destino = CARPETA_PROCESADOS / nombre

    move(
        ARCHIVO_FENIX,
        destino,
    )

    return destino


# ==========================================================
# REGISTRAR CORTE
# ==========================================================

def registrar_corte():
    """
    Registra el corte actual.

    1. Guarda una copia en histórico.
    2. Mueve el archivo original a procesados.
    """

    ruta_historico = guardar_historico()

    ruta_procesado = mover_a_procesados()

    return {

        "historico": ruta_historico,

        "procesado": ruta_procesado,

    }