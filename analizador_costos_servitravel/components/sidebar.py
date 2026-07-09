import streamlit as st


# ==========================================================
# SIDEBAR
# ==========================================================

def mostrar_sidebar(hojas):

    with st.sidebar:

        st.markdown("## 📂 Fuente de Información")

        st.caption(
            "Seleccione la hoja del consolidado para iniciar el análisis."
        )

        st.divider()

        # ==================================================
        # HOJAS DISPONIBLES
        # ==================================================

        hojas_permitidas = [

            "RODAMIENTOS",

            "VIATICOS",

            "PARQUEADEROS",

            "PEAJES"

        ]

        hojas_disponibles = [

            hoja

            for hoja in hojas.keys()

            if hoja.strip().upper() in hojas_permitidas

        ]

        if not hojas_disponibles:

            st.error("No se encontraron hojas válidas.")

            return None

        # ==================================================
        # SELECCIÓN
        # ==================================================

        hoja = st.selectbox(

            "Hoja disponible",

            hojas_disponibles,

            index=0

        )

        # ==================================================
        # ACTUALIZAR
        # ==================================================

        if st.button(

            "🔄 Actualizar Dashboard",

            use_container_width=True,

            type="primary"

        ):

            st.cache_data.clear()

            st.rerun()

        st.divider()

        # ==================================================
        # INFORMACIÓN
        # ==================================================

        st.markdown("### ℹ️ Información")

        st.info(
            """
**Archivo**

INFORME_LIQUIDACION.xlsb

**Estado**

Conectado correctamente
            """
        )

        st.success(f"📄 Hoja activa: **{hoja}**")

        st.divider()

        # ==================================================
        # MÓDULOS
        # ==================================================

        st.markdown("### 📊 Módulos")

        st.caption("✔ KPIs")

        st.caption("✔ Resumen Ejecutivo")

        st.caption("⏳ Comparativo Mensual")

        st.caption("⏳ Ranking de Zonas")

        st.caption("⏳ Ranking de Conceptos")

        st.caption("⏳ Gráficos")

        st.caption("⏳ Hallazgos")

        st.caption("⏳ Exportación")

        st.divider()

        st.caption("Analizador de Costos Operativos")

        st.caption("Versión 1.0")

    # ======================================================
    # DATAFRAME SELECCIONADO
    # ======================================================

    df = hojas.get(hoja)

    if df is None or df.empty:

        st.warning("La hoja seleccionada no contiene información.")

        return None

    return {

        "hoja": hoja,

        "df": df

    }