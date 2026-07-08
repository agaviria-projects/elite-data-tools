import pandas as pd


# ==========================================
# VALIDAR COLUMNA
# ==========================================

def validar_columna(df, columna):

    if columna not in df.columns:
        raise KeyError(f"La columna '{columna}' no existe.")


# ==========================================
# DETECTAR OUTLIERS (IQR)
# ==========================================

def detectar_outliers(df, columna_valor):

    validar_columna(df, columna_valor)

    datos = df.copy()

    datos[columna_valor] = pd.to_numeric(
        datos[columna_valor],
        errors="coerce"
    )

    datos = datos.dropna(subset=[columna_valor])

    q1 = datos[columna_valor].quantile(0.25)
    q3 = datos[columna_valor].quantile(0.75)

    iqr = q3 - q1

    limite_inferior = q1 - (1.5 * iqr)
    limite_superior = q3 + (1.5 * iqr)

    return datos[
        (datos[columna_valor] < limite_inferior)
        |
        (datos[columna_valor] > limite_superior)
    ].reset_index(drop=True)


# ==========================================
# RESUMEN OUTLIERS
# ==========================================

def resumen_outliers(df, columna_valor):

    outliers = detectar_outliers(
        df,
        columna_valor
    )

    return {

        "total_registros": len(df),
        "outliers": len(outliers),
        "porcentaje": round(
            len(outliers) / len(df) * 100,
            2
        ) if len(df) else 0

    }


# ==========================================
# TOP OUTLIERS
# ==========================================

def top_outliers(df, columna_valor, cantidad=20):

    outliers = detectar_outliers(
        df,
        columna_valor
    )

    return (

        outliers
        .sort_values(
            columna_valor,
            ascending=False
        )
        .head(cantidad)
        .reset_index(drop=True)

    )