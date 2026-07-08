import streamlit as st
from datetime import datetime


# ==========================================================
# HEADER
# ==========================================================

def mostrar_header():

    fecha = datetime.now().strftime("%d/%m/%Y")

    contenedor = st.container(border=True)

    with contenedor:

        col1, col2 = st.columns([8, 2])

        with col1:

            st.title("📊 Analizador de Costos Operativos")

            st.caption("Dashboard Ejecutivo · Servitravel")

        with col2:

            st.write("")
            st.write("")

            st.markdown(
                f"""
**📅 Fecha**

{fecha}
"""
            )