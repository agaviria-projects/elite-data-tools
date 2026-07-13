import streamlit as st
from pathlib import Path

def cargar_estilos():

    css = (
        Path(__file__).parent.parent
        / "assets"
        / "styles.css"
    )

    with open(css, encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )