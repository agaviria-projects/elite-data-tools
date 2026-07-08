import pandas as pd


# ==========================================
# VALIDAR COLUMNA
# ==========================================

def validar_columna(df, columna):

    if columna not in df.columns:
        raise KeyError(f"La columna '{columna}' no existe.")


# ==========================================
# COSTO POR CONCEPTO
# ==========================================

def costo_por_concepto(df, columna_concepto, columna_valor):

    validar_columna(df, columna_concepto)
    validar_columna(df, columna_valor)

    datos = df.copy()

    datos[columna_valor] = pd.to_numeric(
        datos[columna_valor],
        errors="coerce"
    ).fillna(0)

    return (

        datos
        .groupby(
            columna_concepto,
            dropna=False
        )[columna_valor]
        .sum()
        .reset_index()
        .rename(
            columns={
                columna_concepto: "Concepto",
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
# TOP CONCEPTOS
# ==========================================

def top_conceptos(df, columna_concepto, columna_valor, cantidad=10):

    return (
        costo_por_concepto(
            df,
            columna_concepto,
            columna_valor
        )
        .head(cantidad)
        .reset_index(drop=True)
    )


# ==========================================
# BOTTOM CONCEPTOS
# ==========================================

def bottom_conceptos(df, columna_concepto, columna_valor, cantidad=10):

    return (

        costo_por_concepto(
            df,
            columna_concepto,
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
# PARTICIPACIÓN POR CONCEPTO
# ==========================================

def participacion_conceptos(df, columna_concepto, columna_valor):

    resumen = costo_por_concepto(
        df,
        columna_concepto,
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