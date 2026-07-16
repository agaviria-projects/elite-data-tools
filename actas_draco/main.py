from pathlib import Path

import argparse
import pandas as pd

from scripts.unificar_draco import unificar_draco
from scripts.filtrar_acta import filtrar_acta


BASE_DIR = Path(__file__).resolve().parent
ARCHIVO_UNIFICADO = (
    BASE_DIR
    / "data"
    / "salida"
    / "DRACO_UNIFICADO.xlsx"
)


def obtener_argumentos():

    parser = argparse.ArgumentParser(
        description="Unificación y generación de informes DRACO"
    )

    parser.add_argument(
        "--acta",
        type=str,
        required=False,
        help="Número o nombre del acta. Ejemplo: 8 o ACTA 8"
    )

    parser.add_argument(
        "--solo-unificar",
        action="store_true",
        help="Genera únicamente el archivo DRACO_UNIFICADO.xlsx"
    )

    return parser.parse_args()


def normalizar_acta(valor_acta):

    if valor_acta is None:
        return None

    acta = str(valor_acta).upper().strip()

    if not acta:
        return None

    if acta.isdigit():
        acta = f"ACTA {acta}"

    return acta


def cargar_unificado():

    if not ARCHIVO_UNIFICADO.exists():

        raise FileNotFoundError(
            "No existe DRACO_UNIFICADO.xlsx.\n"
            "Primero ejecute la opción SOLO UNIFICAR."
        )

    print("=" * 50)
    print("📂 CARGANDO DRACO UNIFICADO")
    print(f"📁 Ruta: {ARCHIVO_UNIFICADO}")
    print("=" * 50)

    return pd.read_excel(
        ARCHIVO_UNIFICADO
    )


def main():

    print("=" * 50)
    print("🚀 INICIANDO PROCESO DRACO")
    print("=" * 50)

    argumentos = obtener_argumentos()

    # ======================================
    # SOLO UNIFICAR
    # ======================================

    if argumentos.solo_unificar:

        unificar_draco()

        print("")
        print("=" * 50)
        print("✅ PROCESO DE UNIFICACIÓN FINALIZADO")
        print("📄 Archivo generado: DRACO_UNIFICADO.xlsx")
        print("=" * 50)

        return

    # ======================================
    # ACTA PARTICULAR
    # ======================================

    acta = normalizar_acta(
        argumentos.acta
    )

    # Ejecución manual
    if acta is None:

        acta = input(
            "\n📌 Ingrese el número de acta "
            "(Ej: ACTA 8): "
        )

        acta = normalizar_acta(
            acta
        )

    if acta is None:

        raise ValueError(
            "No se proporcionó un número de acta válido."
        )

    print(
        f"\n📌 Acta seleccionada: {acta}"
    )

    # Leer el consolidado existente
    df_final = cargar_unificado()

    # Generar solo el acta solicitada
    filtrar_acta(
        df_final,
        acta
    )

    print("")
    print("=" * 50)
    print("✅ PROCESO FINALIZADO")
    print("=" * 50)


if __name__ == "__main__":

    main()