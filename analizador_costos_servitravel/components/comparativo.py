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
# FORMATO
# ==========================================================

def _moneda(valor):

    return f"$ {valor:,.0f}".replace(",", ".")


# ==========================================================
# COMPARATIVO MES VS MES ANTERIOR
# ==========================================================

def mostrar_comparativo(df):

    if df is None or df.empty:
        st.info("No hay información para realizar el comparativo.")
        return

    # ------------------------------------------------------
    # COLUMNAS
    # ------------------------------------------------------

    col_fecha = _buscar_columna(
        df,
        [
            "FECHA"
        ]
    )

    col_placa = _buscar_columna(
        df,
        [
            "PLACA"
        ]
    )

    col_horas = _buscar_columna(
        df,
        [
            "HORAS_EXTRAS",
            "HORAS EXTRA",
            "HORAS EXTRAS"
        ]
    )

    col_valor = _buscar_columna(
        df,
        [
            "TOTAL_EXTRAS",
            "TOTAL EXTRAS",
            "VALOR_HORAS_EXTRAS",
            "VALOR HORAS EXTRAS",
            "TOTAL HORAS EXTRAS"
        ]
    )

    if col_fecha is None:
        st.warning("No existe la columna FECHA.")
        return

    # ------------------------------------------------------
    # PREPARAR
    # ------------------------------------------------------

    datos = df.copy()

    datos[col_fecha] = pd.to_datetime(
        datos[col_fecha],
        dayfirst=True,
        errors="coerce"
    )

    datos = datos.dropna(subset=[col_fecha])

    if datos.empty:
        st.info("No existen fechas válidas.")
        return

    if col_horas:
        datos[col_horas] = pd.to_numeric(
            datos[col_horas],
            errors="coerce"
        ).fillna(0)

    if col_valor:
        datos[col_valor] = pd.to_numeric(
            datos[col_valor],
            errors="coerce"
        ).fillna(0)

    datos["AñoMes"] = (
        datos[col_fecha]
        .dt.to_period("M")
    )

    meses = sorted(datos["AñoMes"].unique())

    if len(meses) < 2:
        st.info("Se requieren al menos dos meses para realizar el comparativo.")
        return

    mes_actual = meses[-1]
    mes_anterior = meses[-2]

    actual = datos[
        datos["AñoMes"] == mes_actual
    ]

    anterior = datos[
        datos["AñoMes"] == mes_anterior
    ]

    # ------------------------------------------------------
    # MÉTRICAS
    # ------------------------------------------------------

    def vehiculos(x):

        if col_placa is None:
            return 0

        return x[col_placa].nunique()

    def horas(x):

        if col_horas is None:
            return 0

        return x[col_horas].sum()

    def extras(x):

        if col_valor is None:
            return 0

        return x[col_valor].sum()

    veh_actual = vehiculos(actual)
    veh_ant = vehiculos(anterior)

    horas_actual = horas(actual)
    horas_ant = horas(anterior)

    extras_actual = extras(actual)
    extras_ant = extras(anterior)

    # ------------------------------------------------------
    # INTERFAZ
    # ------------------------------------------------------

    st.subheader("📈 Comparativo Mes vs Mes Anterior")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "🚚 Vehículos",
        f"{veh_actual:,}".replace(",", "."),
        veh_actual - veh_ant
    )

    c2.metric(
        "⏱ Horas Extras",
        f"{horas_actual:,.1f}".replace(",", "."),
        round(horas_actual - horas_ant, 1)
    )

    c3.metric(
        "💰 Total Horas Extras",
        _moneda(extras_actual),
        _moneda(extras_actual - extras_ant)
    )

    # ------------------------------------------------------
    # TABLA
    # ------------------------------------------------------

    resumen = pd.DataFrame({

        "Indicador": [

            "Vehículos utilizados",
            "Horas Extras",
            "Total Horas Extras"

        ],

        "Mes Anterior": [

            veh_ant,
            round(horas_ant, 2),
            extras_ant

        ],

        "Mes Actual": [

            veh_actual,
            round(horas_actual, 2),
            extras_actual

        ],

        "Variación": [

            veh_actual - veh_ant,
            round(horas_actual - horas_ant, 2),
            extras_actual - extras_ant

        ]

    })

    resumen["Total Horas Extras"] = None

    st.dataframe(
        resumen,
        use_container_width=True,
        hide_index=True
    )