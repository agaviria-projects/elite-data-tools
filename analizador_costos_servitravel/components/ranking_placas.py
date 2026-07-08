import streamlit as st
import pandas as pd


# ==========================================================
# RANKING PLACAS
# ==========================================================

def mostrar_ranking_placas(df: pd.DataFrame):

    st.subheader("🏆 Placas con más servicios")

    if df is None or df.empty:

        st.info("No existen registros.")

        return

    if "PLACA" not in df.columns:

        st.warning("No existe la columna PLACA.")

        return

    # ======================================================
    # AGRUPAR
    # ======================================================

    ranking = (

        df.groupby("PLACA")
        .size()
        .reset_index(name="Cantidad")
        .sort_values(
            "Cantidad",
            ascending=False
        )

    )

    if ranking.empty:

        st.info("Sin información.")

        return

    maximo = ranking["Cantidad"].max()

    # ======================================================
    # TARJETA
    # ======================================================

    with st.container(border=True):

        c1, c2 = st.columns([3,1])

        c1.markdown("#### 🚗 Ranking de Vehículos")

        c2.metric(
            "Total Servicios",
            int(ranking["Cantidad"].sum())
        )

        st.divider()

        # Mostrar Top 15

        for _, fila in ranking.head(15).iterrows():

            placa = fila["PLACA"]

            cantidad = int(fila["Cantidad"])

            porcentaje = cantidad / maximo

            col1, col2 = st.columns([2,6])

            with col1:

                st.markdown(
                    f"**{placa}**"
                )

            with col2:

                st.progress(
                    porcentaje,
                    text=f"{cantidad} servicios"
                )

    if len(ranking) > 15:

        with st.expander("Ver ranking completo"):

            st.dataframe(

                ranking,

                use_container_width=True,

                hide_index=True

            )