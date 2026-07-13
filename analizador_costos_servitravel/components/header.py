import streamlit as st

def mostrar_header():

    st.markdown(
        """
<div style="
background:#1F7A3E;
padding:30px;
border-radius:20px;
color:white;
font-size:32px;
font-weight:bold;
">

Analizador de Costos Operativos

</div>
        """,
        unsafe_allow_html=True,
    )