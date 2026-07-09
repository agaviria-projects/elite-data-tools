import streamlit as st
from datetime import datetime


# ==========================================================
# HEADER
# ==========================================================

def mostrar_header():

    fecha = datetime.now().strftime("%d/%m/%Y")

    st.markdown(
    f"""
    <div class="elite-banner">

    <div class="elite-left">

    <div class="elite-title">
    📊 Analizador de Costos Operativos
    </div>

    <div class="elite-subtitle">
    Sistema de Análisis Operativo · ELITE
    </div>

    </div>

    <div class="elite-right">

    <div class="elite-date-title">
    📅 Fecha
    </div>

    <div class="elite-date">
    {fecha}
    </div>

    </div>

    </div>
    """,
        unsafe_allow_html=True,
    )