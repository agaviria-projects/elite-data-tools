import streamlit as st
import pandas as pd


# ==========================================================
# BUSCAR COLUMNA
# ==========================================================

def _buscar_columna(df, candidatos):

    columnas = {
        c.strip().upper(): c
        for c in df.columns
    }

    for nombre in candidatos:

        if nombre.upper() in columnas:
            return columnas[nombre.upper()]

    return None


# ==========================================================
# FORMATO
# ==========================================================

def _formato_entero(valor):

    return f"{int(valor):,}".replace(",", ".")


def _formato_decimal(valor):

    return f"{valor:,.1f}".replace(",", ".")


def _formato_moneda(valor):

    return f"$ {valor:,.0f}".replace(",", ".")


# ==========================================================
# KPIs
# ==========================================================

def mostrar_kpis(df: pd.DataFrame):

    if df is None or df.empty:

        st.warning("No existen registros para mostrar.")

        return

    df = df.copy()

    # ------------------------------------------------------
    # COLUMNAS
    # ------------------------------------------------------

    col_placa = _buscar_columna(
        df,
        [
            "PLACA"
        ]
    )

    col_horas = _buscar_columna(
        df,
        [
            "HORAS EXTRA",
            "HORAS EXTRAS",
            "HORAS_EXTRAS"
        ]
    )

    col_valor = _buscar_columna(
        df,
        [
            "VALOR HORA EXTRA"
        ]
    )

    # ------------------------------------------------------
    # LIMPIEZA
    # ------------------------------------------------------

    if col_placa:

        df[col_placa] = (
            df[col_placa]
            .astype(str)
            .str.strip()
        )

    if col_horas:

        df[col_horas] = (
            pd.to_numeric(
                df[col_horas],
                errors="coerce"
            )
            .fillna(0)
        )

    if col_valor:

        df[col_valor] = (
            pd.to_numeric(
                df[col_valor],
                errors="coerce"
            )
            .fillna(0)
        )

    # ------------------------------------------------------
    # KPI
    # ------------------------------------------------------

    vehiculos = (
        df[col_placa].nunique()
        if col_placa
        else 0
    )

    horas = (
        df[col_horas].sum()
        if col_horas
        else 0
    )

    total_extras = (
        df[col_valor]
        .fillna(0)
        .sum()
        if col_valor
        else 0
    )

    promedio = (
        horas / vehiculos
        if vehiculos > 0
        else 0
    )

    placa_top = "-"

    if col_placa:

        ranking = (

            df.groupby(col_placa)
            .size()
            .sort_values(ascending=False)

        )

        if not ranking.empty:

            placa_top = ranking.index[0]

    # ------------------------------------------------------
    # DASHBOARD
    # ------------------------------------------------------

    st.subheader("📌 Cierre del Mes")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "🚚 Vehículos utilizados",
        _formato_entero(vehiculos)
    )

    c2.metric(
        "⏱ Horas Extras",
        _formato_decimal(horas)
    )

    c3.metric(
        "💰 Total Horas Extras",
        _formato_moneda(total_extras)
    )
