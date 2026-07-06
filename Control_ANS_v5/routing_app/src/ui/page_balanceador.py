import streamlit as st

def mostrar_balanceador():
    st.markdown('<div class="section-title">⚖️ Balanceador de Carga Operativa</div>', unsafe_allow_html=True)

    st.markdown("""
    Este módulo permite redistribuir de forma inteligente los pedidos críticos
    (📌 VENCIDOS y ⏰ ALERTA 0) para balancear la carga entre cuadrillas y evitar riesgos de penalización.
    """, unsafe_allow_html=False)

    st.info("🚧 Módulo en construcción. Próximamente podrás simular movimientos entre cuadrillas con KPIs de impacto.")