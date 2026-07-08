import pandas as pd


# ==========================================
# VALIDAR COLUMNA
# ==========================================

def validar_columna(df, columna):

    if columna not in df.columns:
        raise KeyError(f"La columna '{columna}' no existe en el DataFrame.")


# ==========================================
# TOTAL REGISTROS
# ==========================================

def total_registros(df):

    return len(df.index)


# ==========================================
# TOTAL COLUMNAS
# ==========================================

def total_columnas(df):

    return len(df.columns)


# ==========================================
# TOTAL NULOS
# ==========================================

def total_nulos(df):

    return int(df.isna().sum().sum())


# ==========================================
# COSTO TOTAL
# ==========================================

def costo_total(df, columna):

    validar_columna(df, columna)

    return round(
        pd.to_numeric(
            df[columna],
            errors="coerce"
        ).fillna(0).sum(),
        2
    )


# ==========================================
# COSTO PROMEDIO
# ==========================================

def costo_promedio(df, columna):

    validar_columna(df, columna)

    return round(
        pd.to_numeric(
            df[columna],
            errors="coerce"
        ).fillna(0).mean(),
        2
    )


# ==========================================
# COSTO MÁXIMO
# ==========================================

def costo_maximo(df, columna):

    validar_columna(df, columna)

    return round(
        pd.to_numeric(
            df[columna],
            errors="coerce"
        ).max(),
        2
    )


# ==========================================
# COSTO MÍNIMO
# ==========================================

def costo_minimo(df, columna):

    validar_columna(df, columna)

    return round(
        pd.to_numeric(
            df[columna],
            errors="coerce"
        ).min(),
        2
    )


# ==========================================
# AGRUPAR
# ==========================================

def agrupar(df, columna, columna_valor):

    validar_columna(df, columna)
    validar_columna(df, columna_valor)

    datos = df.copy()

    datos[columna_valor] = pd.to_numeric(
        datos[columna_valor],
        errors="coerce"
    ).fillna(0)

    return (

        datos
        .groupby(
            columna,
            dropna=False
        )[columna_valor]
        .sum()
        .reset_index()

    )


# ==========================================
# AGRUPAR POR MES
# ==========================================

def agrupar_mes(df, columna_mes, columna_valor):

    return agrupar(
        df,
        columna_mes,
        columna_valor
    )


# ==========================================
# AGRUPAR POR ZONA
# ==========================================

def agrupar_zona(df, columna_zona, columna_valor):

    return agrupar(
        df,
        columna_zona,
        columna_valor
    )


# ==========================================
# AGRUPAR POR PLACA
# ==========================================

def agrupar_placa(df, columna_placa, columna_valor):

    return agrupar(
        df,
        columna_placa,
        columna_valor
    )


# ==========================================
# TOP N
# ==========================================

def top(df, columna_valor, cantidad=10):

    validar_columna(df, columna_valor)

    datos = df.copy()

    datos[columna_valor] = pd.to_numeric(
        datos[columna_valor],
        errors="coerce"
    ).fillna(0)

    return (

        datos
        .sort_values(
            columna_valor,
            ascending=False
        )
        .head(cantidad)
        .reset_index(drop=True)

    )


# ==========================================
# BOTTOM N
# ==========================================

def bottom(df, columna_valor, cantidad=10):

    validar_columna(df, columna_valor)

    datos = df.copy()

    datos[columna_valor] = pd.to_numeric(
        datos[columna_valor],
        errors="coerce"
    ).fillna(0)

    return (

        datos
        .sort_values(
            columna_valor,
            ascending=True
        )
        .head(cantidad)
        .reset_index(drop=True)

    )


# ==========================================
# VARIACIÓN %
# ==========================================

def variacion(actual, anterior):

    if pd.isna(anterior) or anterior == 0:
        return 0

    return round(
        ((actual - anterior) / anterior) * 100,
        2
    )