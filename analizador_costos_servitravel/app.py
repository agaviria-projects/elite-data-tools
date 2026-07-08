import streamlit as st

from data.lector_excel import leer_todas

from components.styles import aplicar_estilos
from components.header import mostrar_header
from components.sidebar import mostrar_sidebar
from components.filtros import mostrar_filtros
from components.kpis import mostrar_kpis
from components.resumen_ejecutivo import mostrar_resumen_ejecutivo
from components.ranking_placas import mostrar_ranking_placas

# Próximas fases
# from components.comparativo import mostrar_comparativo
# from components.ranking_zonas import mostrar_ranking_zonas
# from components.ranking_conceptos import mostrar_ranking_conceptos
# from components.graficos import mostrar_graficos
# from components.hallazgos import mostrar_hallazgos
# from components.detalle import mostrar_detalle


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

st.set_page_config(
    page_title="Analizador de Costos Operativos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# ESTILOS
# ==========================================================

aplicar_estilos()

# ==========================================================
# HEADER
# ==========================================================

mostrar_header()

# ==========================================================
# CARGAR INFORMACIÓN (UNA SOLA VEZ)
# ==========================================================

hojas = leer_todas()

# ==========================================================
# SIDEBAR
# ==========================================================

resultado = mostrar_sidebar(hojas)

if resultado is None:
    st.stop()

df = resultado["df"]
hoja = resultado["hoja"]

# ==========================================================
# FILTROS
# ==========================================================

df_filtrado = mostrar_filtros(df)

if df_filtrado is None or df_filtrado.empty:

    st.warning("No existen registros para los filtros seleccionados.")

    st.stop()

# ==========================================================
# KPIs
# ==========================================================

mostrar_kpis(df_filtrado)

st.divider()


mostrar_ranking_placas(df_filtrado)

st.divider()

# ==========================================================
# RESUMEN EJECUTIVO
# ==========================================================

mostrar_resumen_ejecutivo(df_filtrado)

st.divider()

# ==========================================================
# PRÓXIMAS FASES
# ==========================================================

# mostrar_comparativo(df_filtrado)

# st.divider()

# mostrar_ranking_zonas(df_filtrado)

# st.divider()

# mostrar_ranking_conceptos(df_filtrado)

# st.divider()

# mostrar_graficos(df_filtrado)

# st.divider()

# mostrar_hallazgos(df_filtrado)

# st.divider()

# mostrar_detalle(df_filtrado)