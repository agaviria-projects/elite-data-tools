import streamlit as st
import pandas as pd
from components.tablas import mostrar_tabla


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
# KPI PERSONALIZADO
# ==========================================================

def mostrar_kpi_personalizado(
    etiqueta,
    valor,
    diferencia,
    porcentaje,
    tipo="normal",
    moneda=False,
    decimales=1,
):
    """
    KPI con control explícito de flecha y color.

    tipo="normal":
        aumento     -> verde
        disminución -> rojo

    tipo="costo":
        aumento     -> rojo
        disminución -> verde
    """

    if diferencia > 0:
        flecha = "↑"
    elif diferencia < 0:
        flecha = "↓"
    else:
        flecha = "→"

    if tipo == "costo":
        if diferencia < 0:
            color_texto = "#15803D"
            color_fondo = "#DCFCE7"
        elif diferencia > 0:
            color_texto = "#DC2626"
            color_fondo = "#FEE2E2"
        else:
            color_texto = "#475569"
            color_fondo = "#E2E8F0"
    else:
        if diferencia > 0:
            color_texto = "#15803D"
            color_fondo = "#DCFCE7"
        elif diferencia < 0:
            color_texto = "#DC2626"
            color_fondo = "#FEE2E2"
        else:
            color_texto = "#475569"
            color_fondo = "#E2E8F0"

    if moneda:
        valor_mostrar = f"$ {valor:,.0f}"
        diferencia_mostrar = f"$ {abs(diferencia):,.0f}"
    else:
        if decimales == 0:
            valor_mostrar = f"{valor:,.0f}"
            diferencia_mostrar = f"{abs(diferencia):,.0f}"
        else:
            valor_mostrar = f"{valor:,.1f}"
            diferencia_mostrar = f"{abs(diferencia):,.1f}"

    signo = "+" if diferencia > 0 else "-" if diferencia < 0 else ""

    # IMPORTANTE:
    # HTML en una sola línea para evitar que Markdown lo interprete
    # como bloque de código por la indentación.
    html = (
        f'<div style="padding:2px 0 10px 0;">'
        f'<div style="font-size:14px;font-weight:700;color:#111827;'
        f'margin-bottom:3px;">{etiqueta}</div>'
        f'<div style="font-size:28px;line-height:1.2;font-weight:800;'
        f'color:#020617;margin-bottom:7px;">{valor_mostrar}</div>'
        f'<span style="display:inline-block;background:{color_fondo};'
        f'color:{color_texto};border-radius:999px;padding:3px 8px;'
        f'font-size:13px;font-weight:700;">'
        f'{flecha} {signo}{diferencia_mostrar} ({porcentaje:.1f}%)'
        f'</span>'
        f'</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


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

        mostrar_kpi_personalizado(
            etiqueta="🚗 Vehículos",
            valor=vehiculos_actual,
            diferencia=diff_veh,
            porcentaje=porc_veh,
            tipo="normal",
            moneda=False,
            decimales=0,
        )

    with c2:

        mostrar_kpi_personalizado(
            etiqueta="🕒 Horas Extras",
            valor=horas_actual,
            diferencia=diff_horas,
            porcentaje=porc_horas,
            tipo="costo",
            moneda=False,
            decimales=1,
        )

    with c3:

        mostrar_kpi_personalizado(
            etiqueta="💰 Valor Hora Extra",
            valor=valor_actual,
            diferencia=diff_valor,
            porcentaje=porc_valor,
            tipo="costo",
            moneda=True,
            decimales=0,
        )

    st.divider()

    # ======================================================
    # ANÁLISIS POR VEHÍCULO (SPRINT 1)
    # ======================================================

    horas_actual_placa = (
        df_actual
        .groupby("PLACA", as_index=False)["HORAS EXTRA"]
        .sum()
        .rename(
            columns={
                "HORAS EXTRA": "HORAS_ACTUAL"
            }
        )
    )

    horas_anterior_placa = (
        df_anterior
        .groupby("PLACA", as_index=False)["HORAS EXTRA"]
        .sum()
        .rename(
            columns={
                "HORAS EXTRA": "HORAS_ANTERIOR"
            }
        )
    )

    comparativo_placas = (
        horas_actual_placa.merge(
            horas_anterior_placa,
            on="PLACA",
            how="outer"
        )
        .fillna(0)
    )

    comparativo_placas["DIFERENCIA"] = (
        comparativo_placas["HORAS_ACTUAL"]
        -
        comparativo_placas["HORAS_ANTERIOR"]
    )

    comparativo_placas = (
        comparativo_placas
        .sort_values(
            "DIFERENCIA",
            ascending=False
        )
    )

    st.subheader("🚗 Comparativo de horas extra por vehículo")

    mostrar_tabla(
        comparativo_placas
    )

    # ======================================================
    # SPRINT 1 - COMPARATIVO POR VEHÍCULO
    # ======================================================

    columnas = [
        "PLACA",
        "HORAS EXTRA"
    ]

    actual_placa = (
        df_actual[columnas]
        .groupby("PLACA", as_index=False)
        .sum()
        .rename(
            columns={
                "HORAS EXTRA": "HORAS MES ACTUAL"
            }
        )
    )

    anterior_placa = (
        df_anterior[columnas]
        .groupby("PLACA", as_index=False)
        .sum()
        .rename(
            columns={
                "HORAS EXTRA": "HORAS MES ANTERIOR"
            }
        )
    )

    comparativo = (
        actual_placa.merge(
            anterior_placa,
            on="PLACA",
            how="outer"
        )
        .fillna(0)
    )

    comparativo["DIFERENCIA"] = (
        comparativo["HORAS MES ACTUAL"]
        -
        comparativo["HORAS MES ANTERIOR"]
    )

    comparativo = comparativo.sort_values(
        by="DIFERENCIA",
        ascending=False
    )

    # ======================================================
    # TOP 3 VEHÍCULOS CON MAYOR AUMENTO
    # ======================================================

    top_aumento = (
        comparativo[
            comparativo["DIFERENCIA"] > 0
        ]
        .head(3)
        .copy()
    )

    if not top_aumento.empty:

        top_aumento = top_aumento[
            [
                "PLACA",
                "DIFERENCIA"
            ]
        ]

        top_aumento = top_aumento.rename(
            columns={
                "PLACA": "Vehículo",
                "DIFERENCIA": "Horas adicionales"
            }
        )

        st.subheader("🚗 Vehículos que más aumentaron las horas extra")

        mostrar_tabla(
            top_aumento
        )

        # ======================================================
        # TOP 3 ZONAS CON MAYOR AUMENTO
        # ======================================================

        columnas = [
            "ZONA",
            "HORAS EXTRA"
        ]

        actual_zona = (
            df_actual[columnas]
            .groupby("ZONA", as_index=False)
            .sum()
            .rename(
                columns={
                    "HORAS EXTRA": "HORAS MES ACTUAL"
                }
            )
        )

        anterior_zona = (
            df_anterior[columnas]
            .groupby("ZONA", as_index=False)
            .sum()
            .rename(
                columns={
                    "HORAS EXTRA": "HORAS MES ANTERIOR"
                }
            )
        )

        comparativo_zonas = (
            actual_zona.merge(
                anterior_zona,
                on="ZONA",
                how="outer"
            )
            .fillna(0)
        )

        comparativo_zonas["DIFERENCIA"] = (
            comparativo_zonas["HORAS MES ACTUAL"]
            -
            comparativo_zonas["HORAS MES ANTERIOR"]
        )

        comparativo_zonas = (
            comparativo_zonas[
                comparativo_zonas["DIFERENCIA"] > 0
            ]
            .sort_values(
                "DIFERENCIA",
                ascending=False
            )
            .head(3)
            .copy()
        )

        if not comparativo_zonas.empty:

            comparativo_zonas = comparativo_zonas[
                [
                    "ZONA",
                    "DIFERENCIA"
                ]
            ]

            comparativo_zonas = comparativo_zonas.rename(
                columns={
                    "ZONA": "Zona",
                    "DIFERENCIA": "Horas adicionales"
                }
            )

            st.subheader("🌍 Zonas donde más aumentaron las horas extra")

            mostrar_tabla(
                comparativo_zonas
            )

            mensajes = []

            for _, fila in comparativo_zonas.iterrows():

                mensajes.append(
                    f"• **{fila['Zona']}** → +{fila['Horas adicionales']:.1f} horas"
                )

            st.info(
                "El mayor incremento de horas extra se concentró en:\n\n"
                + "\n".join(mensajes)
            )

        # ======================================================
        # TOP 3 VEHÍCULOS CON MAYOR AUMENTO EN COSTO
        # ======================================================

        columnas = [
            "PLACA",
            "VALOR HORA EXTRA"
        ]

        actual_costo = (
            df_actual[columnas]
            .groupby("PLACA", as_index=False)
            .sum()
            .rename(
                columns={
                    "VALOR HORA EXTRA": "COSTO MES ACTUAL"
                }
            )
        )

        anterior_costo = (
            df_anterior[columnas]
            .groupby("PLACA", as_index=False)
            .sum()
            .rename(
                columns={
                    "VALOR HORA EXTRA": "COSTO MES ANTERIOR"
                }
            )
        )

        comparativo_costos = (
            actual_costo.merge(
                anterior_costo,
                on="PLACA",
                how="outer"
            )
            .fillna(0)
        )

        comparativo_costos["DIFERENCIA"] = (
            comparativo_costos["COSTO MES ACTUAL"]
            -
            comparativo_costos["COSTO MES ANTERIOR"]
        )

        comparativo_costos = (
            comparativo_costos[
                comparativo_costos["DIFERENCIA"] > 0
            ]
            .sort_values(
                "DIFERENCIA",
                ascending=False
            )
            .head(3)
            .copy()
        )

        if not comparativo_costos.empty:

            comparativo_costos = comparativo_costos[
                [
                    "PLACA",
                    "DIFERENCIA"
                ]
            ]

            comparativo_costos = comparativo_costos.rename(
                columns={
                    "PLACA": "Vehículo",
                    "DIFERENCIA": "Incremento ($)"
                }
            )

            st.subheader("💰 Vehículos con mayor aumento en el costo de horas extra")

            comparativo_costos_mostrar = comparativo_costos.copy()

            comparativo_costos_mostrar["Incremento ($)"] = (
                comparativo_costos_mostrar["Incremento ($)"]
                .apply(lambda valor: f"$ {valor:,.0f}")
            )

            mostrar_tabla(
                comparativo_costos_mostrar
            )

            # ==================================================
            # CONCLUSIÓN
            # ==================================================

            principal = comparativo_costos.iloc[0]

            total = comparativo_costos["Incremento ($)"].sum()

            participacion = (
                principal["Incremento ($)"] / total * 100
            )

            st.success(
                f"""
### 📌 Resultado principal

El vehículo **{principal['Vehículo']}** presentó el mayor incremento en el costo de horas extra durante el período.

**Incremento registrado**

💰 $ {principal['Incremento ($)']:,.0f}

**Participación del incremento total**

📈 {participacion:.1f} %
"""
            )

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