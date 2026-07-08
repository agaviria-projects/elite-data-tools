import pandas as pd


# ==========================================
# VALIDAR COLUMNA
# ==========================================

def validar_columna(df, columna):

    if columna not in df.columns:
        raise KeyError(f"La columna '{columna}' no existe.")


# ==========================================
# COSTO POR ZONA
# ==========================================

def costo_por_zona(df, columna_zona, columna_valor):

    validar_columna(df, columna_zona)
    validar_columna(df, columna_valor)

    datos = df.copy()

    datos[columna_valor] = pd.to_numeric(
        datos[columna_valor],
        errors="coerce"
    ).fillna(0)

    return (

        datos
        .groupby(
            columna_zona,
            dropna=False
        )[columna_valor]
        .sum()
        .reset_index()
        .rename(
            columns={
                columna_zona: "Zona",
                columna_valor: "Costo"
            }
        )
        .sort_values(
            "Costo",
            ascending=False
        )
        .reset_index(drop=True)

    )


# ==========================================
# TOP ZONAS
# ==========================================

def top_zonas(df, columna_zona, columna_valor, cantidad=10):

    return (
        costo_por_zona(
            df,
            columna_zona,
            columna_valor
        )
        .head(cantidad)
        .reset_index(drop=True)
    )


# ==========================================
# BOTTOM ZONAS
# ==========================================

def bottom_zonas(df, columna_zona, columna_valor, cantidad=10):

    return (

        costo_por_zona(
            df,
            columna_zona,
            columna_valor
        )
        .sort_values(
            "Costo",
            ascending=True
        )
        .head(cantidad)
        .reset_index(drop=True)

    )


# ==========================================
# PARTICIPACIÓN POR ZONA
# ==========================================

def participacion_zonas(df, columna_zona, columna_valor):

    resumen = costo_por_zona(
        df,
        columna_zona,
        columna_valor
    )

    total = resumen["Costo"].sum()

    if total == 0:

        resumen["Participación %"] = 0

    else:

        resumen["Participación %"] = (
            resumen["Costo"] / total * 100
        ).round(2)

    return resumen