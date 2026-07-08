import pandas as pd


# ==========================================
# VALIDAR COLUMNA
# ==========================================

def validar_columna(df, columna):

    if columna not in df.columns:
        raise KeyError(f"La columna '{columna}' no existe.")


# ==========================================
# COSTO POR MES
# ==========================================

def costo_por_mes(df, columna_mes, columna_valor):

    validar_columna(df, columna_mes)
    validar_columna(df, columna_valor)

    datos = df.copy()

    datos[columna_valor] = pd.to_numeric(
        datos[columna_valor],
        errors="coerce"
    ).fillna(0)

    return (

        datos
        .groupby(
            columna_mes,
            dropna=False
        )[columna_valor]
        .sum()
        .reset_index()
        .sort_values(columna_mes)
        .reset_index(drop=True)

    )


# ==========================================
# COMPARAR DOS MESES
# ==========================================

def comparar(df, columna_mes, columna_valor, mes_actual, mes_anterior):

    resumen = costo_por_mes(
        df,
        columna_mes,
        columna_valor
    )

    actual = resumen.loc[
        resumen[columna_mes] == mes_actual,
        columna_valor
    ].sum()

    anterior = resumen.loc[
        resumen[columna_mes] == mes_anterior,
        columna_valor
    ].sum()

    diferencia = actual - anterior

    porcentaje = 0

    if anterior != 0:

        porcentaje = round(
            (diferencia / anterior) * 100,
            2
        )

    return {

        "mes_actual": mes_actual,
        "mes_anterior": mes_anterior,
        "valor_actual": round(actual, 2),
        "valor_anterior": round(anterior, 2),
        "diferencia": round(diferencia, 2),
        "variacion_pct": porcentaje

    }


# ==========================================
# COMPARATIVO COMPLETO
# ==========================================

def comparativo(df, columna_mes, columna_valor):

    resumen = costo_por_mes(
        df,
        columna_mes,
        columna_valor
    ).copy()

    resumen["Mes Anterior"] = resumen[columna_valor].shift(1)

    resumen["Diferencia"] = (
        resumen[columna_valor]
        - resumen["Mes Anterior"]
    )

    resumen["Variación %"] = (
        resumen["Diferencia"]
        / resumen["Mes Anterior"]
        * 100
    )

    resumen["Variación %"] = (
        resumen["Variación %"]
        .replace([float("inf"), float("-inf")], 0)
        .fillna(0)
        .round(2)
    )

    resumen["Diferencia"] = (
        resumen["Diferencia"]
        .fillna(0)
        .round(2)
    )

    resumen.rename(
        columns={
            columna_mes: "Mes",
            columna_valor: "Costo"
        },
        inplace=True
    )

    return resumen