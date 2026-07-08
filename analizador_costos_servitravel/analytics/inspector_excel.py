import pandas as pd


# ==========================================
# INSPECCIONAR DATAFRAME
# ==========================================

def inspeccionar(df):

    columnas = []

    for col in df.columns:

        columnas.append({

            "columna": col,

            "tipo": str(df[col].dtype),

            "nulos": int(df[col].isna().sum()),

            "unicos": int(df[col].nunique()),

            "ejemplo": "" if df.empty else str(df[col].iloc[0])

        })

    return {

        "registros": len(df),

        "columnas": len(df.columns),

        "detalle": pd.DataFrame(columnas)

    }