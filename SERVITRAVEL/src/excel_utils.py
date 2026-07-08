"""
==========================================================
SERVITRAVEL
UTILIDADES EXCEL
==========================================================

Este módulo contiene todas las funciones de acceso a Excel.

"""

from pathlib import Path
import shutil
from datetime import datetime

import pandas as pd
import xlwings as xw

# ==========================================================
# BACKUP
# ==========================================================

def crear_backup(archivo_excel: Path, carpeta_backup: Path):

    carpeta_backup.mkdir(exist_ok=True)

    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")

    destino = carpeta_backup / f"{archivo_excel.stem}_{fecha}{archivo_excel.suffix}"

    shutil.copy2(archivo_excel, destino)

    print(f"✓ Backup creado:\n{destino.name}")

    return destino


# ==========================================================
# ABRIR EXCEL
# ==========================================================

def abrir_excel(archivo: Path):

    if not archivo.exists():

        raise FileNotFoundError(
            f"No existe el archivo:\n{archivo}"
        )

    app = xw.App(visible=False)

    app.display_alerts = False
    app.screen_updating = False

    libro = app.books.open(str(archivo))

    return app, libro


# ==========================================================
# CERRAR EXCEL
# ==========================================================

def cerrar_excel(app, libro):

    try:
        libro.save()
    finally:
        libro.close()
        app.quit()

# ==========================================================
# BUSCAR FILA DE ENCABEZADOS
# ==========================================================

COLUMNAS_ANIO = {
    "PLACA",
    "TIPO",
    "FECHA",
    "INGRESO",
    "SALIDA"
}

COLUMNAS_VIATICOS = {
    "PLACA",
    "FECHA VIATICOS",
    "TOTAL VIATICOS"
}

COLUMNAS_PARQUEADEROS = {
    "FECHA",
    "PLACA",
    "CANTIDAD",
    "TOTAL PARQUEADEROS"
}

COLUMNAS_PEAJES = {
    "FECHA",
    "PLACA",
    "CANT PEAJES",
    "VALOR PEAJE"
}
import re

# ==========================================================
# NORMALIZAR ENCABEZADOS
# ==========================================================

def normalizar_encabezado(nombre):

    nombre = str(nombre).strip().upper()

    # Unificar espacios
    nombre = re.sub(r"\s+", " ", nombre)

    # MIN HORAS -> MIN HORA
    if nombre == "MIN HORAS":
        return "MIN HORA"

    # KM EXTRA DESPUES DE 90 / 110 / 120...
    if nombre.startswith("KM EXTRA DESPUES DE"):
        return "KM EXTRA DESPUES DE"

    if nombre == "TOTAL PARQUEADERO":
        return "TOTAL PARQUEADEROS"

    return nombre

def buscar_encabezados(hoja, columnas_obligatorias):
    """
    Busca automáticamente la fila donde están los encabezados.

    Retorna:
        fila_encabezado
        columnas -> diccionario con la posición de cada columna
    """

    ultima_fila = hoja.used_range.last_cell.row
    ultima_columna = hoja.used_range.last_cell.column

    for fila in range(1, ultima_fila + 1):

        encabezados = {}

        encontrados = set()

        for columna in range(1, ultima_columna + 1):

            valor = hoja.cells(fila, columna).value

            if valor is None:
                continue

            nombre = str(valor).strip().upper()

            encabezados[nombre] = columna

            if nombre in columnas_obligatorias:
                encontrados.add(nombre)

        # Si encontró todas las columnas obligatorias,
        # esta es la fila del encabezado.

        # if fila <= 10:
        #     print(f"\nFila {fila}: {encabezados}")

        if columnas_obligatorias.issubset(encontrados):

            print(f"✓ Encabezados encontrados en fila {fila}")

            return fila, encabezados

    raise Exception(
        "No fue posible localizar los encabezados del archivo."
    )

# ==========================================================
# LEER TABLA ORIGEN
# ==========================================================

def leer_tabla(
    archivo_excel,
    nombre_hoja,
    columnas_obligatorias
):

    print(f"Leyendo: {archivo_excel.name}")

    app, libro = abrir_excel(archivo_excel)

    try:

        hoja = libro.sheets[nombre_hoja]

    except Exception as e:

        print(f"\n❌ Error al abrir la hoja '{nombre_hoja}'")
        print(f"Detalle: {e}")

        print("\n📋 Hojas disponibles:")

        for hoja_libro in libro.sheets:
            print(f"   - {hoja_libro.name}")

        cerrar_excel(app, libro)

        return None, None


    # Buscar automáticamente la fila de encabezados
    fila_encabezado, columnas = buscar_encabezados(
        hoja,
        columnas_obligatorias
    )

    # Obtener el rango real utilizado
    ultima_fila = hoja.used_range.last_cell.row
    ultima_columna = hoja.used_range.last_cell.column

    # Leer toda la tabla
    rango = hoja.range(
        (fila_encabezado, 1),
        (ultima_fila, ultima_columna)
    )

    df = rango.options(
        pd.DataFrame,
        header=1,
        index=False
    ).value

    cerrar_excel(app, libro)

    # Normalizar encabezados
    df.columns = [normalizar_encabezado(c) for c in df.columns]

    # Eliminar filas completamente vacías
    df = df.dropna(how="all")

    # Eliminar registros sin placa
    df = df[df["PLACA"].notna()]

    df = df.reset_index(drop=True)

    return df, columnas


# ==========================================================
# BUSCAR ÚLTIMA FILA
# ==========================================================

def ultima_fila(hoja):

    return hoja.range("A1048576").end("up").row


# ==========================================================
# ESCRIBIR DATAFRAME
# ==========================================================

def escribir_dataframe(
    hoja,
    fila_inicio,
    dataframe
):

    # ==========================================
    # RELLENAR VACÍOS
    # ==========================================

    columnas_cero = [
        "PEAJES",
        "KM EXTRA DESPUES DE 90",
        "VALOR KM EXTRA",
        "HORAS EXTRA",
        "VALOR HORA EXTRA"
    ]

    for columna in columnas_cero:

        if columna in dataframe.columns:

            dataframe[columna] = dataframe[columna].fillna(0)

    if "OBSERVACION" in dataframe.columns:

        dataframe["OBSERVACION"] = dataframe["OBSERVACION"].fillna("")

    # ==========================================
    # ESCRIBIR
    # ==========================================

    hoja.range(
        (fila_inicio, 1)
    ).options(
        index=False,
        header=False
    ).value = dataframe

    # ==========================================
    # CENTRAR CELDAS
    # ==========================================

    filas = len(dataframe)
    columnas = len(dataframe.columns)

    rango = hoja.range(
        (fila_inicio, 1),
        (fila_inicio + filas - 1, columnas)
    )

    # Centrado horizontal
    rango.api.HorizontalAlignment = -4108

    # Centrado vertical
    rango.api.VerticalAlignment = -4108

    # ==========================================
    # COPIAR FORMATO DE LA FILA ANTERIOR
    # ==========================================

    fila_formato = fila_inicio - 1

    hoja.range(
        (fila_formato, 1),
        (fila_formato, columnas)
    ).api.Copy()

    hoja.range(
        (fila_inicio, 1),
        (fila_inicio + filas - 1, columnas)
    ).api.PasteSpecial(Paste=-4122)

    # Limpiar portapapeles
    hoja.api.Application.CutCopyMode = False
# ==========================================================
# OBTENER MES
# ==========================================================

MESES = {

    1: "ENERO",
    2: "FEBRERO",
    3: "MARZO",
    4: "ABRIL",
    5: "MAYO",
    6: "JUNIO",
    7: "JULIO",
    8: "AGOSTO",
    9: "SEPTIEMBRE",
    10: "OCTUBRE",
    11: "NOVIEMBRE",
    12: "DICIEMBRE"

}


def obtener_mes(fecha):

    if pd.isna(fecha):

        return ""

    try:

        fecha = pd.to_datetime(fecha)

        return MESES[fecha.month]

    except Exception:

        return ""

# ==========================================================
# OBTENER CORTE
# ==========================================================

def obtener_corte(fecha):

    if pd.isna(fecha):

        return ""

    try:

        fecha = pd.to_datetime(fecha)

        if fecha.day <= 15:
            return "1 CORTE"

        return "2 CORTE"

    except Exception:

        return ""
# ==========================================================
# OBTENER ZONA
# ==========================================================

def obtener_zona(nombre_archivo):

    nombre = Path(nombre_archivo).stem.upper()

    equivalencias = {

        "METROPOLITANO": "METROPOLITANA",

        "METROPOLITANA": "METROPOLITANA",

        "OCCIDENTE": "OCCIDENTE",

        "ORIENTE": "ORIENTE",

        "NORDESTE": "NORDESTE",

        "SUROESTE": "SUROESTE"

    }

    return equivalencias.get(
        nombre,
        nombre
    )

# ==========================================================
# OBTENER COLUMNAS DEL DESTINO
# ==========================================================

def obtener_columnas_destino(hoja):
    """
    Busca los encabezados del consolidado AÑO 2026.
    """

    return buscar_encabezados(
        hoja,
        COLUMNAS_ANIO
    )

def construir_dataframe_destino(df_origen, zona):

    df = pd.DataFrame(index=df_origen.index)

    # ======================================================
    # COLUMNAS CALCULADAS
    # ======================================================

    df["ZONA"] = zona
    df["MES"] = df_origen["FECHA"].apply(obtener_mes)

    # ======================================================
    # COLUMNAS DIRECTAS
    # ======================================================

    df["PLACA"] = df_origen["PLACA"]
    df["TIPO"] = df_origen["TIPO"]
    df["FECHA"] = df_origen["FECHA"]
    df["INGRESO"] = df_origen["INGRESO"]
    df["SALIDA"] = df_origen["SALIDA"]
    df["HORAS TRABAJADAS"] = df_origen["HORAS TRABAJADAS"]
    df["ALMUERZO"] = df_origen["ALMUERZO"]
    df["HORAS EXTRA"] = df_origen["HORAS EXTRA"]
    df["VALOR HORA EXTRA"] = df_origen["VALOR HORA EXTRA"]
    df["TOTAL HORAS"] = df_origen["TOTAL HORAS"]
    df["PEAJES"] = df_origen["PEAJES"]
    df["VALOR KM EXTRA"] = df_origen["VALOR KM EXTRA"]
    df["VALOR ÉLITE"] = df_origen["VALOR ÉLITE"]
    df["OBSERVACION"] = df_origen["OBSERVACION"]

    df["MIN HORAS"] = df_origen["MIN HORA"]

    df["KM EXTRA DESPUES DE 90"] = df_origen["KM EXTRA DESPUES DE"]

    # ======================================================
    # REORDENAR COLUMNAS
    # ======================================================

    df = df[
        [
            "ZONA",
            "MES",
            "PLACA",
            "TIPO",
            "FECHA",
            "INGRESO",
            "SALIDA",
            "HORAS TRABAJADAS",
            "ALMUERZO",
            "MIN HORAS",
            "HORAS EXTRA",
            "VALOR HORA EXTRA",
            "TOTAL HORAS",
            "PEAJES",
            "KM EXTRA DESPUES DE 90",
            "VALOR KM EXTRA",
            "VALOR ÉLITE",
            "OBSERVACION",
        ]
    ]

    return df

# ==========================================================
# CONSTRUIR DATAFRAME DESTINO VIATICOS
# ==========================================================

def construir_dataframe_viaticos(df_origen, zona):

    df_origen = df_origen.copy()

    # Eliminar fila de total
    df_origen = df_origen[
        df_origen["PLACA"].astype(str).str.upper() != "TOTAL"
    ]

    df = pd.DataFrame(index=df_origen.index)

    df["ZONA"] = zona
    df["PLACA"] = df_origen["PLACA"]
    df["FECHA VIATICOS"] = df_origen["FECHA VIATICOS"]
    df["TOTAL VIATICOS"] = df_origen["TOTAL VIATICOS"]

    df = df.reset_index(drop=True)

    return df

# ==========================================================
# CONSTRUIR DATAFRAME DESTINO PARQUEADEROS
# ==========================================================

def construir_dataframe_parqueaderos(df_origen, zona):

    df_origen = df_origen.copy()

    # Eliminar fila de total
    df_origen = df_origen[
        df_origen["PLACA"].astype(str).str.upper() != "TOTAL"
    ]

    df = pd.DataFrame(index=df_origen.index)

    df["ZONA"] = zona
    df["FECHA"] = df_origen["FECHA"]
    df["PLACA"] = df_origen["PLACA"]
    df["CANTIDAD"] = df_origen["CANTIDAD"]
    df["TOTAL PARQUEADEROS"] = df_origen["TOTAL PARQUEADEROS"]

    df = df.reset_index(drop=True)

    return df

# ==========================================================
# CONSTRUIR DATAFRAME DESTINO PEAJES
# ==========================================================

def construir_dataframe_peajes(df_origen, zona):

    df_origen = df_origen.copy()

    # Eliminar fila de total
    df_origen = df_origen[
        df_origen["PLACA"].astype(str).str.upper() != "TOTAL"
    ]

    df = pd.DataFrame(index=df_origen.index)

    df["ZONA"] = zona

    df["FECHA EN LA QUE SE CAUSA EL PEAJE"] = df_origen["FECHA"]

    df["PLACA"] = df_origen["PLACA"]

    df["CORTE EN EL QUE SE FACTURA"] = (
        df_origen["FECHA"].apply(obtener_corte)
    )

    df["MES EN EL QUE SE FACTURA"] = (
        df_origen["FECHA"].apply(obtener_mes)
    )

    df["CANTIDAD PEAJES"] = df_origen["CANT PEAJES"]

    df["VALOR PEAJE"] = df_origen["VALOR PEAJE"]

    df["TOTAL PEAJES"] = (
        pd.to_numeric(df["CANTIDAD PEAJES"], errors="coerce").fillna(0)
        *
        pd.to_numeric(df["VALOR PEAJE"], errors="coerce").fillna(0)
    )
    # ======================================================
    # REORDENAR COLUMNAS
    # ======================================================

    df = df[
        [
            "ZONA",
            "FECHA EN LA QUE SE CAUSA EL PEAJE",
            "PLACA",
            "CORTE EN EL QUE SE FACTURA",
            "MES EN EL QUE SE FACTURA",
            "CANTIDAD PEAJES",
            "VALOR PEAJE",
            "TOTAL PEAJES",
        ]
    ]

    df = df.reset_index(drop=True)

    return df

# ==========================================================
# IMPRIMIR RESUMEN
# ==========================================================

def imprimir_resumen(nombre, resumen_zonas, total_registros):

    print("\n" + "=" * 60)
    print(f"RESUMEN {nombre}")
    print("=" * 60)

    for zona, cantidad in resumen_zonas.items():

        print(f"{zona:<15} : {cantidad:>5} registros")

    print("-" * 60)
    print(f"{'TOTAL':<15} : {total_registros:>5} registros")
    print("=" * 60)