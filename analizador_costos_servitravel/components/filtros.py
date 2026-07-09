import streamlit as st
import pandas as pd


# ==========================================================
# BUSCAR COLUMNA
# ==========================================================

def _buscar_columna(df, nombres):

    columnas = {
        c.strip().upper(): c
        for c in df.columns
    }

    for nombre in nombres:

        if nombre.upper() in columnas:
            return columnas[nombre.upper()]

    return None


# ==========================================================
# CREAR AÑO-MES
# ==========================================================

def _crear_anio_mes(df, columna_fecha):

    if columna_fecha is None:
        return df

    df = df.copy()

    df[columna_fecha] = pd.to_datetime(
        df[columna_fecha],
        dayfirst=True,
        errors="coerce"
    )

    df["AñoMes"] = (
        df[columna_fecha]
        .dt.to_period("M")
        .astype(str)
    )

    return df


# ==========================================================
# FILTROS
# ==========================================================
def mostrar_filtros(df, key_prefix="filtros"):

    if df is None or df.empty:

        return pd.DataFrame()  

    # ------------------------------------------------------

    col_fecha = _buscar_columna(
        df,
        [
            "FECHA"
        ]
    )

    col_zona = _buscar_columna(
        df,
        [
            "ZONA"
        ]
    )

    col_placa = _buscar_columna(
        df,
        [
            "PLACA"
        ]
    )

    # ------------------------------------------------------

    df = _crear_anio_mes(
        df,
        col_fecha
    )

    st.subheader("🔎 Filtros")

    c1, c2, c3 = st.columns(3)

    # ======================================================
    # MES
    # ======================================================

    if "AñoMes" in df.columns:

        meses = sorted(

            df["AñoMes"]
            .dropna()
            .unique()

        )

        if meses:

            mes = c1.selectbox(
                "Mes",
                meses,
                index=len(meses)-1,
                key=f"{key_prefix}_mes"
            )

            df = df[
                df["AñoMes"] == mes
            ]

    # ======================================================
    # ZONA
    # ======================================================

    if col_zona:

        zonas = [

            "Todas",

            *sorted(
                df[col_zona]
                .dropna()
                .astype(str)
                .unique()
            )

        ]

        zona = c2.selectbox(
            "Zona",
            zonas,
            key=f"{key_prefix}_zona"
        )

        if zona != "Todas":

            df = df[
                df[col_zona] == zona
            ]

    # ======================================================
    # PLACA
    # ======================================================

    if col_placa:

        placas = [

            "Todas",

            *sorted(
                df[col_placa]
                .dropna()
                .astype(str)
                .unique()
            )

        ]

        placa = c3.selectbox(
            "Placa",
            placas,
            key=f"{key_prefix}_placa"
        )

        if placa != "Todas":

            df = df[
                df[col_placa] == placa
            ]

    return df