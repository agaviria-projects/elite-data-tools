import streamlit as st


# ==========================================================
# ESTILOS GLOBALES
# ==========================================================

def aplicar_estilos():

    st.markdown(
        """
<style>

/*==========================================================
OCULTAR STREAMLIT
==========================================================*/

#MainMenu,
header,
footer{
    visibility:hidden;
}

/*==========================================================
CONTENEDOR
==========================================================*/

.block-container{

    max-width:1600px;

    padding-top:20px;

    padding-left:35px;

    padding-right:35px;

    padding-bottom:30px;

}

/*==========================================================
FUENTE
==========================================================*/

html,
body,
[class*="css"]{

    font-family:"Segoe UI",sans-serif;

}

/*==========================================================
TÍTULOS
==========================================================*/

h1{

    font-size:40px !important;

    font-weight:700 !important;

}

h2{

    font-size:30px !important;

    font-weight:700 !important;

}

h3{

    font-size:24px !important;

    font-weight:600 !important;

}

/*==========================================================
SIDEBAR
==========================================================*/

section[data-testid="stSidebar"]{

    background:#F7F9FC;

    border-right:1px solid #E5E7EB;

}

/*==========================================================
SELECTBOX
==========================================================*/

div[data-baseweb="select"]{

    font-size:15px;

}

/*==========================================================
KPIs
==========================================================*/

div[data-testid="stMetric"]{

    background:white;

    border-radius:14px;

    border:1px solid #E4E8F0;

    padding:16px;

    box-shadow:0 3px 10px rgba(0,0,0,.05);

}

/* título KPI */

div[data-testid="stMetricLabel"]{

    font-size:15px;

    font-weight:600;

}

/* valor KPI */

div[data-testid="stMetricValue"]{

    font-size:38px;

    font-weight:700;

    color:#1E3A8A;

}

/*==========================================================
BOTONES
==========================================================*/

.stButton>button{

    width:100%;

    height:42px;

    border-radius:10px;

    font-weight:600;

}

/*==========================================================
TABLAS
==========================================================*/

div[data-testid="stDataFrame"]{

    border-radius:12px;

    overflow:hidden;

    border:1px solid #E5E7EB;

}

/*==========================================================
DATA EDITOR
==========================================================*/

div[data-testid="stDataFrame"] table{

    font-size:15px;

}

/* cabecera */

thead tr th{

    background:#F3F4F6 !important;

    font-weight:700 !important;

    font-size:15px !important;

}

/* filas */

tbody tr td{

    font-size:15px !important;

}

/*==========================================================
DIVIDER
==========================================================*/

hr{

    margin-top:25px;

    margin-bottom:25px;

}

/*==========================================================
RESPONSIVE
==========================================================*/

@media (max-width:900px){

.block-container{

padding-left:15px;

padding-right:15px;

}

}

</style>
        """,
        unsafe_allow_html=True
    )