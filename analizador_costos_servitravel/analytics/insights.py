import pandas as pd


# ==========================================
# MAYOR COSTO
# ==========================================

def mayor_costo(df, columna_categoria, columna_valor):

    datos = (

        df
        .groupby(columna_categoria, dropna=False)[columna_valor]
        .sum()
        .reset_index()

    )

    datos[columna_valor] = pd.to_numeric(
        datos[columna_valor],
        errors="coerce"
    ).fillna(0)

    fila = datos.loc[datos[columna_valor].idxmax()]

    return {

        "categoria": fila[columna_categoria],
        "valor": round(float(fila[columna_valor]), 2)

    }


# ==========================================
# MENOR COSTO
# ==========================================

def menor_costo(df, columna_categoria, columna_valor):

    datos = (

        df
        .groupby(columna_categoria, dropna=False)[columna_valor]
        .sum()
        .reset_index()

    )

    datos[columna_valor] = pd.to_numeric(
        datos[columna_valor],
        errors="coerce"
    ).fillna(0)

    fila = datos.loc[datos[columna_valor].idxmin()]

    return {

        "categoria": fila[columna_categoria],
        "valor": round(float(fila[columna_valor]), 2)

    }


# ==========================================
# TOP N INSIGHTS
# ==========================================

def top_insights(df, columna_categoria, columna_valor, cantidad=5):

    datos = (

        df
        .groupby(columna_categoria, dropna=False)[columna_valor]
        .sum()
        .reset_index()

    )

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
# BOTTOM N INSIGHTS
# ==========================================

def bottom_insights(df, columna_categoria, columna_valor, cantidad=5):

    datos = (

        df
        .groupby(columna_categoria, dropna=False)[columna_valor]
        .sum()
        .reset_index()

    )

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
# RESUMEN EJECUTIVO
# ==========================================

def resumen_ejecutivo(df, columna_categoria, columna_valor):

    mayor = mayor_costo(
        df,
        columna_categoria,
        columna_valor
    )

    menor = menor_costo(
        df,
        columna_categoria,
        columna_valor
    )

    total = round(

        pd.to_numeric(
            df[columna_valor],
            errors="coerce"
        ).fillna(0).sum(),

        2

    )

    return {

        "total": total,
        "mayor_categoria": mayor["categoria"],
        "mayor_valor": mayor["valor"],
        "menor_categoria": menor["categoria"],
        "menor_valor": menor["valor"]

    }