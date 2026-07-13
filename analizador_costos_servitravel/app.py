import streamlit as st

from data.lector_excel import leer_todas

from components.styles import cargar_estilos
from components.banner import mostrar_banner
from components.sidebar import mostrar_sidebar
from components.filtros import mostrar_filtros
from components.kpis import mostrar_kpis
from components.ranking_placas import mostrar_ranking_placas
from components.indicadores_mensuales import mostrar_indicadores_mensuales
from components.datos import mostrar_datos

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
    page_title="Analizador de Costos Operativos Servitravel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# ESTILOS
# ==========================================================

cargar_estilos()

# ==========================================================
# HEADER
# ==========================================================

mostrar_banner()

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
# NAVEGACIÓN
# ==========================================================

opcion = st.radio(
    "",
    [
        "📂 Datos",
        "📊 Resumen del período",
        "📈 Indicadores Mensuales",
        "🚗 Vehículos",
        "💰 Gastos Operativos",
        "🗺️ Zonas",
        "📋 Detalle",
    ],
    horizontal=True,
    label_visibility="collapsed"
)
# ==========================================================
# DATOS
# ==========================================================

if opcion == "📂 Datos":

     mostrar_datos(hojas)

# ==========================================================
# RESUMEN EJECUTIVO
# ==========================================================
if opcion == "📊 Resumen del período":

    df_filtrado = mostrar_filtros(
        df,
        key_prefix="resumen"
    )

    if df_filtrado.empty:

        st.warning("No existen registros para los filtros seleccionados.")

    else:

        mostrar_kpis(df_filtrado)

        st.divider()

        mostrar_ranking_placas(df_filtrado)

# ==========================================================
# INDICADORES MENSUALES
# ==========================================================

if opcion == "📈 Indicadores Mensuales":

    df_filtrado = mostrar_filtros(
        df,
        key_prefix="indicadores"
    )

    if df_filtrado.empty:

        st.warning("No existen registros para los filtros seleccionados.")

    else:

        mostrar_indicadores_mensuales(
            df,
            df_filtrado
        )
   

# ==========================================================
# VEHÍCULOS
# ==========================================================

if opcion == "🚗 Vehículos":

    st.info("Módulo en construcción.")

# ==========================================================
# GASTOS OPERATIVOS
# ==========================================================

if opcion == "💰 Gastos Operativos":

    st.info("Módulo en construcción.")

# ==========================================================
# ZONAS
# ==========================================================

if opcion == "🗺️ Zonas":

    st.info("Módulo en construcción.")

# ==========================================================
# DETALLE
# ==========================================================

if opcion == "📋 Detalle":

    st.info("Módulo en construcción.")