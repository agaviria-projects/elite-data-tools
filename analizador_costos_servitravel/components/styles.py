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

    color:#1F2937;

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

    font-weight:700 !important;

    color:#1E3A8A !important;

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
/*=====================================================
TABLAS DATAFRAME
=====================================================*/

[data-testid="stDataFrame"] table {

    font-size: 15px !important;

}

[data-testid="stDataFrame"] th {

    font-size: 14px !important;

    font-weight: 700 !important;

    color: #111827 !important;

    background: #F3F4F6 !important;

}

[data-testid="stDataFrame"] td {

    font-size: 14px !important;

    font-weight: 500 !important;

    color: #1F2937 !important;

}

[data-testid="stDataFrame"] tbody tr:hover {

    background-color: #EEF5FF !important;

}

/*=====================================================
TABS PRINCIPALES
=====================================================*/

/* Texto de las pestañas */

button[data-baseweb="tab"]{

    color:#1F2937 !important;

    font-size:15px !important;

    font-weight:600 !important;

}

/* Pestaña activa */

button[data-baseweb="tab"][aria-selected="true"]{

    color:#0F62FE !important;

    font-weight:700 !important;

    border-bottom:3px solid #0F62FE !important;

}

/* Hover */

button[data-baseweb="tab"]:hover{

    color:#2563EB !important;

}
/* ===================================================== */
/* HEADER ELITE */
/* ===================================================== */

.elite-banner{

    display:flex;
    justify-content:space-between;
    align-items:center;

    background:linear-gradient(
        135deg,
        #0b5f2a 0%,
        #14833d 55%,
        #1fa34a 100%
    );

    border-radius:18px;

    padding:28px 34px;

    margin-bottom:18px;

    color:white;

    box-shadow:0 8px 22px rgba(0,0,0,.18);
}

.elite-left{

    display:flex;
    flex-direction:column;
}

.elite-title{

    font-size:34px;

    font-weight:700;

    line-height:1.1;
}

.elite-subtitle{

    margin-top:8px;

    font-size:16px;

    color:rgba(255,255,255,.90);
}

.elite-right{

    text-align:right;
}

.elite-date-title{

    font-size:15px;

    color:rgba(255,255,255,.85);
}

.elite-date{

    margin-top:6px;

    font-size:24px;

    font-weight:700;
}
</style>
        """,
        unsafe_allow_html=True
    )