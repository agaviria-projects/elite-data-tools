"""
=========================================================
PROCESO DRACO
=========================================================

Funciones disponibles:

1. Unificar todas las actas:
   python main.py --solo-unificar

2. Generar un acta particular desde DRACO_UNIFICADO.xlsx:
   python main.py --acta 10

3. Ejecución manual:
   python main.py
=========================================================
"""

import argparse
from datetime import datetime
from pathlib import Path
from time import perf_counter

import pandas as pd

from scripts.filtrar_acta import filtrar_acta
from scripts.unificar_draco import unificar_draco


# ==========================================================
# RUTAS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

CARPETA_SALIDA = (
    BASE_DIR
    / "data"
    / "salida"
)

ARCHIVO_UNIFICADO = (
    CARPETA_SALIDA
    / "DRACO_UNIFICADO.xlsx"
)


# ==========================================================
# ARGUMENTOS
# ==========================================================

def obtener_argumentos():

    parser = argparse.ArgumentParser(
        description=(
            "Unificación y generación de informes DRACO"
        )
    )

    parser.add_argument(
        "--acta",
        type=str,
        required=False,
        help=(
            "Número o nombre del acta. "
            "Ejemplo: 10 o ACTA 10"
        )
    )

    parser.add_argument(
        "--solo-unificar",
        action="store_true",
        help=(
            "Genera únicamente el archivo "
            "DRACO_UNIFICADO.xlsx"
        )
    )

    return parser.parse_args()


# ==========================================================
# UTILIDADES
# ==========================================================

def hora_actual():

    return datetime.now().strftime(
        "%H:%M:%S"
    )


def formatear_tiempo(segundos):

    segundos = int(segundos)

    horas, resto = divmod(
        segundos,
        3600
    )

    minutos, segundos = divmod(
        resto,
        60
    )

    return (
        f"{horas:02d}:"
        f"{minutos:02d}:"
        f"{segundos:02d}"
    )


def normalizar_acta(valor_acta):

    if valor_acta is None:
        return None

    acta = str(
        valor_acta
    ).upper().strip()

    if not acta:
        return None

    # Permite recibir:
    # 10
    # "10"
    # "ACTA 10"
    if acta.isdigit():
        acta = f"ACTA {acta}"

    return acta


def obtener_numero_acta(acta):

    return (
        acta
        .replace("ACTA", "")
        .strip()
    )


# ==========================================================
# CARGAR UNIFICADO
# ==========================================================

def cargar_unificado():

    if not ARCHIVO_UNIFICADO.exists():

        raise FileNotFoundError(
            "\nNo existe el archivo "
            "DRACO_UNIFICADO.xlsx.\n\n"
            "Primero ejecute la opción "
            "SOLO UNIFICAR."
        )

    return pd.read_excel(
        ARCHIVO_UNIFICADO
    )


# ==========================================================
# SOLO UNIFICAR
# ==========================================================

def ejecutar_unificacion(inicio):

    print("")
    print(
        f"[{hora_actual()}] "
        "📂 Iniciando unificación de archivos..."
    )
    print("")

    unificar_draco()

    duracion = (
        perf_counter()
        - inicio
    )

    print("")
    print("─" * 60)
    print(
        f"[{hora_actual()}] "
        "✅ DRACO_UNIFICADO.xlsx generado"
    )
    print(
        f"[{hora_actual()}] "
        f"⏱ Tiempo total: "
        f"{formatear_tiempo(duracion)}"
    )
    print("─" * 60)


# ==========================================================
# GENERAR ACTA PARTICULAR
# ==========================================================

def ejecutar_acta_particular(
    acta,
    inicio
):

    numero_acta = obtener_numero_acta(
        acta
    )

    archivo_salida_acta = (
        CARPETA_SALIDA
        / f"DRACO_ACTA_{numero_acta}.xlsx"
    )

    print("")
    print(
        f"[{hora_actual()}] "
        "📂 Cargando DRACO_UNIFICADO.xlsx"
    )

    print(
        f"[{hora_actual()}] "
        f"📁 Ruta: {ARCHIVO_UNIFICADO}"
    )

    df_final = cargar_unificado()

    cantidad_registros = (
        f"{len(df_final):,}"
        .replace(",", ".")
    )

    print(
        f"[{hora_actual()}] "
        f"📊 Registros disponibles: "
        f"{cantidad_registros}"
    )

    print("")
    print(
        f"[{hora_actual()}] "
        f"📌 Generando informe {acta}"
    )

    filtrar_acta(
        df_final,
        acta
    )

    duracion = (
        perf_counter()
        - inicio
    )

    print("")
    print("─" * 60)
    print(
        f"[{hora_actual()}] "
        f"✅ DRACO_ACTA_{numero_acta}.xlsx generado"
    )
    print(
        f"[{hora_actual()}] "
        f"📁 Ruta: {archivo_salida_acta}"
    )
    print(
        f"[{hora_actual()}] "
        f"⏱ Tiempo total: "
        f"{formatear_tiempo(duracion)}"
    )
    print("─" * 60)


# ==========================================================
# MAIN
# ==========================================================

def main():

    inicio = perf_counter()

    print("=" * 60)
    print(
        f"[{hora_actual()}] "
        "▶ Inicio del proceso DRACO"
    )
    print("=" * 60)

    argumentos = obtener_argumentos()

    # ------------------------------------------------------
    # SOLO UNIFICAR
    # ------------------------------------------------------

    if argumentos.solo_unificar:

        ejecutar_unificacion(
            inicio
        )

        return

    # ------------------------------------------------------
    # GENERAR ACTA PARTICULAR
    # ------------------------------------------------------

    acta = normalizar_acta(
        argumentos.acta
    )

    # Mantiene la ejecución manual
    if acta is None:

        acta = input(
            "\n📌 Ingrese el número de acta "
            "(Ej: ACTA 10): "
        )

        acta = normalizar_acta(
            acta
        )

    if acta is None:

        raise ValueError(
            "No se proporcionó un número "
            "de acta válido."
        )

    ejecutar_acta_particular(
        acta,
        inicio
    )


# ==========================================================
# EJECUTAR
# ==========================================================

if __name__ == "__main__":

    main()