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
        # ARCHIVO FUENTE
        # ==================================================

        st.markdown("**📄 Archivo fuente**")

        st.info(
            """
**INFORME_LIQUIDACION.xlsb**

🟢 Conectado
"""
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
    # COMPATIBILIDAD
    # ======================================================

    hoja = "RODAMIENTOS"

    df = hojas.get(hoja)

    return {

        "hoja": hoja,

        "df": df,

    }