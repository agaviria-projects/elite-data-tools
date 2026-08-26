"""
==========================================================
SERVITRAVEL
ACTUALIZACIÓN DE FACTURACIÓN
==========================================================

Objetivo:
- Leer Seguimiento facturas.xlsx desde OneDrive.
- Leer únicamente la hoja Vinculaciones.
- Actualizar la hoja FACTURACION del consolidado.
- NO duplicar registros: la hoja destino se reemplaza con
  el estado actual del archivo origen.
- Conservar la estructura de columnas ya existente en
  FACTURACION.
==========================================================
"""

import pandas as pd

from config import (
    ARCHIVO_FACTURACION,
    HOJA_ORIGEN_FACTURACION,
    HOJA_FACTURACION,
)


# ==========================================================
# UTILIDADES
# ==========================================================

def _limpiar_encabezados(df):
    """
    Limpia espacios extremos de los encabezados sin alterar
    sus nombres funcionales.
    """

    df = df.copy()

    df.columns = [
        str(columna).strip()
        for columna in df.columns
    ]

    return df


def _obtener_encabezados_destino(hoja):
    """
    Lee los encabezados actuales de la fila 1 de FACTURACION.
    La propia hoja destino define qué columnas deben conservarse.
    """

    ultima_columna = hoja.used_range.last_cell.column

    valores = hoja.range(
        (1, 1),
        (1, ultima_columna),
    ).value

    if not isinstance(valores, list):
        valores = [valores]

    encabezados = []

    for valor in valores:

        if valor is None:
            continue

        nombre = str(valor).strip()

        if nombre:
            encabezados.append(nombre)

    return encabezados


def _preparar_dataframe_destino(df_origen, encabezados_destino):
    """
    Construye el DataFrame final usando el orden y las columnas
    ya existentes en FACTURACION.

    Si una columna del destino no existe en el origen, se crea
    vacía y se informa en consola.
    """

    df = df_origen.copy()

    # Eliminar filas completamente vacías
    df = df.dropna(how="all").reset_index(drop=True)

    columnas_faltantes = []

    for columna in encabezados_destino:

        if columna not in df.columns:

            df[columna] = pd.NA
            columnas_faltantes.append(columna)

    if columnas_faltantes:

        print(
            "\n⚠ Columnas del destino no encontradas en el origen:"
        )

        for columna in columnas_faltantes:
            print(f"   - {columna}")

        print(
            "   Se conservarán vacías en FACTURACION."
        )

    # Mantener exactamente el orden de la hoja destino
    df = df[encabezados_destino].copy()

    return df


def _limpiar_datos_destino(hoja, cantidad_columnas):
    """
    Borra únicamente los datos existentes debajo de los encabezados.
    No elimina la hoja ni los encabezados.
    """

    ultima_fila = max(
        hoja.used_range.last_cell.row,
        2,
    )

    if ultima_fila >= 2:

        hoja.range(
            (2, 1),
            (ultima_fila, cantidad_columnas),
        ).clear_contents()


def _escribir_dataframe(hoja, df):
    """
    Escribe el DataFrame desde la fila 2, sin volver a escribir
    los encabezados.
    """

    if df.empty:
        return

    hoja.range(
        (2, 1)
    ).options(
        index=False,
        header=False,
    ).value = df


def _copiar_formato_base(hoja, filas, columnas):
    """
    Extiende el formato de la primera fila de datos hacia las demás
    filas escritas, sin modificar valores.
    """

    if filas <= 1:
        return

    try:

        hoja.range(
            (2, 1),
            (2, columnas),
        ).api.Copy()

        hoja.range(
            (3, 1),
            (filas + 1, columnas),
        ).api.PasteSpecial(
            Paste=-4122  # xlPasteFormats
        )

        hoja.api.Application.CutCopyMode = False

    except Exception:

        # El formato es secundario frente a la actualización de datos.
        pass


# ==========================================================
# ACTUALIZAR FACTURACIÓN
# ==========================================================

def actualizar_facturacion(libro):
    """
    Actualiza FACTURACION dentro de INFORME_LIQUIDACION.xlsb.

    IMPORTANTE:
    La actualización es por reemplazo del contenido actual,
    no por anexado acumulativo. Así se evitan duplicados y
    también se reflejan correcciones hechas en el archivo origen.
    """

    print("\n" + "=" * 60)
    print("ACTUALIZANDO FACTURACIÓN")
    print("=" * 60)

    # ------------------------------------------------------
    # VALIDAR ARCHIVO ORIGEN
    # ------------------------------------------------------

    if not ARCHIVO_FACTURACION.exists():

        raise FileNotFoundError(
            "No se encontró el archivo de facturación:\n"
            f"{ARCHIVO_FACTURACION}"
        )

    print(
        f"\nOrigen : {ARCHIVO_FACTURACION.name}"
    )

    print(
        f"Hoja   : {HOJA_ORIGEN_FACTURACION}"
    )

    # ------------------------------------------------------
    # VALIDAR HOJA ORIGEN
    # ------------------------------------------------------

    with pd.ExcelFile(
        ARCHIVO_FACTURACION,
        engine="openpyxl",
    ) as excel:

        if HOJA_ORIGEN_FACTURACION not in excel.sheet_names:

            raise ValueError(
                "No existe la hoja "
                f"'{HOJA_ORIGEN_FACTURACION}' "
                "en el archivo de facturación."
            )

    # ------------------------------------------------------
    # LEER ORIGEN
    # ------------------------------------------------------

    df_origen = pd.read_excel(
        ARCHIVO_FACTURACION,
        sheet_name=HOJA_ORIGEN_FACTURACION,
        engine="openpyxl",
    )

    df_origen = _limpiar_encabezados(
        df_origen
    )

    df_origen = (
        df_origen
        .dropna(how="all")
        .reset_index(drop=True)
    )

    print(
        f"Registros origen : {len(df_origen):,}"
    )

    # ------------------------------------------------------
    # OBTENER HOJA DESTINO
    # ------------------------------------------------------

    try:

        hoja_destino = libro.sheets[
            HOJA_FACTURACION
        ]

    except Exception as error:

        raise ValueError(
            f"No existe la hoja '{HOJA_FACTURACION}' "
            "en INFORME_LIQUIDACION.xlsb."
        ) from error

    # ------------------------------------------------------
    # USAR ESTRUCTURA ACTUAL DEL DESTINO
    # ------------------------------------------------------

    encabezados_destino = (
        _obtener_encabezados_destino(
            hoja_destino
        )
    )

    if not encabezados_destino:

        raise ValueError(
            "La hoja FACTURACION no contiene encabezados "
            "válidos en la fila 1."
        )

    df_destino = _preparar_dataframe_destino(
        df_origen,
        encabezados_destino,
    )

    # ------------------------------------------------------
    # REEMPLAZAR CONTENIDO
    # ------------------------------------------------------

    _limpiar_datos_destino(
        hoja_destino,
        len(encabezados_destino),
    )

    _escribir_dataframe(
        hoja_destino,
        df_destino,
    )

    _copiar_formato_base(
        hoja_destino,
        filas=len(df_destino),
        columnas=len(encabezados_destino),
    )

    print(
        f"Registros destino: {len(df_destino):,}"
    )

    print(
        "\n✅ FACTURACION actualizada correctamente."
    )

    print(
        "✅ No se acumularon registros anteriores."
    )

    print(
        "✅ Se conservó la estructura actual de columnas."
    )
