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

        if "PARQUEADEROS" not in hojas:

            st.warning("No existe la hoja PARQUEADEROS.")

        else:

            mostrar_parqueaderos(
                hojas["PARQUEADEROS"]
            )

    # ======================================================
    # PEAJES
    # ======================================================

    with tab4:

        if "PEAJES" not in hojas:

            st.warning("No existe la hoja PEAJES.")

        else:

            mostrar_peajes(
                hojas["PEAJES"]
            )


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
# ==========================================================
# PARQUEADEROS
# ==========================================================

def mostrar_parqueaderos(df: pd.DataFrame):

    df = df.copy()

    st.markdown("## 🅿️ Parqueaderos")

    # ======================================================
    # BUSCADOR
    # ======================================================

    col_buscar, col_info = st.columns([4, 1])

    with col_buscar:

        buscar = st.text_input(
            "🔍 Digite la placa",
            placeholder="Ejemplo: TPQ282",
            key="buscar_parqueaderos"
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
        if "PLACA" in df_tabla.columns
        else 0
    )

    cantidad = (
        pd.to_numeric(
            df_tabla["CANTIDAD"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
        if "CANTIDAD" in df_tabla.columns
        else 0
    )

    total_parqueaderos = (
        pd.to_numeric(
            df_tabla["TOTAL PARQUEADEROS"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
        if "TOTAL PARQUEADEROS" in df_tabla.columns
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
            "🅿️ Cantidad",
            f"{cantidad:,.0f}"
        )

    with kpi4:

        st.metric(
            "💰 Total Parqueaderos",
            f"$ {total_parqueaderos:,.0f}"
        )

    st.divider()

    # ======================================================
    # ORDEN DE COLUMNAS
    # ======================================================

    columnas_principales = [

        "ZONA",

        "FECHA",

        "PLACA",

        "CANTIDAD",

        "TOTAL PARQUEADEROS"

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

    if "FECHA" in df_tabla.columns:

        df_tabla["FECHA"] = pd.to_datetime(
            df_tabla["FECHA"],
            errors="coerce"
        )

    if "CANTIDAD" in df_tabla.columns:

        df_tabla["CANTIDAD"] = (
            pd.to_numeric(
                df_tabla["CANTIDAD"],
                errors="coerce"
            )
            .fillna(0)
        )

    if "TOTAL PARQUEADEROS" in df_tabla.columns:

        df_tabla["TOTAL PARQUEADEROS"] = (
            pd.to_numeric(
                df_tabla["TOTAL PARQUEADEROS"],
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

            "FECHA": st.column_config.DateColumn(
                "Fecha",
                format="DD/MM/YYYY"
            ),

            "CANTIDAD": st.column_config.NumberColumn(
                "Cantidad",
                format="%.0f"
            ),

            "TOTAL PARQUEADEROS": st.column_config.NumberColumn(
                "Total Parqueaderos",
                format="$ %,.0f"
            )

        }
    )    
# ==========================================================
# PEAJES
# ==========================================================

def mostrar_peajes(df: pd.DataFrame):

    df = df.copy()

    st.markdown("## 🛣️ Peajes")

    # ======================================================
    # BUSCADOR
    # ======================================================

    col_buscar, col_info = st.columns([4, 1])

    with col_buscar:

        buscar = st.text_input(
            "🔍 Digite la placa",
            placeholder="Ejemplo: TPQ282",
            key="buscar_peajes"
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
        if "PLACA" in df_tabla.columns
        else 0
    )

    cantidad_peajes = (
        pd.to_numeric(
            df_tabla["CANTIDAD PEAJES"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
        if "CANTIDAD PEAJES" in df_tabla.columns
        else 0
    )

    total_peajes = (
        pd.to_numeric(
            df_tabla["TOTAL PEAJES"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
        if "TOTAL PEAJES" in df_tabla.columns
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
            "🛣️ Cantidad Peajes",
            f"{cantidad_peajes:,.0f}"
        )

    with kpi4:

        st.metric(
            "💰 Total Peajes",
            f"$ {total_peajes:,.0f}"
        )

    st.divider()

    # ======================================================
    # ORDEN DE COLUMNAS
    # ======================================================

    columnas_principales = [

        "ZONA",

        "FECHA EN LA QUE SE CAUSA EL PEAJE",

        "PLACA",

        "CORTE EN EL QUE SE FACTURA",

        "MES EN EL QUE SE FACTURA",

        "CANTIDAD PEAJES",

        "VALOR PEAJE",

        "TOTAL PEAJES"

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

    if "FECHA EN LA QUE SE CAUSA EL PEAJE" in df_tabla.columns:

        df_tabla["FECHA EN LA QUE SE CAUSA EL PEAJE"] = pd.to_datetime(
            df_tabla["FECHA EN LA QUE SE CAUSA EL PEAJE"],
            errors="coerce"
        )

    for columna in [

        "CANTIDAD PEAJES",

        "VALOR PEAJE",

        "TOTAL PEAJES"

    ]:

        if columna in df_tabla.columns:

            df_tabla[columna] = (
                pd.to_numeric(
                    df_tabla[columna],
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

            "FECHA EN LA QUE SE CAUSA EL PEAJE": st.column_config.DateColumn(
                "Fecha Peaje",
                format="DD/MM/YYYY"
            ),

            "CANTIDAD PEAJES": st.column_config.NumberColumn(
                "Cantidad Peajes",
                format="%.0f"
            ),

            "VALOR PEAJE": st.column_config.NumberColumn(
                "Valor Peaje",
                format="$ %,.0f"
            ),

            "TOTAL PEAJES": st.column_config.NumberColumn(
                "Total Peajes",
                format="$ %,.0f"
            )

        }
    )    