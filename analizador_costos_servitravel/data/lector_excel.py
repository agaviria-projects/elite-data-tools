from pathlib import Path

import pandas as pd


# ==========================================
# RUTA DEL ARCHIVO
# ==========================================

BASE = Path(__file__).resolve().parent.parent.parent

ARCHIVO = (
    BASE
    / "SERVITRAVEL"
    / "salida"
    / "INFORME_LIQUIDACION.xlsb"
)


# ==========================================
# CONFIGURACIÓN DE HOJAS
# ==========================================

CONFIG_HOJAS = {

    "RODAMIENTOS": {
        "header": 0,
        "usecols": None,
    },

    "VIATICOS": {
        "header": 1,
        "usecols": "A:D",
    },

    "PARQUEADEROS": {
        "header": 0,
        "usecols": "A:E",
    },

    "PEAJES": {
        "header": 0,
        "usecols": "A:H",
    },

    "FACTURACION": {
        "header": 0,
        "usecols": None,
    },

}


# ==========================================
# VALIDAR ARCHIVO
# ==========================================

def archivo_existe():

    return ARCHIVO.exists()


# ==========================================
# OBTENER RUTA
# ==========================================

def obtener_ruta():

    return ARCHIVO


# ==========================================
# OBTENER HOJAS
# ==========================================

def obtener_hojas():

    if not ARCHIVO.exists():
        raise FileNotFoundError(
            f"No existe el archivo:\n{ARCHIVO}"
        )

    with pd.ExcelFile(
        ARCHIVO,
        engine="pyxlsb",
    ) as libro:

        return libro.sheet_names


# ==========================================
# CONVERTIR FECHAS
# ==========================================

def convertir_fechas(df):

    columnas_fecha = [

        # RODAMIENTOS
        "FECHA",

        # VIÁTICOS
        "FECHA VIATICOS",

        # PEAJES
        "FECHA EN LA QUE SE CAUSA EL PEAJE",

        # FACTURACIÓN
        "FECHA FACTURA",
        "VENCIMIENTO",

    ]

    for columna in columnas_fecha:

        if columna not in df.columns:
            continue

        try:

            serie = df[columna]

            # Excel puede entregar fechas como números seriales
            if pd.api.types.is_numeric_dtype(serie):

                df[columna] = pd.to_datetime(
                    serie,
                    unit="D",
                    origin="1899-12-30",
                    errors="coerce",
                )

            else:

                df[columna] = pd.to_datetime(
                    serie,
                    dayfirst=True,
                    errors="coerce",
                )

        except Exception:

            pass

    return df


# ==========================================
# CONVERTIR HORAS EXCEL
# ==========================================

def convertir_horas(df):

    columnas_hora = [

        "INGRESO",
        "SALIDA",
        "HORAS TRABAJADAS",
        "ALMUERZO",
        "MIN HORAS",
        "HORAS EXTRA",
        "TOTAL HORAS",

    ]

    for columna in columnas_hora:

        if columna not in df.columns:
            continue

        try:

            serie = df[columna]

            # Excel guarda las horas como fracción de día
            if pd.api.types.is_numeric_dtype(serie):

                df[columna] = (
                    pd.to_numeric(
                        serie,
                        errors="coerce",
                    )
                    .fillna(0)
                    * 24
                )

            else:

                tiempo = pd.to_timedelta(
                    serie,
                    errors="coerce",
                )

                df[columna] = (
                    tiempo.dt.total_seconds()
                    / 3600
                ).fillna(0)

        except Exception:

            pass

    return df


# ==========================================
# CONVERTIR VALORES MONETARIOS
# ==========================================

def convertir_monedas(df):

    columnas_monetarias = [

        # RODAMIENTOS
        "VALOR HORA EXTRA",
        "PEAJES",
        "VALOR KM EXTRA",
        "VALOR ÉLITE",

        # VIÁTICOS
        "TOTAL VIATICOS",

        # PARQUEADEROS
        "TOTAL PARQUEADEROS",

        # PEAJES
        "VALOR PEAJE",
        "TOTAL PEAJES",

        # FACTURACIÓN
        "SUBTOTAL",
        "DESCUENTO",
        "IVA",
        "RETEFUENTE",
        "TOTAL",

    ]

    for columna in columnas_monetarias:

        if columna not in df.columns:
            continue

        try:

            df[columna] = (
                df[columna]
                .astype(str)
                .str.replace(
                    "$",
                    "",
                    regex=False,
                )
                .str.replace(
                    ",",
                    "",
                    regex=False,
                )
                .str.strip()
            )

            df[columna] = pd.to_numeric(
                df[columna],
                errors="coerce",
            ).fillna(0)

        except Exception:

            pass

    return df


# ==========================================
# LIMPIAR ENCABEZADOS
# ==========================================

def limpiar_encabezados(df):

    df.columns = [
        str(columna).strip()
        for columna in df.columns
    ]

    return df


# ==========================================
# LEER UNA HOJA
# ==========================================

def leer_hoja(nombre_hoja):

    if not ARCHIVO.exists():
        raise FileNotFoundError(
            f"No existe el archivo:\n{ARCHIVO}"
        )

    hoja = nombre_hoja.strip().upper()

    config = CONFIG_HOJAS.get(
        hoja,
        {
            "header": 0,
            "usecols": None,
        },
    )

    df = pd.read_excel(
        ARCHIVO,
        sheet_name=nombre_hoja,
        engine="pyxlsb",
        header=config["header"],
        usecols=config["usecols"],
    )

    df = limpiar_encabezados(df)

    df = convertir_fechas(df)

    df = convertir_horas(df)

    df = convertir_monedas(df)

    df = df.dropna(
        how="all"
    ).reset_index(
        drop=True
    )

    return df


# ==========================================
# LEER TODAS LAS HOJAS
# ==========================================

def leer_todas():

    hojas = {}

    for hoja in obtener_hojas():

        hojas[hoja] = leer_hoja(
            hoja
        )

    return hojas