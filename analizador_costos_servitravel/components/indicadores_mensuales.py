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

    nombre_mes = {
        1: "enero",
        2: "febrero",
        3: "marzo",
        4: "abril",
        5: "mayo",
        6: "junio",
        7: "julio",
        8: "agosto",
        9: "septiembre",
        10: "octubre",
        11: "noviembre",
        12: "diciembre"
    }

    mes_ref = nombre_mes[mes_anterior.month]

    st.subheader("📋 Principales hallazgos del período")

    # ======================================================
    # VEHÍCULOS
    # ======================================================

    if diff_veh > 0:

        st.success(
            f"🚗 Se utilizaron **{diff_veh} vehículos más** respecto a **{mes_ref}** "
            f"(**+{porc_veh:.1f}%**)."
        )

    elif diff_veh < 0:

        st.info(
            f"🚗 Se utilizaron **{abs(diff_veh)} vehículo(s) menos** respecto a **{mes_ref}** "
            f"(**{porc_veh:.1f}%**)."
        )

    else:

        st.info(
            f"🚗 La cantidad de vehículos se mantuvo igual respecto a **{mes_ref}**."
        )

    # ======================================================
    # HORAS EXTRA
    # ======================================================

    if diff_horas > 0:

        st.warning(
            f"⏱️ Las horas extra **aumentaron {diff_horas:,.1f} horas** respecto a "
            f"**{mes_ref}** (**+{porc_horas:.1f}%**)."
        )

    elif diff_horas < 0:

        st.success(
            f"⏱️ Las horas extra **disminuyeron {abs(diff_horas):,.1f} horas** respecto a "
            f"**{mes_ref}** (**{porc_horas:.1f}%**)."
        )

    else:

        st.info(
            f"⏱️ Las horas extra no presentaron variación respecto a **{mes_ref}**."
        )

    # ======================================================
    # COSTO HORAS EXTRA
    # ======================================================

    if diff_valor > 0:

        st.error(
            f"💰 El costo de horas extra **aumentó $ {diff_valor:,.0f}** respecto a "
            f"**{mes_ref}** (**+{porc_valor:.1f}%**)."
        )

    elif diff_valor < 0:

        st.success(
            f"💰 El costo de horas extra **disminuyó $ {abs(diff_valor):,.0f}** respecto a "
            f"**{mes_ref}** (**{porc_valor:.1f}%**)."
        )

    else:

        st.info(
            f"💰 El costo de horas extra no presentó variación respecto a **{mes_ref}**."
        )