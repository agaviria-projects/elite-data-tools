import pandas as pd


# ==========================================
# COLUMNAS
# ==========================================

def obtener_columnas(df):

    return list(df.columns)


# ==========================================
# TIPOS DE DATOS
# ==========================================

def obtener_tipos(df):

    return df.dtypes.astype(str).to_dict()


# ==========================================
# NULOS
# ==========================================

def obtener_nulos(df):

    return df.isna().sum().to_dict()


# ==========================================
# VALORES ÚNICOS
# ==========================================

def obtener_unicos(df):

    return df.nunique().to_dict()


# ==========================================
# MEMORIA
# ==========================================

def obtener_memoria(df):

    return round(
        df.memory_usage(deep=True).sum() / 1024 / 1024,
        2
    )


# ==========================================
# DUPLICADOS
# ==========================================

def obtener_duplicados(df):

    return int(df.duplicated().sum())


# ==========================================
# PERFIL COMPLETO
# ==========================================

def perfil_dataframe(df):

    detalle = []

    for columna in df.columns:

        detalle.append({

            "columna": columna,

            "tipo": str(df[columna].dtype),

            "nulos": int(df[columna].isna().sum()),

            "unicos": int(df[columna].nunique())

        })

    return {

        "registros": len(df),

        "columnas": len(df.columns),

        "memoria": obtener_memoria(df),

        "duplicados": obtener_duplicados(df),

        "detalle_columnas": detalle

    }