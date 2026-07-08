import pandas as pd


# ==========================================
# VALIDAR COLUMNA
# ==========================================

def validar_columna(df, columna):

    if columna not in df.columns:
        raise KeyError(f"La columna '{columna}' no existe.")


# ==========================================
# TENDENCIA POR PERIODO
# ==========================================

def tendencia(df, columna_periodo, columna_valor):

    validar_columna(df, columna_periodo)
    validar_columna(df, columna_valor)

    datos = df.copy()

    datos[columna_valor] = pd.to_numeric(
        datos[columna_valor],
        errors="coerce"
    ).fillna(0)

    resultado = (

        datos
        .groupby(
            columna_periodo,
            dropna=False
        )[columna_valor]
        .sum()
        .reset_index()

    )

    resultado["Variación"] = resultado[columna_valor].diff().fillna(0)

    resultado["Variación %"] = (

        resultado[columna_valor]
        .pct_change()
        .replace([float("inf"), float("-inf")], 0)
        .fillna(0)
        * 100

    ).round(2)

    resultado.rename(

        columns={

            columna_periodo: "Periodo",
            columna_valor: "Costo"

        },

        inplace=True

    )

    return resultado


# ==========================================
# CRECIMIENTO ACUMULADO
# ==========================================

def crecimiento_acumulado(df, columna_periodo, columna_valor):

    resultado = tendencia(
        df,
        columna_periodo,
        columna_valor
    ).copy()

    resultado["Acumulado"] = resultado["Costo"].cumsum()

    return resultado


# ==========================================
# MEJOR PERIODO
# ==========================================

def mejor_periodo(df, columna_periodo, columna_valor):

    datos = tendencia(
        df,
        columna_periodo,
        columna_valor
    )

    fila = datos.loc[datos["Costo"].idxmax()]

    return {

        "periodo": fila["Periodo"],
        "costo": round(float(fila["Costo"]), 2)

    }


# ==========================================
# PEOR PERIODO
# ==========================================

def peor_periodo(df, columna_periodo, columna_valor):

    datos = tendencia(
        df,
        columna_periodo,
        columna_valor
    )

    fila = datos.loc[datos["Costo"].idxmin()]

    return {

        "periodo": fila["Periodo"],
        "costo": round(float(fila["Costo"]), 2)

    }