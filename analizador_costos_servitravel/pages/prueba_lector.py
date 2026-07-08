import streamlit as st

from data.lector_excel import (
    obtener_hojas,
    leer_hoja,
    obtener_ruta
)

st.title("Prueba lector Excel")

st.write(obtener_ruta())

try:

    hojas = obtener_hojas()

    st.success(f"Se encontraron {len(hojas)} hojas.")

    hoja = st.selectbox(
        "Seleccione una hoja",
        hojas
    )

    df = leer_hoja(hoja)

    st.write(df.shape)

    st.dataframe(df.head())

except Exception as e:

    st.error(e)