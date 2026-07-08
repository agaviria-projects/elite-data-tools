import streamlit as st


# ==========================================================
# DATAFRAME GLOBAL
# ==========================================================

def guardar_dataframe(df):

    st.session_state["df_costos"] = df


# ==========================================================
# OBTENER DATAFRAME
# ==========================================================

def obtener_dataframe():

    return st.session_state.get(
        "df_costos",
        None
    )


# ==========================================================
# EXISTE DATAFRAME
# ==========================================================

def existe_dataframe():

    return "df_costos" in st.session_state


# ==========================================================
# LIMPIAR DATAFRAME
# ==========================================================

def limpiar_dataframe():

    if "df_costos" in st.session_state:

        del st.session_state["df_costos"]