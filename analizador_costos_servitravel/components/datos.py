import streamlit as st
import pandas as pd


# ==========================================================
# MÓDULO DATOS
# ==========================================================

def mostrar_datos(hojas: dict):

    st.subheader("📂 Explorador de Datos")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🚗 Rodamientos",
            "🍽️ Viáticos",
            "🅿️ Parqueaderos",
            "🛣️ Peajes"
        ]
    )

    # ======================================================
    # RODAMIENTOS
    # ======================================================

    with tab1:

        if "RODAMIENTOS" not in hojas:

            st.warning("No existe la hoja RODAMIENTOS.")

        else:

            mostrar_rodamientos(
                hojas["RODAMIENTOS"]
            )

    # ======================================================
    # VIÁTICOS
    # ======================================================
    with tab2:

        if "VIATICOS" not in hojas:

            st.warning("No existe la hoja VIATICOS.")

        else:

            mostrar_viaticos(
                hojas["VIATICOS"]
            )
    

    # ======================================================
    # PARQUEADEROS
    # ======================================================

    with tab3:

        st.info("Próximamente.")

    # ======================================================
    # PEAJES
    # ======================================================

    with tab4:

        st.info("Próximamente.")


# ==========================================================
# RODAMIENTOS
# ==========================================================

def mostrar_rodamientos(df: pd.DataFrame):

    df = df.copy()

    st.markdown("## 🚗 Rodamientos")

    # ======================================================
    # BUSCADOR
    # ======================================================

    col_buscar, col_info = st.columns([4, 1])

    with col_buscar:

        buscar = st.text_input(
            "🔍 Digite la placa",
            placeholder="Ejemplo: TPQ282"
        )

    # ======================================================
    # FILTRAR INFORMACIÓN
    # ======================================================

    df_tabla = df.copy()

    if buscar:

        df_tabla = df_tabla[
            df_tabla["PLACA"]
            .astype(str)
            .str.contains(
                buscar,
                case=False,
                na=False
            )
        ]

    # ======================================================
    # KPIs (SOBRE EL DATAFRAME FILTRADO)
    # ======================================================

    registros = len(df_tabla)

    vehiculos = (
        df_tabla["PLACA"].astype(str).nunique()
        if "PLACA" in df_tabla.columns
        else 0
    )

    horas_extra = (
        pd.to_numeric(
            df_tabla["HORAS EXTRA"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    valor_elite = (
        pd.to_numeric(
            df_tabla["VALOR ÉLITE"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    with col_info:

        st.metric(
            "Registros",
            f"{registros:,}"
        )

    st.caption(
        f"Mostrando {registros:,} registros"
    )

    # ======================================================
    # KPIs
    # ======================================================

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:

        st.metric(
            "📄 Registros",
            f"{registros:,}"
        )

    with kpi2:

        st.metric(
            "🚗 Vehículos",
            f"{vehiculos:,}"
        )

    with kpi3:

        st.metric(
            "🕒 Horas Extra",
            f"{horas_extra:,.1f}"
        )

    with kpi4:

        st.metric(
            "💰 Valor Élite",
            f"$ {valor_elite:,.0f}"
        )

    st.divider()

    # ======================================================
    # COLUMNAS PRINCIPALES
    # ======================================================

    columnas_principales = [

        "ZONA",

        "MES",

        "PLACA",

        "TIPO",

        "FECHA",

        "INGRESO",

        "SALIDA",

        "HORAS EXTRA",

        "VALOR HORA EXTRA",

        "VALOR ÉLITE"

    ]

    columnas_principales = [
        c
        for c in columnas_principales
        if c in df_tabla.columns
    ]

    columnas_restantes = [
        c
        for c in df_tabla.columns
        if c not in columnas_principales
    ]

    df_tabla = df_tabla[
        columnas_principales + columnas_restantes
    ]

    # ======================================================
    # NORMALIZACIÓN DE FECHAS
    # ======================================================

    if "FECHA" in df_tabla.columns:

        df_tabla["FECHA"] = pd.to_datetime(
            df_tabla["FECHA"],
            errors="coerce"
        )

    # ======================================================
    # NORMALIZACIÓN DE HORAS
    # ======================================================

    def convertir_hora(valor):

        if pd.isna(valor):

            return None

        if isinstance(valor, str):

            return valor
        try:

            valor = float(valor)

            horas = int(valor)

            minutos = int(round((valor - horas) * 60))

            if minutos == 60:

                horas += 1

                minutos = 0

            return f"{horas:02d}:{minutos:02d}"

        except Exception:

            return None


    for columna in [

        "INGRESO",

        "SALIDA"

    ]:

        if columna in df_tabla.columns:

            df_tabla[columna] = (
                df_tabla[columna]
                .apply(convertir_hora)
            )

    # ======================================================
    # NORMALIZACIÓN DE VALORES NUMÉRICOS
    # ======================================================

    columnas_numericas = [

        "HORAS EXTRA",

        "VALOR HORA EXTRA",

        "VALOR ÉLITE",

        "PEAJES"

    ]

    for columna in columnas_numericas:

        if columna in df_tabla.columns:

            df_tabla[columna] = (
                pd.to_numeric(
                    df_tabla[columna],
                    errors="coerce"
                )
                .fillna(0)
            )

    # ======================================================
    # CONFIGURACIÓN DE COLUMNAS
    # ======================================================

    column_config = {}

    if "FECHA" in df_tabla.columns:

        column_config["FECHA"] = st.column_config.DateColumn(
            "Fecha",
            format="DD/MM/YYYY"
        )

    if "INGRESO" in df_tabla.columns:

        column_config["INGRESO"] = st.column_config.TextColumn(
            "Ingreso"
        )

    if "SALIDA" in df_tabla.columns:

        column_config["SALIDA"] = st.column_config.TextColumn(
            "Salida"
        )

    if "HORAS EXTRA" in df_tabla.columns:

        column_config["HORAS EXTRA"] = (
            st.column_config.NumberColumn(
                "Horas Extra",
                format="%.1f"
            )
        )

    if "VALOR HORA EXTRA" in df_tabla.columns:

        column_config["VALOR HORA EXTRA"] = (
            st.column_config.NumberColumn(
                "Valor Hora Extra",
                format="$ %,.0f"
            )
        )

    if "VALOR ÉLITE" in df_tabla.columns:

        column_config["VALOR ÉLITE"] = (
            st.column_config.NumberColumn(
                "Valor Élite",
                format="$ %,.0f"
            )
        )

    if "PEAJES" in df_tabla.columns:

        column_config["PEAJES"] = (
            st.column_config.NumberColumn(
                "Peajes",
                format="$ %,.0f"
            )
        )

    # ======================================================
    # TABLA
    # ======================================================

    st.dataframe(
        df_tabla,
        use_container_width=True,
        hide_index=True,
        height=620,
        column_config=column_config
    )    
# ==========================================================
# VIÁTICOS
# ==========================================================

def mostrar_viaticos(df: pd.DataFrame):

    df = df.copy()

    st.markdown("## 🍽️ Viáticos")

    # ======================================================
    # BUSCADOR
    # ======================================================

    col_buscar, col_info = st.columns([4, 1])

    with col_buscar:

        buscar = st.text_input(
            "🔍 Digite la placa",
            placeholder="Ejemplo: TPQ282",
            key="buscar_viaticos"
        )

    # ======================================================
    # FILTRAR INFORMACIÓN
    # ======================================================

    df_tabla = df.copy()

    if buscar:

        df_tabla = df_tabla[
            df_tabla["PLACA"]
            .astype(str)
            .str.contains(
                buscar,
                case=False,
                na=False
            )
        ]

    # ======================================================
    # KPIs
    # ======================================================

    registros = len(df_tabla)

    vehiculos = (
        df_tabla["PLACA"]
        .astype(str)
        .nunique()
    )

    zonas = (
        df_tabla["ZONA"].astype(str).nunique()
        if "ZONA" in df_tabla.columns
        else 0
    )

    total_viaticos = (
        pd.to_numeric(
            df_tabla["TOTAL VIATICOS"],
            errors="coerce"
        ).fillna(0).sum()
        if "TOTAL VIATICOS" in df_tabla.columns
        else 0
    )

    with col_info:

        st.metric(
            "Registros",
            f"{registros:,}"
        )

    st.caption(
        f"Mostrando {registros:,} registros"
    )

    # ======================================================
    # TARJETAS KPI
    # ======================================================

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:

        st.metric(
            "📄 Registros",
            f"{registros:,}"
        )

    with kpi2:

        st.metric(
            "🚗 Vehículos",
            f"{vehiculos:,}"
        )

    with kpi3:

        st.metric(
            "🌎 Zonas",
            f"{zonas:,}"
        )

    with kpi4:

        st.metric(
            "💰 Total Viáticos",
            f"$ {total_viaticos:,.0f}"
        )

    st.divider()

    # ======================================================
    # ORDEN DE COLUMNAS
    # ======================================================

    columnas_principales = [

        "ZONA",

        "PLACA",

        "FECHA VIATICOS",

        "TOTAL VIATICOS"

    ]

    columnas_principales = [
        c
        for c in columnas_principales
        if c in df_tabla.columns
    ]

    columnas_restantes = [
        c
        for c in df_tabla.columns
        if c not in columnas_principales
    ]

    df_tabla = df_tabla[
        columnas_principales + columnas_restantes
    ]

    # ======================================================
    # FORMATO
    # ======================================================

    if "FECHA VIATICOS" in df_tabla.columns:

        df_tabla["FECHA VIATICOS"] = pd.to_datetime(
            df_tabla["FECHA VIATICOS"],
            errors="coerce"
        )

    if "TOTAL VIATICOS" in df_tabla.columns:

        df_tabla["TOTAL VIATICOS"] = (
            pd.to_numeric(
                df_tabla["TOTAL VIATICOS"],
                errors="coerce"
            )
            .fillna(0)
        )

    # ======================================================
    # TABLA
    # ======================================================

    st.dataframe(
        df_tabla,
        use_container_width=True,
        hide_index=True,
        height=620,
        column_config={

            "FECHA VIATICOS": st.column_config.DateColumn(
                "Fecha Viáticos",
                format="DD/MM/YYYY"
            ),

            "TOTAL VIATICOS": st.column_config.NumberColumn(
                "Total Viáticos",
                format="$ %,.0f"
            )

        }
    )    
    