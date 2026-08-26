from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    ColumnsAutoSizeMode,
)

import altair as alt
import pandas as pd
import streamlit as st


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

ORDEN_MESES = [
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
]

MAPA_MESES = {
    mes: numero
    for numero, mes in enumerate(ORDEN_MESES, start=1)
}

ABREV_MESES = {
    "ENERO": "ENE",
    "FEBRERO": "FEB",
    "MARZO": "MAR",
    "ABRIL": "ABR",
    "MAYO": "MAY",
    "JUNIO": "JUN",
    "JULIO": "JUL",
    "AGOSTO": "AGO",
    "SEPTIEMBRE": "SEP",
    "OCTUBRE": "OCT",
    "NOVIEMBRE": "NOV",
    "DICIEMBRE": "DIC",
}


# ==========================================================
# TABLA AGGRID LOCAL PARA FACTURACIÓN
# ==========================================================

def _mostrar_tabla(df, height=460):
    if df is None or df.empty:
        return

    df = df.copy()

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        sortable=True,
        filter=True,
        floatingFilter=True,
        editable=False,
        resizable=True,
        minWidth=120,
        cellStyle={
            "fontSize": "13px",
            "fontWeight": "500",
            "display": "flex",
            "alignItems": "center",
        },
    )

    gb.configure_grid_options(
        animateRows=True,
        pagination=True,
        paginationPageSize=20,
        rowHeight=42,
        headerHeight=50,
        floatingFiltersHeight=42,
        suppressRowClickSelection=True,
        enableCellTextSelection=True,
        rowSelection="single",
        domLayout="normal",
    )

    css = {
        ".ag-root-wrapper": {
            "border": "1px solid #E5E7EB",
            "border-radius": "12px",
            "overflow": "hidden",
            "box-shadow": "0 6px 18px rgba(15,23,42,.08)",
        },
        ".ag-header": {
            "background-color": "#EEF2F7 !important",
            "border-bottom": "1px solid #D1D5DB",
        },
        ".ag-header-cell": {
            "color": "#1F2937 !important",
            "font-weight": "700 !important",
            "font-size": "13px !important",
            "border-right": "1px solid #E5E7EB",
        },
        ".ag-header-cell-label": {
            "justify-content": "center",
        },
        ".ag-floating-filter": {
            "background-color": "#F8FAFC !important",
            "border-right": "1px solid #E5E7EB",
        },
        ".ag-floating-filter-body input": {
            "border-radius": "6px",
            "border": "1px solid #CBD5E1",
            "padding": "5px 7px",
            "font-size": "12px",
            "background-color": "#FFFFFF",
        },
        ".ag-cell": {
            "font-size": "13px",
            "color": "#222",
            "border-right": "1px solid #EEF2F7",
            "display": "flex",
            "align-items": "center",
        },
        ".ag-row-hover": {
            "background-color": "#ECFDF3 !important",
        },
        ".ag-row-selected": {
            "background-color": "#D1FAE5 !important",
        },
        ".ag-paging-panel": {
            "font-size": "13px",
            "font-weight": "600",
            "padding": "8px",
        },
    }

    AgGrid(
        df,
        gridOptions=gb.build(),
        height=height,
        theme="streamlit",
        custom_css=css,
        fit_columns_on_grid_load=True,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
    )


# ==========================================================
# UTILIDADES
# ==========================================================

def _normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip().upper()


def _moneda(valor):
    try:
        return f"$ {float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "$ 0"


def _buscar_columna(df, candidatos):
    columnas = {
        str(columna).strip().upper(): columna
        for columna in df.columns
    }

    for candidato in candidatos:
        candidato = candidato.strip().upper()

        if candidato in columnas:
            return columnas[candidato]

    return None


def _lista_unicos(df, columna):
    if columna is None:
        return []

    valores = (
        df[columna]
        .dropna()
        .astype(str)
        .str.strip()
    )

    return sorted(
        [
            valor
            for valor in valores.unique()
            if valor
        ]
    )


def _formatear_porcentaje(valor):
    try:
        return f"{float(valor) * 100:.1f}%".replace(".", ",")
    except Exception:
        return "0,0%"


# ==========================================================
# PREPARAR FACTURACIÓN
# ==========================================================

def _preparar_facturacion(df):
    df = df.copy()

    col_mes_servicio = _buscar_columna(
        df,
        ["MES SERVICIO", "MES_SERVICIO"],
    )

    col_anio = _buscar_columna(
        df,
        ["AÑO", "ANIO"],
    )

    col_total = _buscar_columna(
        df,
        ["TOTAL"],
    )

    col_factura = _buscar_columna(
        df,
        ["FACTURA", "NUM FACTURA", "NRO FACTURA"],
    )

    col_proveedor = _buscar_columna(
        df,
        ["PROVEEDOR"],
    )

    col_ciudad = _buscar_columna(
        df,
        ["CIUDAD", "ZONA"],
    )

    col_concepto = _buscar_columna(
        df,
        ["CONCEPTO", "CONCEPTO.1"],
    )

    if col_mes_servicio is None:
        raise ValueError(
            "No se encontró la columna MES SERVICIO "
            "en la hoja FACTURACION."
        )

    if col_anio is None:
        raise ValueError(
            "No se encontró la columna AÑO "
            "en la hoja FACTURACION."
        )

    if col_total is None:
        raise ValueError(
            "No se encontró la columna TOTAL "
            "en la hoja FACTURACION."
        )

    df[col_mes_servicio] = (
        df[col_mes_servicio]
        .apply(_normalizar_texto)
    )

    if col_proveedor is not None:
        df[col_proveedor] = (
            df[col_proveedor]
            .astype(str)
            .str.strip()
            .str.upper()
    )

    df[col_anio] = pd.to_numeric(
        df[col_anio],
        errors="coerce",
    )

    df[col_total] = pd.to_numeric(
        df[col_total],
        errors="coerce",
    ).fillna(0)

    df["__MES_ORDEN"] = (
        df[col_mes_servicio]
        .map(MAPA_MESES)
    )

    df["__PERIODO_ORDEN"] = (
        df[col_anio] * 100
        + df["__MES_ORDEN"]
    )

    validos = (
        df[col_anio].notna()
        & df["__MES_ORDEN"].notna()
    )

    df["__PERIODO_FECHA"] = pd.NaT

    df.loc[validos, "__PERIODO_FECHA"] = pd.to_datetime(
        {
            "year": df.loc[validos, col_anio].astype(int),
            "month": df.loc[validos, "__MES_ORDEN"].astype(int),
            "day": 1,
        },
        errors="coerce",
    )

    df["PERIODO"] = ""
    df["PERIODO_CORTO"] = ""

    df.loc[validos, "PERIODO"] = (
        df.loc[validos, col_mes_servicio].astype(str)
        + " "
        + df.loc[validos, col_anio].astype(int).astype(str)
    )

    df.loc[validos, "PERIODO_CORTO"] = (
        df.loc[validos, col_mes_servicio].map(ABREV_MESES)
        + " "
        + df.loc[validos, col_anio].astype(int).astype(str)
    )

    return {
        "df": df,
        "mes_servicio": col_mes_servicio,
        "anio": col_anio,
        "total": col_total,
        "factura": col_factura,
        "proveedor": col_proveedor,
        "ciudad": col_ciudad,
        "concepto": col_concepto,
    }


# ==========================================================
# FILTROS
# ==========================================================

def _mostrar_filtros(
    df,
    col_anio,
    col_mes,
    col_ciudad,
    col_proveedor,
    col_concepto,
):
    st.markdown("### 🔎 Filtros")

    anios_disponibles = sorted(
        [
            int(valor)
            for valor in df[col_anio].dropna().unique()
        ]
    )

    meses_presentes = set(
        df[col_mes]
        .dropna()
        .astype(str)
        .str.upper()
    )

    meses_disponibles = [
        mes
        for mes in ORDEN_MESES
        if mes in meses_presentes
    ]

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        anio = st.selectbox(
            "Año",
            ["TODOS"] + anios_disponibles,
            key="facturacion_anio",
        )

    with c2:
        mes = st.selectbox(
            "Mes servicio",
            ["TODOS"] + meses_disponibles,
            key="facturacion_mes",
        )

    with c3:
        ciudad = st.selectbox(
            "Ciudad",
            ["TODAS"] + _lista_unicos(df, col_ciudad),
            key="facturacion_ciudad",
        )

    with c4:
        proveedor = st.selectbox(
            "Proveedor",
            ["TODOS"] + _lista_unicos(df, col_proveedor),
            key="facturacion_proveedor",
        )

    with c5:
        concepto = st.selectbox(
            "Concepto",
            ["TODOS"] + _lista_unicos(df, col_concepto),
            key="facturacion_concepto",
        )

    return anio, mes, ciudad, proveedor, concepto


def _aplicar_filtros(
    df,
    col_anio,
    col_mes,
    col_ciudad,
    col_proveedor,
    col_concepto,
    anio,
    mes,
    ciudad,
    proveedor,
    concepto,
):
    salida = df.copy()

    if anio != "TODOS":
        salida = salida[
            salida[col_anio] == int(anio)
        ]

    if mes != "TODOS":
        salida = salida[
            salida[col_mes].astype(str).str.upper() == mes
        ]

    if col_ciudad is not None and ciudad != "TODAS":
        salida = salida[
            salida[col_ciudad].astype(str).str.strip() == ciudad
        ]

    if col_proveedor is not None and proveedor != "TODOS":
        salida = salida[
            salida[col_proveedor].astype(str).str.strip() == proveedor
        ]

    if col_concepto is not None and concepto != "TODOS":
        salida = salida[
            salida[col_concepto].astype(str).str.strip() == concepto
        ]

    return salida.reset_index(drop=True)


# ==========================================================
# KPIs
# ==========================================================

def _mostrar_kpis(df, col_total, col_factura, col_proveedor):
    total_facturado = float(df[col_total].sum())

    if col_factura is not None:
        cantidad_facturas = (
            df[col_factura]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )
    else:
        cantidad_facturas = len(df)

    if col_proveedor is not None:
        cantidad_proveedores = (
            df[col_proveedor]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )
    else:
        cantidad_proveedores = 0

    promedio_factura = (
        total_facturado / cantidad_facturas
        if cantidad_facturas
        else 0
    )

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("💰 Total facturado", _moneda(total_facturado))
    k2.metric("🧾 N.º facturas", f"{cantidad_facturas:,}")
    k3.metric("🏢 Proveedores", f"{cantidad_proveedores:,}")
    k4.metric("📌 Promedio por factura", _moneda(promedio_factura))


# ==========================================================
# RESUMEN POR PERÍODO
# ==========================================================

def _resumen_por_periodo(
    df,
    col_anio,
    col_mes,
    col_total,
    col_factura,
):
    columnas_grupo = [
        col_anio,
        col_mes,
        "__MES_ORDEN",
        "__PERIODO_ORDEN",
        "__PERIODO_FECHA",
        "PERIODO",
        "PERIODO_CORTO",
    ]

    if col_factura is not None:
        resumen = (
            df
            .groupby(columnas_grupo, dropna=False)
            .agg(
                FACTURAS=(col_factura, "nunique"),
                TOTAL=(col_total, "sum"),
            )
            .reset_index()
        )
    else:
        resumen = (
            df
            .groupby(columnas_grupo, dropna=False)
            .agg(
                FACTURAS=(col_total, "size"),
                TOTAL=(col_total, "sum"),
            )
            .reset_index()
        )

    return (
        resumen
        .dropna(subset=["__PERIODO_FECHA"])
        .sort_values("__PERIODO_FECHA")
        .reset_index(drop=True)
    )


# ==========================================================
# RESUMEN
# ==========================================================

def _mostrar_resumen(
    df,
    col_anio,
    col_mes,
    col_total,
    col_factura,
):
    st.markdown("### 📅 Facturación por período de servicio")

    resumen = _resumen_por_periodo(
        df=df,
        col_anio=col_anio,
        col_mes=col_mes,
        col_total=col_total,
        col_factura=col_factura,
    )

    if resumen.empty:
        st.warning("No existen períodos válidos para mostrar.")
        return

    tabla = resumen[
        ["PERIODO", "FACTURAS", "TOTAL"]
    ].copy()

    tabla["TOTAL"] = tabla["TOTAL"].apply(_moneda)

    _mostrar_tabla(
        tabla,
        height=520,
    )

    st.markdown("### 📈 Evolución mensual de facturación")

    grafico = resumen[
        [
            "PERIODO",
            "PERIODO_CORTO",
            "FACTURAS",
            "TOTAL",
        ]
    ].copy()

    grafico["TOTAL_LABEL"] = grafico["TOTAL"].apply(_moneda)

    orden_periodos = grafico["PERIODO_CORTO"].tolist()

    eje_x = alt.X(
        "PERIODO_CORTO:N",
        sort=orden_periodos,
        title=None,
        axis=alt.Axis(
            labelAngle=0,
            labelFontSize=12,
            labelFontWeight="bold",
            labelPadding=12,
            grid=False,
        ),
    )

    eje_y = alt.Y(
        "TOTAL:Q",
        title="Total facturado",
        axis=alt.Axis(
            labelFontSize=12,
            titleFontSize=13,
            format=",.0f",
        ),
        scale=alt.Scale(zero=True, padding=80,),
    )

    tooltips = [
        alt.Tooltip("PERIODO:N", title="Período"),
        alt.Tooltip("FACTURAS:Q", title="Facturas", format=",.0f"),
        alt.Tooltip("TOTAL_LABEL:N", title="Total facturado"),
    ]

    linea = (
        alt.Chart(grafico)
        .mark_line(strokeWidth=3)
        .encode(
            x=eje_x,
            y=eje_y,
            tooltip=tooltips,
        )
    )

    puntos = (
        alt.Chart(grafico)
        .mark_point(
            filled=True,
            size=100,
        )
        .encode(
            x=eje_x,
            y=eje_y,
            tooltip=tooltips,
        )
    )

    etiquetas = (
        alt.Chart(grafico)
        .mark_text(
            dy=-16,
            fontSize=11,
            fontWeight="bold",
        )
        .encode(
            x=alt.X(
                "PERIODO_CORTO:N",
                sort=orden_periodos,
                title=None,
            ),
            y=alt.Y(
                "TOTAL:Q",
                title="Total facturado",
            ),
            text=alt.Text("TOTAL_LABEL:N"),
        )
    )

    grafico_final = (
        linea
        + puntos
        + etiquetas
    ).properties(
        height=430,
    ).configure_view(
        strokeWidth=0,
    ).configure_axis(
        labelColor="#334155",
        titleColor="#334155",
    )

    st.altair_chart(
        grafico_final,
        use_container_width=True,
    )


# ==========================================================
# MATRIZ MENSUAL
# ==========================================================

def _mostrar_matriz_mensual(df, col_ciudad, col_total):
    st.markdown("### 📅 Matriz mensual de facturación")

    if col_ciudad is None:
        st.warning(
            "No se encontró la columna CIUDAD "
            "para construir la matriz."
        )
        return

    periodos = (
        df[["PERIODO", "__PERIODO_FECHA"]]
        .dropna()
        .drop_duplicates()
        .sort_values("__PERIODO_FECHA")["PERIODO"]
        .tolist()
    )

    matriz = pd.pivot_table(
        df,
        index=col_ciudad,
        columns="PERIODO",
        values=col_total,
        aggfunc="sum",
        fill_value=0,
        margins=False,
    )

    matriz = matriz.reindex(
        columns=periodos,
        fill_value=0,
    )

    matriz["TOTAL GENERAL"] = matriz.sum(axis=1)

    fila_total = pd.DataFrame(
        [matriz.sum(axis=0)],
        index=["TOTAL GENERAL"],
    )

    matriz = pd.concat([matriz, fila_total])
    matriz.index.name = "CIUDAD"

    matriz_mostrar = matriz.copy()

    for columna in matriz_mostrar.columns:
        matriz_mostrar[columna] = (
            matriz_mostrar[columna].apply(_moneda)
        )

    _mostrar_tabla(
        matriz_mostrar.reset_index(),
        height=520,
    )


# ==========================================================
# POR PROVEEDOR
# ==========================================================

def _mostrar_por_proveedor(
    df,
    col_proveedor,
    col_factura,
    col_total,
):
    st.markdown("### 🏢 Facturación por proveedor")

    if col_proveedor is None:
        st.warning("No se encontró la columna PROVEEDOR.")
        return

    if col_factura is not None:
        resumen = (
            df
            .groupby(col_proveedor, dropna=False)
            .agg(
                FACTURAS=(col_factura, "nunique"),
                TOTAL=(col_total, "sum"),
            )
            .reset_index()
        )
    else:
        resumen = (
            df
            .groupby(col_proveedor, dropna=False)
            .agg(
                FACTURAS=(col_total, "size"),
                TOTAL=(col_total, "sum"),
            )
            .reset_index()
        )

    resumen = (
        resumen
        .sort_values("TOTAL", ascending=False)
        .reset_index(drop=True)
    )

    total_general = float(resumen["TOTAL"].sum())

    resumen["PARTICIPACIÓN"] = (
        resumen["TOTAL"] / total_general
        if total_general
        else 0
    )

    mostrar = resumen.copy()
    mostrar["TOTAL"] = mostrar["TOTAL"].apply(_moneda)
    mostrar["PARTICIPACIÓN"] = (
        mostrar["PARTICIPACIÓN"]
        .apply(_formatear_porcentaje)
    )

    _mostrar_tabla(
        mostrar,
        height=460,
    )

    st.markdown("### 📈 Proveedores con mayor facturación")

    grafico = (
        resumen
        .head(10)
        .copy()
    )

    grafico["TOTAL_LABEL"] = (
        grafico["TOTAL"]
        .apply(_moneda)
    )

    orden_proveedores = (
        grafico[col_proveedor]
        .tolist()
    )

    max_total = float(grafico["TOTAL"].max()) if not grafico.empty else 0

    limite_superior = (
        max_total * 1.12
        if max_total > 0
        else 1
    )

    eje_x = alt.X(
        f"{col_proveedor}:N",
        sort=orden_proveedores,
        title=None,
        axis=alt.Axis(
            labelAngle=-45,
            labelFontSize=11,
            labelPadding=10,
        ),
    )

    eje_y = alt.Y(
        "TOTAL:Q",
        title="Facturación ($)",
        axis=alt.Axis(
            format=",.0f",
            labelFontSize=11,
        ),
        scale=alt.Scale(
            domain=[0, limite_superior],
        ),
    )

    tooltips = [
        alt.Tooltip(
            f"{col_proveedor}:N",
            title="Proveedor",
        ),
        alt.Tooltip(
            "TOTAL_LABEL:N",
            title="Facturación",
        ),
    ]

    linea = (
        alt.Chart(grafico)
        .mark_line(
            strokeWidth=3,
        )
        .encode(
            x=eje_x,
            y=eje_y,
            tooltip=tooltips,
        )
    )

    puntos = (
        alt.Chart(grafico)
        .mark_point(
            filled=True,
            size=110,
        )
        .encode(
            x=eje_x,
            y=eje_y,
            tooltip=tooltips,
        )
    )

    etiquetas = (
        alt.Chart(grafico)
        .mark_text(
            dy=-16,
            fontSize=11,
            fontWeight="bold",
        )
        .encode(
            x=eje_x,
            y=eje_y,
            text=alt.Text(
                "TOTAL_LABEL:N",
            ),
        )
    )

    grafico_final = (
        linea
        + puntos
        + etiquetas
    ).properties(
        height=420,
    ).configure_view(
        strokeWidth=0,
    ).configure_axis(
        labelColor="#334155",
        titleColor="#334155",
    )

    st.altair_chart(
        grafico_final,
        use_container_width=True,
    )


# ==========================================================
# DETALLE
# ==========================================================

def _mostrar_detalle(df):
    st.markdown("### 📄 Detalle de facturación")

    detalle = df.drop(
        columns=[
            "__MES_ORDEN",
            "__PERIODO_ORDEN",
            "__PERIODO_FECHA",
            "PERIODO",
            "PERIODO_CORTO",
        ],
        errors="ignore",
    ).copy()

    # ======================================================
    # FORMATO FECHA CORTA
    # ======================================================

    columnas_fecha = [
        "FECHA",
        "FECHA FACTURA",
        "VENCIMIENTO",
    ]

    for columna in columnas_fecha:

        if columna not in detalle.columns:
            continue

        serie_fecha = pd.to_datetime(
            detalle[columna],
            dayfirst=True,
            errors="coerce",
        )

        detalle[columna] = (
            serie_fecha
            .dt.strftime("%d/%m/%Y")
            .fillna("")
        )

    # ======================================================
    # MOSTRAR DETALLE
    # ======================================================

    st.caption(
        f"{len(detalle):,} registros encontrados."
    )

    _mostrar_tabla(
        detalle,
        height=560,
    )

# ==========================================================
# MÓDULO PRINCIPAL
# ==========================================================

def mostrar_facturacion(hojas):
    st.subheader("🧾 Facturación")

    if "FACTURACION" not in hojas:
        st.error(
            "No se encontró la hoja FACTURACION "
            "en INFORME_LIQUIDACION.xlsb."
        )
        return

    datos = _preparar_facturacion(
        hojas["FACTURACION"]
    )

    df = datos["df"]

    col_mes = datos["mes_servicio"]
    col_anio = datos["anio"]
    col_total = datos["total"]
    col_factura = datos["factura"]
    col_proveedor = datos["proveedor"]
    col_ciudad = datos["ciudad"]
    col_concepto = datos["concepto"]

    (
        anio,
        mes,
        ciudad,
        proveedor,
        concepto,
    ) = _mostrar_filtros(
        df,
        col_anio,
        col_mes,
        col_ciudad,
        col_proveedor,
        col_concepto,
    )

    df_filtrado = _aplicar_filtros(
        df=df,
        col_anio=col_anio,
        col_mes=col_mes,
        col_ciudad=col_ciudad,
        col_proveedor=col_proveedor,
        col_concepto=col_concepto,
        anio=anio,
        mes=mes,
        ciudad=ciudad,
        proveedor=proveedor,
        concepto=concepto,
    )

    if df_filtrado.empty:
        st.warning(
            "No existen registros para "
            "los filtros seleccionados."
        )
        return

    st.markdown("### Análisis")

    subvista = st.radio(
        "",
        [
            "📊 Resumen",
            "📅 Matriz mensual",
            "🏢 Por proveedor",
            "📄 Detalle",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="facturacion_subvista",
    )

    st.divider()

    if subvista == "📊 Resumen":
        _mostrar_kpis(
            df_filtrado,
            col_total,
            col_factura,
            col_proveedor,
        )

        st.divider()

        _mostrar_resumen(
            df_filtrado,
            col_anio,
            col_mes,
            col_total,
            col_factura,
        )

    elif subvista == "📅 Matriz mensual":
        _mostrar_matriz_mensual(
            df_filtrado,
            col_ciudad,
            col_total,
        )

    elif subvista == "🏢 Por proveedor":
        _mostrar_por_proveedor(
            df_filtrado,
            col_proveedor,
            col_factura,
            col_total,
        )

    elif subvista == "📄 Detalle":
        _mostrar_detalle(df_filtrado)