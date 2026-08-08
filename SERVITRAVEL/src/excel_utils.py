"""
==========================================================
SERVITRAVEL
UTILIDADES EXCEL
==========================================================

Este módulo contiene todas las funciones de acceso a Excel.

"""

from pathlib import Path
import re
import shutil
import unicodedata
from datetime import datetime

import pandas as pd
import xlwings as xw


# ==========================================================
# CONFIGURACIÓN DE NORMALIZACIÓN
# ==========================================================

# Las claves se registran en una forma "limpia" sin tildes,
# espacios especiales ni diferencias entre mayúsculas/minúsculas.
# Los valores corresponden al nombre canónico utilizado por SERVITRAVEL.
#
# Para agregar una nueva equivalencia:
#
#     "NOMBRE RECIBIDO": "NOMBRE ESPERADO",
#
EQUIVALENCIAS_ENCABEZADOS = {
    "KM EXTRA DESPUES DE 90": "KM EXTRA DESPUES DE",
    "KM EXTRA DESPUES DE 100": "KM EXTRA DESPUES DE",
    "KM EXTRA DESPUES DE 110": "KM EXTRA DESPUES DE",
    "KM EXTRA DESPUES DE 120": "KM EXTRA DESPUES DE",
    "KM EXTRA DESPUES DE": "KM EXTRA DESPUES DE",
    "TOTAL PARQUEADERO": "TOTAL PARQUEADEROS",
    "TOTAL PARQUEADEROS": "TOTAL PARQUEADEROS",
    "MIN HORAS": "MIN HORA",
    "MIN HORA": "MIN HORA",
    "OBSERVACION": "OBSERVACION",
    "OBSERVACIONES": "OBSERVACION",
    "VALOR ELITE": "VALOR ÉLITE",
    "VALOR HORA EXTRA": "VALOR HORA EXTRA",
    "HORAS EXTRA": "HORAS EXTRA",
    "HORAS TRABAJADAS": "HORAS TRABAJADAS",
    "TOTAL HORAS": "TOTAL HORAS",
    "VALOR KM EXTRA": "VALOR KM EXTRA",
    "FECHA VIATICOS": "FECHA VIATICOS",
    "TOTAL VIATICOS": "TOTAL VIATICOS",
    "CANT PEAJES": "CANT PEAJES",
    "CANT PEAJE": "CANT PEAJES",
    "CANTIDAD PEAJES": "CANT PEAJES",
    "CANTIDAD DE PEAJES": "CANT PEAJES",
    "VALOR PEAJE": "VALOR PEAJE",
}

# Columnas que construir_dataframe_destino() consume directamente
# y que pueden crearse con un valor seguro cuando el usuario no las
# suministra en el archivo de origen.
COLUMNAS_OPCIONALES_NUMERICAS = {
    "HORAS TRABAJADAS",
    "ALMUERZO",
    "MIN HORA",
    "HORAS EXTRA",
    "VALOR HORA EXTRA",
    "TOTAL HORAS",
    "PEAJES",
    "KM EXTRA DESPUES DE",
    "VALOR KM EXTRA",
    "VALOR ÉLITE",
}

COLUMNAS_OPCIONALES_TEXTO = {
    "OBSERVACION",
}


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

    archivo = Path(archivo)

    if not archivo.exists():

        raise FileNotFoundError(
            f"No existe el archivo:\n{archivo}"
        )

    app = xw.App(visible=False)

    app.display_alerts = False
    app.screen_updating = False

    try:
        libro = app.books.open(str(archivo))
    except Exception:
        app.quit()
        raise

    return app, libro


# ==========================================================
# CERRAR EXCEL
# ==========================================================

def cerrar_excel(app, libro):

    try:
        libro.save()
    finally:
        try:
            libro.close()
        finally:
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


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def _texto_base_encabezado(nombre):
    """
    Convierte un encabezado a una forma comparable y estable.
    No representa necesariamente el nombre final usado por el ETL.
    """

    if nombre is None:
        return ""

    try:
        if pd.isna(nombre):
            return ""
    except (TypeError, ValueError):
        pass

    texto = str(nombre)

    # Normalizar distintas representaciones Unicode.
    texto = unicodedata.normalize("NFKC", texto)

    # Espacios y caracteres invisibles frecuentes provenientes de Excel.
    texto = (
        texto
        .replace("\u00A0", " ")
        .replace("\u1680", " ")
        .replace("\u180E", "")
        .replace("\u2000", " ")
        .replace("\u2001", " ")
        .replace("\u2002", " ")
        .replace("\u2003", " ")
        .replace("\u2004", " ")
        .replace("\u2005", " ")
        .replace("\u2006", " ")
        .replace("\u2007", " ")
        .replace("\u2008", " ")
        .replace("\u2009", " ")
        .replace("\u200A", " ")
        .replace("\u200B", "")
        .replace("\u200C", "")
        .replace("\u200D", "")
        .replace("\u202F", " ")
        .replace("\u205F", " ")
        .replace("\u2060", "")
        .replace("\u3000", " ")
        .replace("\uFEFF", "")
    )

    # Saltos de línea, tabulaciones y espacios múltiples.
    texto = re.sub(r"[\r\n\t\v\f]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip().upper()

    # Eliminar tildes y otros signos diacríticos para comparación.
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    # Segunda limpieza tras la descomposición Unicode.
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def _nombre_archivo_desde_hoja(hoja):
    """
    Intenta obtener el nombre del archivo que contiene la hoja.
    """

    try:
        ruta = hoja.book.fullname
        if ruta:
            return Path(str(ruta)).name
    except Exception:
        pass

    try:
        nombre = hoja.book.name
        if nombre:
            return str(nombre)
    except Exception:
        pass

    return "archivo desconocido"


def _nombre_hoja(hoja):
    """
    Obtiene un nombre legible de la hoja.
    """

    try:
        return str(hoja.name)
    except Exception:
        return "hoja desconocida"


def _normalizar_conjunto_columnas(columnas):
    """
    Normaliza un iterable de nombres de columnas.
    """

    return {
        normalizar_encabezado(columna)
        for columna in columnas
        if normalizar_encabezado(columna)
    }


def _fusionar_columnas_duplicadas(df):
    """
    Si dos encabezados distintos terminan representando la misma columna
    canónica, conserva una sola columna tomando el primer valor no vacío
    de izquierda a derecha.
    """

    if df.empty and not df.columns.duplicated().any():
        return df

    columnas = list(df.columns)

    if len(columnas) == len(set(columnas)):
        return df

    resultado = pd.DataFrame(index=df.index)
    procesadas = set()

    for nombre in columnas:

        if nombre in procesadas:
            continue

        posiciones = [
            indice
            for indice, columna in enumerate(columnas)
            if columna == nombre
        ]

        if len(posiciones) == 1:
            resultado[nombre] = df.iloc[:, posiciones[0]]
        else:
            bloque = df.iloc[:, posiciones].copy()

            # Tratar cadenas vacías como ausencia únicamente durante la
            # fusión para permitir recuperar un valor existente en otra
            # columna equivalente.
            bloque = bloque.replace(r"^\s*$", pd.NA, regex=True)

            resultado[nombre] = bloque.bfill(axis=1).iloc[:, 0]

            print(
                f"⚠ Encabezado duplicado normalizado: {nombre}. "
                "Se conservará el primer valor disponible."
            )

        procesadas.add(nombre)

    return resultado


def _normalizar_columnas_dataframe(df):
    """
    Normaliza todos los nombres de columnas y resuelve equivalencias.
    """

    df = df.copy()
    df.columns = [
        normalizar_encabezado(columna)
        for columna in df.columns
    ]

    df = _fusionar_columnas_duplicadas(df)

    return df


def _es_tabla_anio(columnas_obligatorias):
    """
    Determina si la lectura corresponde a la tabla principal AÑO.
    """

    obligatorias = _normalizar_conjunto_columnas(columnas_obligatorias)

    return _normalizar_conjunto_columnas(COLUMNAS_ANIO).issubset(obligatorias)


def _crear_columnas_opcionales(df, archivo_excel, nombre_hoja, columnas_obligatorias):
    """
    Crea únicamente las columnas opcionales requeridas por el flujo
    de la tabla principal.
    """

    if not _es_tabla_anio(columnas_obligatorias):
        return df

    for columna in COLUMNAS_OPCIONALES_NUMERICAS:

        if columna not in df.columns:

            df[columna] = 0

            print(
                f"\n⚠ Archivo {Path(archivo_excel).name}\n"
                f"Hoja: {nombre_hoja}\n"
                f"No existe la columna:\n"
                f"{columna}\n"
                f"Se utilizará valor 0."
            )

    for columna in COLUMNAS_OPCIONALES_TEXTO:

        if columna not in df.columns:

            df[columna] = ""

            print(
                f"\n⚠ Archivo {Path(archivo_excel).name}\n"
                f"Hoja: {nombre_hoja}\n"
                f"No existe la columna:\n"
                f"{columna}\n"
                f'Se utilizará valor "".'
            )

    return df


def _validar_columnas_obligatorias_dataframe(
    df,
    archivo_excel,
    nombre_hoja,
    columnas_obligatorias
):
    """
    Verifica que las columnas requeridas existan después de normalizar.
    """

    obligatorias = _normalizar_conjunto_columnas(columnas_obligatorias)

    faltantes = sorted(
        columna
        for columna in obligatorias
        if columna not in df.columns
    )

    if not faltantes:
        return True

    for columna in faltantes:

        print(
            f"\n❌ Archivo: {Path(archivo_excel).name}\n"
            f"Hoja: {nombre_hoja}\n"
            f"Columna faltante: {columna}\n"
            "Causa: la columna obligatoria no existe o no pudo "
            "ser reconocida en los encabezados."
        )

    return False


def _imprimir_error_lectura(
    archivo_excel,
    nombre_hoja,
    causa,
    columna=None
):
    """
    Muestra un error de lectura con contexto suficiente para el usuario.
    """

    print("\n" + "=" * 60)
    print("❌ ERROR AL PROCESAR ARCHIVO")
    print("=" * 60)
    print(f"Archivo : {Path(archivo_excel).name}")
    print(f"Hoja    : {nombre_hoja}")

    if columna:
        print(f"Columna : {columna}")

    print(f"Causa   : {causa}")
    print("Este archivo será omitido.")
    print("=" * 60)


# ==========================================================
# NORMALIZAR ENCABEZADOS
# ==========================================================

def normalizar_encabezado(nombre):

    nombre_base = _texto_base_encabezado(nombre)

    if not nombre_base:
        return ""

    # Equivalencias exactas registradas.
    if nombre_base in EQUIVALENCIAS_ENCABEZADOS:
        return EQUIVALENCIAS_ENCABEZADOS[nombre_base]

    # Variantes dinámicas:
    # KM EXTRA DESPUES DE 90
    # KM EXTRA DESPUES DE 110
    # KM EXTRA DESPUES DE 120
    # etc.
    if re.fullmatch(
        r"KM\s+EXTRA\s+DESPUES\s+DE(?:\s+\d+(?:[.,]\d+)?)?",
        nombre_base
    ):
        return "KM EXTRA DESPUES DE"

    return nombre_base


def buscar_encabezados(hoja, columnas_obligatorias):
    """
    Busca automáticamente la fila donde están los encabezados.

    Retorna:
        fila_encabezado
        columnas -> diccionario con la posición de cada columna
    """

    archivo = _nombre_archivo_desde_hoja(hoja)
    nombre_hoja = _nombre_hoja(hoja)

    obligatorias = _normalizar_conjunto_columnas(
        columnas_obligatorias
    )

    if not obligatorias:
        raise ValueError(
            f"Archivo: {archivo} | Hoja: {nombre_hoja} | "
            "Causa: no se definieron columnas obligatorias para "
            "localizar los encabezados."
        )

    try:
        ultima_fila = hoja.used_range.last_cell.row
        ultima_columna = hoja.used_range.last_cell.column
    except Exception as e:
        raise RuntimeError(
            f"Archivo: {archivo} | Hoja: {nombre_hoja} | "
            f"Causa: no fue posible determinar el rango utilizado. {e}"
        ) from e

    mejor_fila = None
    mejor_encontrados = set()

    for fila in range(1, ultima_fila + 1):

        encabezados = {}
        encontrados = set()

        for columna in range(1, ultima_columna + 1):

            valor = hoja.cells(fila, columna).value

            if valor is None:
                continue

            nombre = normalizar_encabezado(valor)

            if not nombre:
                continue

            # Mantener la primera aparición de una columna canónica.
            if nombre not in encabezados:
                encabezados[nombre] = columna

            if nombre in obligatorias:
                encontrados.add(nombre)

        if len(encontrados) > len(mejor_encontrados):
            mejor_fila = fila
            mejor_encontrados = encontrados

        if obligatorias.issubset(encontrados):

            print(f"✓ Encabezados encontrados en fila {fila}")

            return fila, encabezados

    faltantes = sorted(obligatorias - mejor_encontrados)

    detalle_faltantes = ", ".join(faltantes) if faltantes else "desconocidas"

    if mejor_fila is not None:
        detalle_fila = f" La fila más cercana fue la {mejor_fila}."
    else:
        detalle_fila = ""

    raise ValueError(
        f"Archivo: {archivo} | Hoja: {nombre_hoja} | "
        f"Columnas faltantes: {detalle_faltantes} | "
        "Causa: no fue posible localizar una fila que contenga "
        f"todos los encabezados obligatorios.{detalle_fila}"
    )


# ==========================================================
# LEER TABLA ORIGEN
# ==========================================================

def leer_tabla(
    archivo_excel,
    nombre_hoja,
    columnas_obligatorias
):

    archivo_excel = Path(archivo_excel)

    print(f"Leyendo: {archivo_excel.name}")

    app = None
    libro = None

    try:

        app, libro = abrir_excel(archivo_excel)

        try:
            hoja = libro.sheets[nombre_hoja]

        except Exception as e:

            print(f"\n❌ Error al abrir la hoja '{nombre_hoja}'")
            print(f"Archivo: {archivo_excel.name}")
            print(f"Detalle: {e}")

            print("\n📋 Hojas disponibles:")

            for hoja_libro in libro.sheets:
                print(f"   - {hoja_libro.name}")

            cerrar_excel(app, libro)
            app = None
            libro = None

            return None, None

        # Buscar automáticamente la fila de encabezados
        try:
            fila_encabezado, columnas = buscar_encabezados(
                hoja,
                columnas_obligatorias
            )

        except Exception as e:

            _imprimir_error_lectura(
                archivo_excel=archivo_excel,
                nombre_hoja=nombre_hoja,
                causa=str(e)
            )

            cerrar_excel(app, libro)
            app = None
            libro = None

            return None, None

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
        app = None
        libro = None

        if df is None:
            _imprimir_error_lectura(
                archivo_excel=archivo_excel,
                nombre_hoja=nombre_hoja,
                causa="Excel no devolvió datos para la tabla."
            )
            return None, None

        # Normalizar encabezados
        df = _normalizar_columnas_dataframe(df)

        # Validar obligatorias después de la lectura real.
        if not _validar_columnas_obligatorias_dataframe(
            df=df,
            archivo_excel=archivo_excel,
            nombre_hoja=nombre_hoja,
            columnas_obligatorias=columnas_obligatorias
        ):
            return None, None

        # Crear columnas opcionales antes de que sean consumidas
        # por las funciones constructoras.
        df = _crear_columnas_opcionales(
            df=df,
            archivo_excel=archivo_excel,
            nombre_hoja=nombre_hoja,
            columnas_obligatorias=columnas_obligatorias
        )

        # Eliminar filas completamente vacías
        df = df.dropna(how="all")

        # Eliminar registros sin placa
        if "PLACA" not in df.columns:
            _imprimir_error_lectura(
                archivo_excel=archivo_excel,
                nombre_hoja=nombre_hoja,
                columna="PLACA",
                causa=(
                    "La columna obligatoria PLACA no está disponible "
                    "después de normalizar los encabezados."
                )
            )
            return None, None

        df = df[df["PLACA"].notna()]

        df = df.reset_index(drop=True)

        return df, columnas

    except KeyError as e:

        columna = str(e).strip("'\"")

        _imprimir_error_lectura(
            archivo_excel=archivo_excel,
            nombre_hoja=nombre_hoja,
            columna=columna,
            causa=(
                "Se intentó utilizar una columna que no existe "
                "después de normalizar el archivo."
            )
        )

        return None, None

    except Exception as e:

        _imprimir_error_lectura(
            archivo_excel=archivo_excel,
            nombre_hoja=nombre_hoja,
            causa=str(e)
        )

        return None, None

    finally:

        if app is not None and libro is not None:

            try:
                cerrar_excel(app, libro)
            except Exception:
                pass

        elif app is not None:

            try:
                app.quit()
            except Exception:
                pass


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
