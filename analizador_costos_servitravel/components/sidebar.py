from pathlib import Path

import streamlit as st


# ==========================================================
# RUTA LOGO
# ==========================================================

BASE = Path(__file__).resolve().parent.parent

LOGO = BASE / "assets" / "logo_elite.png"


# ==========================================================
# SIDEBAR
# ==========================================================

def mostrar_sidebar(hojas):

    with st.sidebar:

        # ==================================================
        # LOGO
        # ==================================================

        if LOGO.exists():

            st.image(
                str(LOGO),
                use_container_width=True
            )

        st.markdown(
            """
            <div class="sidebar-title">
                Dashboard Operativo
            </div>

            <div class="sidebar-subtitle">
                Analizador de Costos ELITE
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # ==================================================
        # HOJAS DISPONIBLES
        # ==================================================

        hojas_permitidas = [

            "RODAMIENTOS",

            "VIATICOS",

            "PARQUEADEROS",

            "PEAJES",

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
        # FUENTE DE INFORMACIÓN
        # ==================================================

        hoja = st.selectbox(

            "📂 Fuente de información",

            hojas_disponibles,

            index=0,

        )

        # ==================================================
        # ACTUALIZAR
        # ==================================================

        if st.button(

            "🔄 Actualizar datos",

            use_container_width=True,

            type="primary",

        ):

            st.cache_data.clear()

            st.rerun()

        st.divider()

        st.caption("Versión 1.0")

    # ======================================================
    # DATAFRAME
    # ======================================================

    df = hojas.get(hoja)

    if df is None or df.empty:

        st.warning("La hoja seleccionada no contiene información.")

        return None

    return {

        "hoja": hoja,

        "df": df,

    }