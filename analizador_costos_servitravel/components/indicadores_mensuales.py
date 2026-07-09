import streamlit as st
import pandas as pd


# ==========================================================
# FUNCIÓN AUXILIAR
# ==========================================================

def calcular_variacion(actual, anterior):

    diferencia = actual - anterior

    if anterior == 0:
        porcentaje = 0
    else:
        porcentaje = (diferencia / anterior) * 100

    return diferencia, porcentaje


# ==========================================================
# INDICADORES MENSUALES
# ==========================================================

def mostrar_indicadores_mensuales(
    df: pd.DataFrame,
    df_filtrado: pd.DataFrame
):

    st.subheader("📈 Indicadores Mensuales")

    if "FECHA" not in df.columns:

        st.warning("No existe la columna FECHA.")
        return

    datos = df.copy()

    datos["FECHA"] = pd.to_datetime(
        datos["FECHA"],
        errors="coerce"
    )

    datos = datos.dropna(subset=["FECHA"])

    datos["AÑO_MES"] = datos["FECHA"].dt.to_period("M")

    # ======================================================
    # MES SELECCIONADO
    # ======================================================

    actual = df_filtrado.copy()

    actual["FECHA"] = pd.to_datetime(
        actual["FECHA"],
        errors="coerce"
    )

    actual = actual.dropna(subset=["FECHA"])

    if actual.empty:

        st.info("No existen registros para el mes seleccionado.")
        return

    mes_actual = actual["FECHA"].dt.to_period("M").iloc[0]

    mes_anterior = mes_actual - 1

    # ======================================================
    # DATAFRAMES
    # ======================================================

    df_actual = actual

    df_anterior = datos[
        datos["AÑO_MES"] == mes_anterior
    ]

    if df_anterior.empty:

        st.warning(
            f"No existe información para el mes anterior ({mes_anterior})."
        )

        return

    # ======================================================
    # KPIs
    # ======================================================

    vehiculos_actual = df_actual["PLACA"].nunique()
    vehiculos_anterior = df_anterior["PLACA"].nunique()

    horas_actual = df_actual["HORAS EXTRA"].sum()
    horas_anterior = df_anterior["HORAS EXTRA"].sum()

    valor_actual = df_actual["VALOR HORA EXTRA"].sum()
    valor_anterior = df_anterior["VALOR HORA EXTRA"].sum()

    diff_veh, porc_veh = calcular_variacion(
        vehiculos_actual,
        vehiculos_anterior
    )

    diff_horas, porc_horas = calcular_variacion(
        horas_actual,
        horas_anterior
    )

    diff_valor, porc_valor = calcular_variacion(
        valor_actual,
        valor_anterior
    )

    # ======================================================
    # ENCABEZADO
    # ======================================================

    st.markdown(
        f"""
### Comparativo

**{mes_actual}** vs **{mes_anterior}**
"""
    )

    # ======================================================
    # KPIs
    # ======================================================

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            label="🚗 Vehículos",
            value=f"{vehiculos_actual}",
            delta=f"{diff_veh:+} ({porc_veh:.1f}%)"
        )

    with c2:

        st.metric(
            label="🕒 Horas Extras",
            value=f"{horas_actual:,.1f}",
            delta=f"{diff_horas:+,.1f} ({porc_horas:.1f}%)"
        )

    with c3:

        st.metric(
            label="💰 Valor Hora Extra",
            value=f"$ {valor_actual:,.0f}",
            delta=f"$ {diff_valor:+,.0f} ({porc_valor:.1f}%)"
        )

    st.divider()

    # ======================================================
    # HALLAZGOS
    # ======================================================

    st.subheader("📝 Hallazgos del Mes")

    if diff_veh > 0:
        st.success(
            f"Se utilizaron **{diff_veh}** vehículos más que el mes anterior."
        )
    elif diff_veh < 0:
        st.info(
            f"Se utilizaron **{abs(diff_veh)}** vehículos menos que el mes anterior."
        )
    else:
        st.write("• La cantidad de vehículos no presentó variación.")

    if diff_horas > 0:
        st.warning(
            f"Las horas extras aumentaron **{porc_horas:.1f}%**."
        )
    elif diff_horas < 0:
        st.success(
            f"Las horas extras disminuyeron **{abs(porc_horas):.1f}%**."
        )
    else:
        st.write("• Las horas extras no presentaron variación.")

    if diff_valor > 0:
        st.error(
            f"El costo de horas extras aumentó **{porc_valor:.1f}%**."
        )
    elif diff_valor < 0:
        st.success(
            f"El costo de horas extras disminuyó **{abs(porc_valor):.1f}%**."
        )
    else:
        st.write("• El costo de horas extras no presentó variación.")