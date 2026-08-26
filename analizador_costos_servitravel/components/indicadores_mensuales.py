import pandas as pd
import streamlit as st

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    ColumnsAutoSizeMode,
)

from components.tablas import mostrar_tabla



# ==========================================================
# UTILIDADES
# ==========================================================

def calcular_variacion(actual, anterior):
    diferencia = actual - anterior

    if anterior == 0:
        porcentaje = 0
    else:
        porcentaje = (diferencia / anterior) * 100

    return diferencia, porcentaje


def _altura_tabla_foco(df):
    if df is None or df.empty:
        return 105

    return min(220, 86 + (len(df) * 36))


def _mostrar_tabla_foco(
    df: pd.DataFrame,
    columnas_moneda=None,
):
    """
    AgGrid compacto para las tablas Top 3.
    Conserva el estilo corporativo verde y evita espacios vacíos grandes.
    """

    if df is None or df.empty:
        st.info("Sin novedades para este criterio.")
        return

    tabla = df.copy()
    columnas_moneda = columnas_moneda or []

    for columna in columnas_moneda:
        if columna in tabla.columns:
            tabla[columna] = pd.to_numeric(
                tabla[columna],
                errors="coerce",
            ).fillna(0)

    gb = GridOptionsBuilder.from_dataframe(tabla)

    gb.configure_default_column(
        sortable=True,
        filter=True,
        floatingFilter=True,
        editable=False,
        resizable=True,
        minWidth=150,
        cellStyle={
            "fontSize": "13px",
            "fontWeight": "500",
            "display": "flex",
            "alignItems": "center",
        },
    )

    for columna in tabla.columns:
        nombre = str(columna)

        if columna in columnas_moneda:
            gb.configure_column(
                columna,
                type=["numericColumn"],
                valueFormatter=(
                    "'$ ' + Number(value).toLocaleString('es-CO', "
                    "{maximumFractionDigits: 0})"
                ),
            )

        elif "Horas" in nombre or "HORAS" in nombre:
            gb.configure_column(
                columna,
                type=["numericColumn"],
                valueFormatter=(
                    "Number(value).toLocaleString('es-CO', "
                    "{minimumFractionDigits: 1, maximumFractionDigits: 1})"
                ),
            )

    gb.configure_grid_options(
        animateRows=True,
        pagination=False,
        rowHeight=36,
        headerHeight=42,
        floatingFiltersHeight=36,
        suppressRowClickSelection=True,
        enableCellTextSelection=True,
        ensureDomOrder=True,
        rowSelection="single",
        domLayout="normal",
    )

    css = {
        ".ag-root-wrapper": {
            "border": "1px solid #D1D5DB",
            "border-radius": "10px",
            "overflow": "hidden",
            "box-shadow": "0 4px 12px rgba(15,23,42,.07)",
        },
        ".ag-header": {
            "background-color": "#166534 !important",
            "border-bottom": "1px solid #14532D",
        },
        ".ag-header-cell": {
            "background-color": "#166534 !important",
            "color": "#FFFFFF !important",
            "font-weight": "700 !important",
            "font-size": "12px !important",
            "border-right": "1px solid rgba(255,255,255,.20)",
        },
        ".ag-header-cell-label": {
            "justify-content": "center",
        },
        ".ag-floating-filter": {
            "background-color": "#F0FDF4 !important",
            "border-right": "1px solid #D1D5DB",
            "border-bottom": "1px solid #D1D5DB",
        },
        ".ag-floating-filter-body input": {
            "border-radius": "5px",
            "border": "1px solid #94A3B8",
            "padding": "4px 6px",
            "font-size": "11px",
            "background-color": "#FFFFFF",
        },
        ".ag-cell": {
            "font-size": "13px",
            "color": "#1F2937",
            "border-right": "1px solid #E5E7EB",
            "border-bottom": "1px solid #E5E7EB",
            "display": "flex",
            "align-items": "center",
        },
        ".ag-row-even": {
            "background-color": "#FFFFFF",
        },
        ".ag-row-odd": {
            "background-color": "#F8FAFC",
        },
        ".ag-row-hover": {
            "background-color": "#ECFDF3 !important",
        },
        ".ag-row-selected": {
            "background-color": "#D1FAE5 !important",
        },
    }

    AgGrid(
        tabla,
        gridOptions=gb.build(),
        height=_altura_tabla_foco(tabla),
        theme="streamlit",
        custom_css=css,
        fit_columns_on_grid_load=True,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
    )


# ==========================================================
# KPI PERSONALIZADO
# ==========================================================

def mostrar_kpi_personalizado(
    etiqueta,
    valor,
    diferencia,
    porcentaje,
    moneda=False,
    decimales=1,
):
    """
    Lenguaje visual único:

    AUMENTO     -> ROJO
    DISMINUCIÓN -> VERDE
    SIN CAMBIO  -> GRIS

    La flecha muestra la dirección real.
    El color muestra si requiere atención.
    """

    if diferencia > 0:
        flecha = "↑"
        color_texto = "#DC2626"
        color_fondo = "#FEE2E2"

    elif diferencia < 0:
        flecha = "↓"
        color_texto = "#15803D"
        color_fondo = "#DCFCE7"

    else:
        flecha = "→"
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
    df_filtrado: pd.DataFrame,
):
    st.subheader("📈 Indicadores Mensuales")

    # ======================================================
    # VALIDACIONES
    # ======================================================

    columnas_requeridas = [
        "FECHA",
        "PLACA",
        "HORAS EXTRA",
        "VALOR HORA EXTRA",
    ]

    faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in df.columns
    ]

    if faltantes:
        st.warning(
            "Faltan columnas necesarias para Indicadores Mensuales: "
            + ", ".join(faltantes)
        )
        return

    # ======================================================
    # PREPARAR DATOS
    # ======================================================

    datos = df.copy()

    datos["FECHA"] = pd.to_datetime(
        datos["FECHA"],
        errors="coerce",
    )

    datos = datos.dropna(subset=["FECHA"])
    datos["AÑO_MES"] = datos["FECHA"].dt.to_period("M")

    actual = df_filtrado.copy()

    actual["FECHA"] = pd.to_datetime(
        actual["FECHA"],
        errors="coerce",
    )

    actual = actual.dropna(subset=["FECHA"])

    if actual.empty:
        st.info("No existen registros para el mes seleccionado.")
        return

    mes_actual = actual["FECHA"].dt.to_period("M").iloc[0]
    mes_anterior = mes_actual - 1

    df_actual = actual

    df_anterior = datos[
        datos["AÑO_MES"] == mes_anterior
    ].copy()

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

    horas_actual = pd.to_numeric(
        df_actual["HORAS EXTRA"],
        errors="coerce",
    ).fillna(0).sum()

    horas_anterior = pd.to_numeric(
        df_anterior["HORAS EXTRA"],
        errors="coerce",
    ).fillna(0).sum()

    valor_actual = pd.to_numeric(
        df_actual["VALOR HORA EXTRA"],
        errors="coerce",
    ).fillna(0).sum()

    valor_anterior = pd.to_numeric(
        df_anterior["VALOR HORA EXTRA"],
        errors="coerce",
    ).fillna(0).sum()

    diff_veh, porc_veh = calcular_variacion(
        vehiculos_actual,
        vehiculos_anterior,
    )

    diff_horas, porc_horas = calcular_variacion(
        horas_actual,
        horas_anterior,
    )

    diff_valor, porc_valor = calcular_variacion(
        valor_actual,
        valor_anterior,
    )

    # ======================================================
    # COMPARATIVO
    # ======================================================

    st.markdown("### Comparativo")
    st.markdown(f"**{mes_actual}** vs **{mes_anterior}**")

    c1, c2, c3 = st.columns(3)

    with c1:
        mostrar_kpi_personalizado(
            etiqueta="🚗 Vehículos",
            valor=vehiculos_actual,
            diferencia=diff_veh,
            porcentaje=porc_veh,
            moneda=False,
            decimales=0,
        )

    with c2:
        mostrar_kpi_personalizado(
            etiqueta="🕒 Horas Extras",
            valor=horas_actual,
            diferencia=diff_horas,
            porcentaje=porc_horas,
            moneda=False,
            decimales=1,
        )

    with c3:
        mostrar_kpi_personalizado(
            etiqueta="💰 Valor Hora Extra",
            valor=valor_actual,
            diferencia=diff_valor,
            porcentaje=porc_valor,
            moneda=True,
            decimales=0,
        )

    st.divider()

    # ======================================================
    # NOMBRE MES ANTERIOR
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
        12: "diciembre",
    }

    mes_ref = nombre_mes[mes_anterior.month]

    # ======================================================
    # PRINCIPALES HALLAZGOS — AHORA VAN PRIMERO
    # ======================================================

    st.subheader("📋 Principales hallazgos del período")

    # VEHÍCULOS
    if diff_veh > 0:
        st.error(
            f"🚗 Se utilizaron **{diff_veh} vehículos más** respecto a "
            f"**{mes_ref}** (**+{porc_veh:.1f}%**)."
        )

    elif diff_veh < 0:
        st.success(
            f"🚗 Se utilizaron **{abs(diff_veh)} vehículo(s) menos** respecto a "
            f"**{mes_ref}** (**{porc_veh:.1f}%**)."
        )

    else:
        st.info(
            f"🚗 La cantidad de vehículos se mantuvo igual respecto a "
            f"**{mes_ref}**."
        )

    # HORAS EXTRA
    if diff_horas > 0:
        st.error(
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
            f"⏱️ Las horas extra no presentaron variación respecto a "
            f"**{mes_ref}**."
        )

    # COSTO HORAS EXTRA
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
            f"💰 El costo de horas extra no presentó variación respecto a "
            f"**{mes_ref}**."
        )

    # ======================================================
    # CÁLCULOS DE FOCOS
    # ======================================================

    # ------------------------------------------------------
    # HORAS POR VEHÍCULO
    # ------------------------------------------------------

    horas_actual_placa = (
        df_actual
        .groupby("PLACA", as_index=False)["HORAS EXTRA"]
        .sum()
        .rename(
            columns={
                "HORAS EXTRA": "HORAS_ACTUAL",
            }
        )
    )

    horas_anterior_placa = (
        df_anterior
        .groupby("PLACA", as_index=False)["HORAS EXTRA"]
        .sum()
        .rename(
            columns={
                "HORAS EXTRA": "HORAS_ANTERIOR",
            }
        )
    )

    comparativo_placas = (
        horas_actual_placa
        .merge(
            horas_anterior_placa,
            on="PLACA",
            how="outer",
        )
        .fillna(0)
    )

    comparativo_placas["DIFERENCIA"] = (
        comparativo_placas["HORAS_ACTUAL"]
        - comparativo_placas["HORAS_ANTERIOR"]
    )

    comparativo_placas = (
        comparativo_placas
        .sort_values(
            "DIFERENCIA",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    top_aumento = (
        comparativo_placas[
            comparativo_placas["DIFERENCIA"] > 0
        ]
        .head(3)
        .loc[:, ["PLACA", "DIFERENCIA"]]
        .rename(
            columns={
                "PLACA": "Vehículo",
                "DIFERENCIA": "Horas adicionales",
            }
        )
        .reset_index(drop=True)
    )

    # ------------------------------------------------------
    # HORAS POR ZONA
    # ------------------------------------------------------

    if (
        "ZONA" in df_actual.columns
        and "ZONA" in df_anterior.columns
    ):
        actual_zona = (
            df_actual
            .groupby("ZONA", as_index=False)["HORAS EXTRA"]
            .sum()
            .rename(
                columns={
                    "HORAS EXTRA": "HORAS MES ACTUAL",
                }
            )
        )

        anterior_zona = (
            df_anterior
            .groupby("ZONA", as_index=False)["HORAS EXTRA"]
            .sum()
            .rename(
                columns={
                    "HORAS EXTRA": "HORAS MES ANTERIOR",
                }
            )
        )

        comparativo_zonas = (
            actual_zona
            .merge(
                anterior_zona,
                on="ZONA",
                how="outer",
            )
            .fillna(0)
        )

        comparativo_zonas["DIFERENCIA"] = (
            comparativo_zonas["HORAS MES ACTUAL"]
            - comparativo_zonas["HORAS MES ANTERIOR"]
        )

        comparativo_zonas = (
            comparativo_zonas[
                comparativo_zonas["DIFERENCIA"] > 0
            ]
            .sort_values(
                "DIFERENCIA",
                ascending=False,
            )
            .head(3)
            .loc[:, ["ZONA", "DIFERENCIA"]]
            .rename(
                columns={
                    "ZONA": "Zona",
                    "DIFERENCIA": "Horas adicionales",
                }
            )
            .reset_index(drop=True)
        )

    else:
        comparativo_zonas = pd.DataFrame(
            columns=[
                "Zona",
                "Horas adicionales",
            ]
        )

    # ------------------------------------------------------
    # COSTOS POR VEHÍCULO
    # ------------------------------------------------------

    actual_costo = (
        df_actual
        .groupby("PLACA", as_index=False)["VALOR HORA EXTRA"]
        .sum()
        .rename(
            columns={
                "VALOR HORA EXTRA": "COSTO MES ACTUAL",
            }
        )
    )

    anterior_costo = (
        df_anterior
        .groupby("PLACA", as_index=False)["VALOR HORA EXTRA"]
        .sum()
        .rename(
            columns={
                "VALOR HORA EXTRA": "COSTO MES ANTERIOR",
            }
        )
    )

    comparativo_costos_todos = (
        actual_costo
        .merge(
            anterior_costo,
            on="PLACA",
            how="outer",
        )
        .fillna(0)
    )

    comparativo_costos_todos["DIFERENCIA"] = (
        comparativo_costos_todos["COSTO MES ACTUAL"]
        - comparativo_costos_todos["COSTO MES ANTERIOR"]
    )

    aumentos_costo = (
        comparativo_costos_todos[
            comparativo_costos_todos["DIFERENCIA"] > 0
        ]
        .sort_values(
            "DIFERENCIA",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    comparativo_costos = (
        aumentos_costo
        .head(3)
        .loc[:, ["PLACA", "DIFERENCIA"]]
        .rename(
            columns={
                "PLACA": "Vehículo",
                "DIFERENCIA": "Incremento ($)",
            }
        )
        .reset_index(drop=True)
    )

    # ======================================================
    # HALLAZGO DESTACADO — DEBAJO DE LOS HALLAZGOS
    # ======================================================

    if not aumentos_costo.empty:

        principal = aumentos_costo.iloc[0]

        total_incrementos = float(
            aumentos_costo["DIFERENCIA"].sum()
        )

        participacion = (
            principal["DIFERENCIA"] / total_incrementos * 100
            if total_incrementos
            else 0
        )

        if diff_valor < 0:
            contexto = (
                f"Aunque el costo total de horas extra disminuyó "
                f"**$ {abs(diff_valor):,.0f}**, "
            )

        elif diff_valor > 0:
            contexto = (
                f"Dentro del aumento total de **$ {diff_valor:,.0f}**, "
            )

        else:
            contexto = (
                "Aunque el costo total no presentó variación, "
            )

        st.warning(
            f"""
### 🔎 Hallazgo destacado

{contexto}el vehículo **{principal['PLACA']}** presentó el mayor incremento individual en el costo de horas extra:

**💰 +$ {principal['DIFERENCIA']:,.0f}**

Representa **{participacion:.1f}%** de los incrementos positivos detectados entre los vehículos.
"""
        )

    else:
        st.success(
            "🔎 **Hallazgo destacado:** no se detectaron vehículos con aumento "
            "en el costo de horas extra durante el período."
        )

    st.divider()

    # ======================================================
    # FOCOS DE ATENCIÓN — TABLAS COMPACTAS
    # ======================================================

    st.subheader("🎯 Focos de atención")

    col_vehiculo, col_zona = st.columns(2)

    with col_vehiculo:
        st.markdown(
            "#### 🚗 Vehículos con mayor aumento en horas extra"
        )

        _mostrar_tabla_foco(
            top_aumento,
        )

    with col_zona:
        st.markdown(
            "#### 🌍 Zonas con mayor aumento en horas extra"
        )

        _mostrar_tabla_foco(
            comparativo_zonas,
        )

    st.markdown(
        "#### 💰 Vehículos con mayor aumento en el costo de horas extra"
    )

    _mostrar_tabla_foco(
        comparativo_costos,
        columnas_moneda=["Incremento ($)"],
    )

    # ==========================================================
    # COMPARATIVO COMPLETO
    # ==========================================================

    ver_comparativo = st.toggle(
        "🔍 Ver comparativo completo de horas extra por vehículo",
        value=False,
        key=f"ver_comparativo_{mes_actual}",
    )

    if ver_comparativo:

        st.markdown(
            "#### 🚗 Comparativo completo de horas extra por vehículo"
        )

        mostrar_tabla(
            comparativo_placas
        )
