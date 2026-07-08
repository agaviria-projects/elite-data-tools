import streamlit as st

from analytics.comparador_meses import comparativo


# ==========================================================
# BUSCAR COLUMNA
# ==========================================================

def buscar_columna(df, candidatos):

    columnas = {c.upper(): c for c in df.columns}

    for nombre in candidatos:

        if nombre.upper() in columnas:

            return columnas[nombre.upper()]

    return None


# ==========================================================
# RESUMEN EJECUTIVO
# ==========================================================

def mostrar_resumen_ejecutivo(df):

    st.subheader("📈 Resumen Ejecutivo")

    columna_mes = buscar_columna(

        df,

        [

            "MES"

        ]

    )

    columna_valor = buscar_columna(

        df,

        [

            "VALOR ÉLITE",
            "TOTAL",
            "VALOR",
            "COSTO"

        ]

    )

    if columna_mes is None:

        st.warning("No existe la columna MES.")

        return

    if columna_valor is None:

        st.warning("No existe una columna de costos.")

        return

    resumen = comparativo(

        df,

        columna_mes,

        columna_valor

    )

    if len(resumen) < 2:

        st.info("No existen suficientes meses para comparar.")

        return

    actual = resumen.iloc[-1]

    anterior = resumen.iloc[-2]

    diferencia = actual["Costo"] - anterior["Costo"]

    porcentaje = actual["Variación %"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(

        "Mes Anterior",

        f"${anterior['Costo']:,.0f}"

    )

    c2.metric(

        "Mes Actual",

        f"${actual['Costo']:,.0f}"

    )

    c3.metric(

        "Diferencia",

        f"${diferencia:,.0f}"

    )

    c4.metric(

        "Variación",

        f"{porcentaje:.2f}%"

    )

    st.write("")

    if porcentaje > 0:

        st.error(

            f"📈 Los costos aumentaron **{porcentaje:.2f}%** respecto al mes anterior."

        )

    elif porcentaje < 0:

        st.success(

            f"📉 Los costos disminuyeron **{abs(porcentaje):.2f}%** respecto al mes anterior."

        )

    else:

        st.info(

            "Los costos permanecieron estables respecto al mes anterior."

        )