import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import base64

from src.io_excel import cargar_excel, separar_invalidos_latlng
from src.filters import aplicar_filtros
from src.constants import CONCEPTOS_RUTEO
from src.clustering import asignar_cuadrillas_kmeans
from src.routing import generar_rutas_por_cuadrilla, url_google_maps_cuadrilla
from src.map_view import construir_mapa_rutas
from src.export import exportar_rutas_excel_bytes
from src.geo import sugerir_origen_por_df, obtener_direccion_por_latlng, clasificar_zona_geo
from src.routing import urls_google_maps_cuadrilla_tramos
from pathlib import Path
from src.logger_auditoria import registrar_evento
from src.cc_ans_ui import render_centro_control_ans
from src.cc_ans_metrics import construir_seguimiento_plan, resumir_seguimiento

from datetime import datetime
import pytz


DEBUG_UI = False

st.set_page_config(
    page_title="Enrutamiento por Cuadrillas",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "ingreso_registrado" not in st.session_state:
    registrar_evento("ingreso_app", "Atlas 360 iniciado")
    st.session_state["ingreso_registrado"] = True

# Listener global: recibe el click del icono y activa open_manual=1
components.html("""
<script>
window.addEventListener("message", (event) => {
if (event.data && event.data.type === "OPEN_MANUAL") {
    const url = new URL(window.location.href);
    url.searchParams.set("open_manual", "1");
    window.location.href = url.toString();
}
});
</script>
""", height=0)

def inyectar_css_ui():
    st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background: #F6F7FB;
    }

    /* Barra superior de color (elegante) */
    .kpi-card::before{
        content:"";
        position:absolute;
        top:0; left:0; right:0;
        height: 6px;
        background: var(--kpi);
    }

    .kpi-title{
        font-size: 12px;
        font-weight: 600;
        color: rgba(16,24,40,0.72);
        margin: 6px 0 4px 0;
        letter-spacing: .2px;
    }

    .kpi-value{
        font-size: 30px;
        font-weight: 800;
        color: #101828;
        line-height: 1.05;
    }

    .kpi-sub{
        font-size: 12px;
        color: rgba(16,24,40,0.55);
        margin-top: 6px;
    }

    /* Responsive: cuando la pantalla es angosta */
    @media (max-width: 1100px){
        .kpi-grid{ grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
    @media (max-width: 640px){
        .kpi-grid{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    </style>
    """, unsafe_allow_html=True)


inyectar_css_ui()


@st.cache_data(show_spinner=False)
def _preparar_df(file_bytes: bytes):
    df = cargar_excel(file_bytes)
    df_ok, df_bad = separar_invalidos_latlng(df)
    df_ok = df_ok.copy()
    if "zona_geo" not in df_ok.columns:
        cache = {}

        def _z(lat, lng):
            try:
                k = (round(float(lat), 5), round(float(lng), 5))
            except Exception:
                k = (lat, lng)
            if k not in cache:
                cache[k] = clasificar_zona_geo(lat, lng)
            return cache[k]

        df_ok["zona_geo"] = [_z(a, b) for a, b in zip(df_ok["lat"], df_ok["lng"])]
    return df, df_ok, df_bad


def _kpi_estado_counts(df_in: pd.DataFrame) -> dict:
    total = len(df_in)

    if "estado" in df_in.columns:
        vc = df_in["estado"].fillna("").astype(str).str.strip().str.upper().value_counts().to_dict()
    else:
        vc = {}

    vencidos = vc.get("VENCIDO", 0)
    alerta = vc.get("ALERTA", 0)

    alerta0 = 0
    for k in ("ALERTA_0", "ALERTA_0 DIAS", "ALERTA 0 DIAS", "ALERTA_0 DÍAS", "ALERTA 0 DÍAS"):
        alerta0 += vc.get(k, 0)

    atiempo = vc.get("A TIEMPO", 0) + vc.get("ATIEMPO", 0)

    sin_fecha = 0
    col_fecha = (
        "FECHA_LIMITE_ANS" if "FECHA_LIMITE_ANS" in df_in.columns
        else ("fecha_limite_ans" if "fecha_limite_ans" in df_in.columns else None)
    )
    if col_fecha:
        sin_fecha = pd.to_datetime(df_in[col_fecha], errors="coerce").isna().sum()

    return {
        "Total": int(total),
        "Vencidos": int(vencidos),
        "Alerta_0 Días": int(alerta0),
        "Alerta": int(alerta),
        "A Tiempo": int(atiempo),
        "Sin Fecha": int(sin_fecha),
    }


def render_kpis(k: dict):
    colores = {
        "Total": "#667085",
        "Vencidos": "#D92D20",
        "Alerta_0 Días": "#F79009",
        "Alerta": "#EAAA08",
        "A Tiempo": "#12B76A",
        "Sin Fecha": "#2E90FA",
    }

    subt = {
        "Total": "Total pedidos",
        "Vencidos": "Atención inmediata",
        "Alerta_0 Días": "Prioridad hoy",
        "Alerta": "Riesgo cercano",
        "A Tiempo": "Dentro del ANS",
        "Sin Fecha": "Requiere revisión",
    }

    orden = ["Total", "Vencidos", "Alerta_0 Días", "Alerta", "A Tiempo", "Sin Fecha"]

    html = '<div class="kpi-grid">'

    for label in orden:
        val = int(k.get(label, 0) or 0)
        color = colores[label]

        html += (
            f'<div class="kpi-card">'
            f'  <div class="kpi-topbar" style="background:{color};"></div>'
            f'  <div class="kpi-head">'
            f'    <div class="kpi-title">{label}</div>'
            f'  </div>'
            f'  <div class="kpi-value">{val:,}</div>'
            f'  <div class="kpi-sub">{subt[label]}</div>'
            f'</div>'
        )

    html += '</div>'

    st.markdown(html, unsafe_allow_html=True)


def _dedupe_por_pedido(df_in: pd.DataFrame) -> pd.DataFrame:
    """
    Garantiza que un PEDIDO aparezca UNA sola vez.
    Regla: se queda con la fila "más urgente" (VENCIDO > ALERTA_0 > ALERTA > A TIEMPO > SIN FECHA),
    y si empatan, por fecha_limite más cercana.
    """
    if df_in is None or df_in.empty:
        return df_in

    col_pedido = "PEDIDO" if "PEDIDO" in df_in.columns else ("pedido" if "pedido" in df_in.columns else None)
    if not col_pedido:
        return df_in

    df = df_in.copy()

    # Canon estado
    if "estado" in df.columns:
        est = df["estado"].fillna("").astype(str).str.strip().str.upper()
    else:
        est = pd.Series([""] * len(df), index=df.index)

    # Prioridad (menor = más urgente)
    prio = pd.Series(99, index=df.index)
    prio[est.eq("VENCIDO")] = 1
    prio[est.isin(["ALERTA_0", "ALERTA_0 DIAS", "ALERTA 0 DIAS", "ALERTA_0 DÍAS", "ALERTA 0 DÍAS"])] = 2
    prio[est.eq("ALERTA")] = 3
    prio[est.isin(["A TIEMPO", "ATIEMPO"])] = 4
    df["_prio"] = prio

    # Fecha límite (para desempate)
    col_fecha = "FECHA_LIMITE_ANS" if "FECHA_LIMITE_ANS" in df.columns else (
        "fecha_limite_ans" if "fecha_limite_ans" in df.columns else None
    )
    if col_fecha:
        df["_fecha_lim"] = pd.to_datetime(df[col_fecha], errors="coerce")
    else:
        df["_fecha_lim"] = pd.NaT

    # Ordena: más urgente + fecha más cercana primero
    df = df.sort_values(by=["_prio", "_fecha_lim"], ascending=[True, True], na_position="last")

    # Drop duplicados por pedido (se queda con la mejor fila)
    df = df.drop_duplicates(subset=[col_pedido], keep="first")

    # Limpieza
    df = df.drop(columns=["_prio", "_fecha_lim"], errors="ignore")

    return df


# =========================
# ✅ NUEVO: helpers para filtros extra (REPORTE_TECNICO / MARCA_TEMPORAL) y columnas
# =========================
def _pick_col(df_: pd.DataFrame, candidates: list[str]) -> str | None:
    if df_ is None or df_.empty:
        return None
    cols = list(df_.columns)
    up_map = {str(c).strip().upper(): c for c in cols}
    for cand in candidates:
        k = str(cand).strip().upper()
        if k in up_map:
            return up_map[k]
    return None


def _norm_txt(s) -> str:
    if pd.isna(s):
        return ""
    return str(s).strip()


def _aplicar_filtro_reporte(df_in: pd.DataFrame, reporte_sel: list[str]) -> pd.DataFrame:
    if df_in is None or df_in.empty:
        return df_in
    if not reporte_sel:
        return df_in

    col_rep = _pick_col(df_in, ["REPORTE_TECNICO", "reporte_tecnico"])
    if not col_rep:
        return df_in

    rep_norm = df_in[col_rep].fillna("").astype(str).str.strip()
    # Match exact values seleccionados (seguro y predecible)
    return df_in[rep_norm.isin(reporte_sel)].copy()


def _aplicar_excluir_ejecutados_marca(df_in: pd.DataFrame, excluir: bool) -> pd.DataFrame:
    if df_in is None or df_in.empty or not excluir:
        return df_in

    col_mt = _pick_col(df_in, ["MARCA_TEMPORAL", "marca_temporal", "MARCA TEMPORAL"])
    if not col_mt:
        return df_in

    # Si marca_temporal tiene valor => ya ejecutado => excluir
    mt = df_in[col_mt]
    mt_txt = mt.fillna("").astype(str).str.strip()
    mask_no_ejecutado = mt_txt.eq("")
    return df_in[mask_no_ejecutado].copy()


USAR_REGLA_REPORTE_TECNICO = True


def _canon_rt_text(v) -> str:
    """
    Normaliza texto para comparar nombres de columnas y valores:
    - mayúsculas
    - quita tildes comunes
    - reemplaza _ por espacio
    - colapsa espacios
    """
    if pd.isna(v):
        return ""

    s = str(v).strip().upper()

    reemplazos = str.maketrans({
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "Ü": "U",
        "_": " ",
    })
    s = s.translate(reemplazos)
    s = " ".join(s.split())
    return s


def _unique_vals_rt(df_in: pd.DataFrame, col: str) -> list[str]:
    if col not in df_in.columns:
        return []
    return (
        df_in[col]
        .fillna("")
        .astype(str)
        .map(_canon_rt_text)
        .unique()
        .tolist()
    )


def _pick_col_reporte_operativo(df_in: pd.DataFrame) -> str | None:
    """
    Prioriza la columna de detalle real del reporte técnico,
    evitando columnas de bandera/cruce.
    """
    if df_in is None or df_in.empty:
        return None

    cols = list(df_in.columns)
    canon_map = {_canon_rt_text(c): c for c in cols}

    exactos_operativos = [
        "REPORTE TECNICO",
    ]

    valores_flag = {"", "SI", "SÍ", "NO", "0", "1"}

    # 1) Prioridad máxima: REPORTE TECNICO exacto si NO es una bandera pura
    for cand in exactos_operativos:
        if cand in canon_map:
            col = canon_map[cand]
            vals = set(_unique_vals_rt(df_in, col))

            if not vals.issubset(valores_flag):
                return col

    # 2) Buscar columnas relacionadas evitando auxiliares de cruce/bandera
    for c in cols:
        up = _canon_rt_text(c)

        if "REPORTE" in up and "TECN" in up:
            if any(tok in up for tok in ["FLAG", "BANDERA", "CRUCE", "VALIDA", "VALIDACION", "EXCLUIR"]):
                continue

            vals = set(_unique_vals_rt(df_in, c))

            if not vals.issubset(valores_flag):
                return c

    return None


def _pick_col_flag_reporte(df_in: pd.DataFrame) -> str | None:
    """
    Busca una columna tipo bandera de cruce: SI/NO, 1/0.
    Primero intenta columnas cuyo nombre sugiera claramente bandera/cruce.
    """
    if df_in is None or df_in.empty:
        return None

    cols = list(df_in.columns)
    valores_flag = {"", "SI", "SÍ", "NO", "0", "1"}

    # 1) Priorizar columnas cuyo nombre sí parece bandera/cruce
    for c in cols:
        up = _canon_rt_text(c)

        if "REPORTE" in up and "TECN" in up:
            if any(tok in up for tok in ["FLAG", "BANDERA", "CRUCE", "VALIDA", "VALIDACION", "EXCLUIR"]):
                vals = set(_unique_vals_rt(df_in, c))
                if vals and vals.issubset(valores_flag):
                    return c

    # 2) Fallback: cualquier columna REPORTE+TECN que sea bandera pura
    for c in cols:
        up = _canon_rt_text(c)

        if "REPORTE" in up and "TECN" in up:
            vals = set(_unique_vals_rt(df_in, c))
            if vals and vals.issubset(valores_flag):
                return c

    return None


def _normalizar_reporte_tecnico(df_in: pd.DataFrame) -> pd.Series:
    col_rep = _pick_col_reporte_operativo(df_in)

    if not col_rep:
        return pd.Series(["SIN DATOS"] * len(df_in), index=df_in.index)

    s = (
        df_in[col_rep]
        .fillna("")
        .astype(str)
        .map(_canon_rt_text)
    )

    s = s.replace({
        "": "SIN DATOS",
        "NAN": "SIN DATOS",
        "NONE": "SIN DATOS",
        "NULL": "SIN DATOS",
        "SIN DATO": "SIN DATOS",
        "NO REPORTA": "NO REPORTADO",
        "NO REPORTADO ": "NO REPORTADO",
        "NO APLICA ": "NO APLICA",
        "N A": "NO APLICA",
        "N/A": "NO APLICA",
    })

    return s


def _split_operativo_vs_excluidos(df_in: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Regla robusta:
    1) Si existe bandera SI/NO, usarla.
       - programable: NO, 0, vacío
       - excluido: SI, SÍ, 1
    2) Si no existe bandera, usar columna de detalle operativo.
       - programable: SIN DATOS, vacío, NO REPORTADO, PENDIENTE, NO APLICA
       - excluido: cualquier detalle real de gestión
    """
    if df_in is None or df_in.empty:
        return df_in.copy(), df_in.iloc[0:0].copy()

    if not USAR_REGLA_REPORTE_TECNICO:
        return df_in.copy(), df_in.iloc[0:0].copy()

    col_flag = _pick_col_flag_reporte(df_in)

    if col_flag:
        flag = (
            df_in[col_flag]
            .fillna("")
            .astype(str)
            .map(_canon_rt_text)
        )

        mask_programable = flag.isin(["", "NO", "0"])
        df_programable = df_in[mask_programable].copy()
        df_excluidos_rt = df_in[~mask_programable].copy()
        return df_programable, df_excluidos_rt

    rep = _normalizar_reporte_tecnico(df_in)

    valores_programables = {
        "",
        "SIN DATOS",
        "NO REPORTADO",
        "PENDIENTE",
        "NO APLICA",
    }

    mask_programable = rep.isin(valores_programables)

    df_programable = df_in[mask_programable].copy()
    df_excluidos_rt = df_in[~mask_programable].copy()

    return df_programable, df_excluidos_rt

def _insertar_col_despues(df_in: pd.DataFrame, col_ref: str, new_col: str, values) -> pd.DataFrame:
    df = df_in.copy()
    if new_col in df.columns:
        df[new_col] = values
        return df
    

    df[new_col] = values
    cols = list(df.columns)
    try:
        i = cols.index(col_ref)
        cols.remove(new_col)
        cols.insert(i + 1, new_col)
        df = df[cols]
    except Exception:
        pass
    return df
    
def _df_center(df_in: pd.DataFrame):
    """Devuelve un Styler con encabezados y celdas centradas."""
    if df_in is None:
        return df_in
    return (
        df_in.style
        .set_table_styles([
            {"selector": "th", "props": [("text-align", "center"), ("vertical-align", "middle")]},
            {"selector": "td", "props": [("text-align", "center"), ("vertical-align", "middle")]},
        ])
        .set_properties(**{"text-align": "center", "vertical-align": "middle"})
    )    
def _color_estado_tabla(v):
    if v is None:
        return ""
    s = str(v).strip().upper()
    s = s.replace("DÍAS", "DIAS")

    if s == "VENCIDO":
        return "background-color: #FEE2E2; color: #B42318; font-weight: 700;"
    if s in ("ALERTA_0", "ALERTA_0 DIAS", "ALERTA 0 DIAS"):
        return "background-color: #FFEAD5; color: #C4320A; font-weight: 700;"
    if s == "ALERTA":
        return "background-color: #FEF3C7; color: #B54708; font-weight: 700;"
    if s in ("A TIEMPO", "ATIEMPO"):
        return "background-color: #DCFCE7; color: #027A48; font-weight: 700;"
    if s in ("SIN FECHA", "", "NAN", "NONE"):
        return "background-color: #DBEAFE; color: #175CD3; font-weight: 700;"

    return ""

def render_tabla_pro(
    df_in: pd.DataFrame,
    height: int = 320,
    col_estado: str | None = None,
    use_container_width: bool = True
):
    """
    Render uniforme para todas las tablas de Atlas 360.
    - Centra encabezados y datos
    - Aplica color semántico si existe columna de estado
    - Mantiene estilo corporativo consistente
    """
    if df_in is None:
        st.info("No hay datos para mostrar.")
        return

    styler = (
        df_in.style
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("text-align", "center"),
                    ("vertical-align", "middle"),
                    ("font-weight", "800"),
                    ("font-size", "13px"),
                ],
            },
            {
                "selector": "td",
                "props": [
                    ("text-align", "center"),
                    ("vertical-align", "middle"),
                    ("font-size", "13px"),
                ],
            },
        ])
        .set_properties(**{
            "text-align": "center",
            "vertical-align": "middle",
            "font-size": "13px",
        })
    )

    if col_estado and col_estado in df_in.columns:
        styler = styler.applymap(_color_estado_tabla, subset=[col_estado])

    st.dataframe(
        styler,
        use_container_width=use_container_width,
        height=height
    )
def render_tabla_html_pro(
    df_in: pd.DataFrame,
    titulo: str | None = None,
    height: int = 260
):
    """
    Render HTML real para tablas con control visual total.
    Ideal para tablas resumen o de consulta visual.
    """
    if df_in is None or df_in.empty:
        st.info("No hay datos para mostrar.")
        return

    df_show = df_in.copy()

    html_table = df_show.to_html(
        index=True,
        classes="atlas-table",
        border=0
    )

    html = f"""
    <div class="atlas-table-wrap" style="max-height:{height}px;">
        {html_table}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)    
# --------------------------
# CSS GLOBAL (UNA SOLA VEZ)
# --------------------------
st.markdown("""
<style>
    :root{
        --bg: #DEE6EE;
        --card: #FFFFFF;
        --text: #0F172A;
        --muted: rgba(15,23,42,.65);
        --line: rgba(15,23,42,.10);
        --shadow: 0 10px 25px rgba(15,23,42,.06);
        --shadow2: 0 16px 36px rgba(15,23,42,.10);
        --radius: 18px;

        --brand0: #3E9A2A;
        --brand1: #214D12;
        --brand2: #163A0B;
        --brandAccent: #2FA866;

        --kpi_total: #667085;
        --kpi_vencido: #D92D20;
        --kpi_alerta0: #F79009;
        --kpi_alerta: #EAAA08;
        --kpi_atiempo: #12B76A;
        --kpi_sinfecha: #2E90FA;
    }

    /* ✅ KPI semantic colors (ADENTRO DEL MISMO :root) */
    --kpi_total:   #667085;
    --kpi_vencido: #D92D20;
    --kpi_alerta0: #F79009;
    --kpi_alerta:  #EAAA08;
    --kpi_atiempo: #12B76A;
    --kpi_sinfecha:#2E90FA;
}
    /* Acento opcional */
    --brandAccent: #2FA866;
    }
    .banner-title{
    color:#fff;
    font-weight:800;
    font-size: 26px;
    line-height:1.1;
    margin:0;
    }        
    .banner{
    background:
    radial-gradient(520px 220px at 120px 42px, rgba(255,255,255,.10), rgba(255,255,255,0) 62%),
    linear-gradient(90deg, #5FB548 0%, #2E7D1F 45%, #114B08 100%);
    border-radius: 24px;
    padding: 20px 22px;
    box-shadow: 0 18px 40px rgba(15,23,42,.16);
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap: 18px;
    min-height: 140px;
    }

    .banner-left{
    display:flex;
    flex-direction:column;
    align-items:flex-start;
    justify-content:center;
    gap: 8px;
    }

    .banner-logo{
    display:flex;
    align-items:center;
    justify-content:flex-start;
    margin-bottom: 4px;
    }

    .banner-logo img{
    height: 42px !important;
    width: auto !important;
    display:block !important;
    object-fit:contain !important;
    background: transparent !important;
    border:none !important;
    box-shadow:none !important;
    padding:0 !important;
    margin:0 !important;
    filter: drop-shadow(0 2px 8px rgba(0,0,0,.22)) !important;
    opacity: 1 !important;
    }

    .banner-title{
    color: #FFFFFF !important;
    font-weight: 950 !important;
    font-size: 30px !important;
    line-height: 1.12 !important;
    margin: 0 !important;
    text-shadow: 0 2px 10px rgba(0,0,0,.20);
    }

    .banner-subtitle{
    color: rgba(255,255,255,.92);
    font-size: 14px;
    font-weight: 500;
    line-height: 1.45;
    margin-top: 2px;
    max-width: 620px;
    }

    .banner-right{
    display:flex;
    align-items:flex-end;
    justify-content:flex-end;
    height: 100%;
    padding-top: 92px;   /* baja el chip */
    padding-left: 10px;        
    }

    .chip{
    color:#fff;
    background: rgba(255,255,255,.12);
    border: 1px solid rgba(255,255,255,.20);
    padding: 10px 16px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 900;
    backdrop-filter: blur(6px);
    white-space: nowrap;
    box-shadow: 0 8px 20px rgba(0,0,0,.10);
    }
    @media (max-width: 900px){
    .banner{
        flex-direction: column;
        align-items: flex-start;
        padding: 18px 18px;
    }

    .banner-right{
        width: 100%;
        align-items: flex-start;
        justify-content: flex-start;
        padding-top: 10px;    
        padding-left: 0;    
    }
 }
    
/* ✅ Fondo global (forzado) */
html, body, .stApp {
background: var(--bg) !important;
}

div[data-testid="stAppViewContainer"]{
background: var(--bg) !important;
}

div[data-testid="stAppViewContainer"] > .main{
background: var(--bg) !important;
}

/* ✅ Evita "mordido" por overflow de contenedores */
div[data-testid="stAppViewContainer"] { overflow: visible !important; }
div[data-testid="stAppViewContainer"] > .main { overflow: visible !important; }

/* ✅ Oculta la barra superior nativa (la que recorta visualmente) */
header[data-testid="stHeader"] { display: none; }
div[data-testid="stToolbar"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Layout main container */
.block-container{
max-width: 100% !important;
padding: 1.4rem 2.1rem 2.0rem 2.1rem !important; /* top right bottom left */
}

/* Sidebar con más identidad visual */
section[data-testid="stSidebar"]{
background: linear-gradient(
    180deg,
    #F3F7F2 0%,
    #EEF4EC 100%
);
border-right: 4px solid #214D12; /* verde corporativo */
}
            
section[data-testid="stSidebar"] .block-container{
padding-top: 1rem !important;
}
section[data-testid="stSidebar"] .stMarkdown p{
color: var(--muted);
}

/* File uploader */
section[data-testid="stSidebar"] .stFileUploader{
border-radius: 18px !important;
padding: 10px 10px 2px 10px;
border: 1px solid var(--line);
box-shadow: var(--shadow);
background: #fff;
}
section[data-testid="stSidebar"] .stFileUploader label{
font-weight: 800;
}

/* Buttons */
.stButton>button{
border-radius: 14px !important;
border: 1px solid var(--line) !important;
box-shadow: var(--shadow);
padding: .55rem .85rem !important;
font-weight: 800 !important;
}
.stButton>button:hover{
transform: translateY(-1px);
box-shadow: var(--shadow2);
}
button[kind="primary"]{
background: linear-gradient(90deg,var(--brand1),var(--brand2)) !important;
border: 1px solid rgba(255,255,255,.18) !important;
}

/* Header custom */
.app-header{
width: 100%;
border-radius: 22px;
padding: 16px 18px;
margin-top: 6px;
margin-bottom: 14px;
box-shadow: var(--shadow2);
border: 1px solid rgba(255,255,255,0.22);

/* ✅ Verde más vivo: menos velo blanco + gradiente más contrastado */
background:
    radial-gradient(1200px 400px at 10% 10%, rgba(255,255,255,.10), transparent 60%),
    linear-gradient(90deg, var(--brand1), var(--brand2));
}
            
.app-title{
color:#fff;
font-size: 26px;
font-weight: 900;
letter-spacing: .2px;
margin:0;
}
.app-sub{
color: rgba(255,255,255,.92);
font-size: 13px;
margin-top: 6px;
}
.app-badge{
padding: 7px 12px;
border-radius: 999px;
background: rgba(255,255,255,0.16);
border:1px solid rgba(255,255,255,0.22);
color:#fff;
font-size: 12px;
white-space: nowrap;
}
            
/* Fecha/hora actualización en header (lado derecho, elegante) */
.app-updated{
color: rgba(255,255,255,.92);
font-size: 12px;
font-weight: 800;
letter-spacing: .2px;
padding: 6px 10px;
border-radius: 999px;
background: rgba(255,255,255,0.10);
border: 1px solid rgba(255,255,255,0.18);
backdrop-filter: blur(6px);
white-space: nowrap;
}            

/* Cards */
.card{
background: var(--card);
border: 1px solid var(--line);
border-radius: 18px;
padding: 14px 16px;
box-shadow: var(--shadow);
}
            
.section-title{
margin: 10px 0 8px 0;
font-weight: 900;
color: var(--text);
font-size: 16px;
}

/* ===========================
HERO KPI (solo resumen superior)
NO toca los KPIs ANS
=========================== */
.hero-kpi-grid{
display:grid;
grid-template-columns: repeat(4, minmax(0, 1fr));
gap: 16px;
margin-top: 6px;
}

.hero-kpi-card{
background: linear-gradient(180deg, rgba(255,255,255,.98) 0%, rgba(255,255,255,.94) 100%);
border: 1px solid rgba(15,23,42,.08);
border-radius: 18px;
padding: 16px 16px 14px 16px;
box-shadow: 0 10px 24px rgba(15,23,42,.08), 0 2px 6px rgba(15,23,42,.04);
position: relative;
overflow: hidden;
min-height: 118px;
transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}

.hero-kpi-card::before{
content:"";
position:absolute;
top:0; left:0; right:0;
height: 6px;
background: var(--hero-kpi);
}

.hero-kpi-card::after{
content:"";
position:absolute;
right:-16px;
top:-16px;
width: 72px;
height: 72px;
border-radius: 999px;
background: rgba(15,23,42,.03);
box-shadow: inset 0 0 0 1px rgba(15,23,42,.04);
}

.hero-kpi-card:hover{
transform: translateY(-3px);
box-shadow: 0 18px 36px rgba(15,23,42,.12), 0 4px 10px rgba(15,23,42,.05);
border-color: rgba(15,23,42,.14);
}

.hero-kpi-head{
display:flex;
align-items:center;
justify-content:space-between;
gap:10px;
position:relative;
z-index:2;
}

.hero-kpi-title{
font-size: 13px;
font-weight: 900;
color: rgba(15,23,42,.72);
margin: 0;
letter-spacing: .1px;
}

.hero-kpi-ico{
display:flex;
align-items:center;
justify-content:center;
font-size: 22px;
line-height: 1;
background: transparent;
border: none;
box-shadow: none;
position: relative;
z-index: 2;
padding: 0;
margin: 0;
min-width: 24px;
}

.hero-kpi-value{
font-size: 44px;
font-weight: 950;
color: #0F172A;
line-height: 1.0;
margin-top: 14px;
letter-spacing: -.8px;
position:relative;
z-index:2;
}

.hero-kpi-sub{
font-size: 12px;
color: rgba(15,23,42,.56);
margin-top: 10px;
position:relative;
z-index:2;
line-height: 1.35;
}
            
.hero-kpi-head{
display:flex;
align-items:center;
justify-content:space-between;
gap:10px;
padding-right:6px;
}   

.hero-kpi-progress{
margin-top: 12px;
width: 100%;
height: 9px;
background: rgba(15,23,42,.10);
border-radius: 999px;
overflow: hidden;
position: relative;
z-index: 2;
}

.hero-kpi-progress-bar{
height: 100%;
border-radius: 999px;
transition: width .35s ease;
box-shadow: 0 4px 10px rgba(0,0,0,.10);
}                    

@media (max-width: 1100px){
.hero-kpi-grid{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px){
.hero-kpi-grid{ grid-template-columns: repeat(1, minmax(0, 1fr)); }
}
/* KPI cards (legacy st.metric) */
div[data-testid="stMetric"]{
background: var(--card);
border: 1px solid var(--line);
padding: 12px 14px;
border-radius: 16px;
box-shadow: var(--shadow);
}
div[data-testid="stMetric"] label{
color: var(--muted) !important;
font-weight: 800 !important;
}
div[data-testid="stMetric"] div{
color: var(--text);
font-weight: 900;
}

/* ✅ KPI PRO (Resumen ANS) */
.kpi-grid{
display:grid;
grid-template-columns: repeat(6, minmax(0, 1fr));
gap: 14px;
margin-top: 8px;
}

.kpi-card{
background: linear-gradient(180deg, rgba(255,255,255,.98) 0%, rgba(255,255,255,.94) 100%);
border: 1px solid rgba(15,23,42,.08);
border-radius: 16px;
padding: 16px 14px 12px 14px;
box-shadow: 0 10px 22px rgba(15,23,42,.07), 0 2px 6px rgba(15,23,42,.04);
position: relative;
overflow: hidden;
min-height: 108px;
transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}

.kpi-topbar{
height: 8px;
border-radius: 999px;
width: calc(100% - 24px);
margin: 0 auto 12px auto;
opacity: .98;
}

.kpi-card:hover{
transform: translateY(-2px);
box-shadow: 0 16px 30px rgba(15,23,42,.12), 0 3px 8px rgba(15,23,42,.05);
border-color: rgba(15,23,42,.12);
}

.kpi-head{
display:block;
margin-bottom: 6px;
}

/* Titulos de los estados                        
.kpi-title{
font-size: 15px;
font-weight: 900;
color: rgba(15,23,42,.68);
margin: 0;
letter-spacing: .15px;
}

.kpi-value{
font-size: 28px;
font-weight: 950;
color: var(--text);
line-height: 1.05;
margin-top: 8px;
}

.kpi-sub{
font-size: 14px;
color: rgba(15,23,42,.55);
margin-top: 8px;
line-height: 1.3;
}

@media (max-width: 1100px){
.kpi-grid{ grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 640px){
.kpi-grid{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
}   
            
/* Tabs */
.stTabs [data-baseweb="tab-list"]{ gap: 10px; }
.stTabs [data-baseweb="tab"]{
border-radius: 14px;
padding: 10px 14px;
background: rgba(255,255,255,.65);
border: 1px solid var(--line);
}
.stTabs [aria-selected="true"]{
background: #fff;
box-shadow: var(--shadow);
border: 1px solid rgba(11,143,75,.22);
}

/* Dataframes */
div[data-testid="stDataFrame"]{
border-radius: 16px;
border: 1px solid var(--line);
box-shadow: var(--shadow);
overflow: hidden;
}

/* Expanders */
details{
border-radius: 16px !important;
border: 1px solid var(--line) !important;
box-shadow: var(--shadow);
background: #fff;
}

/* 🚫 Quitar botón colapsar (evita que pierdan filtros) */
button[data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"] button[kind="headerNoPadding"],
section[data-testid="stSidebar"] button[aria-label*="Collapse" i],
section[data-testid="stSidebar"] button[title*="Collapse" i]{
display: none !important;
}

/* Caja interna filtros */
section[data-testid="stSidebar"] h3:has(+ div){
background: #FFFFFF;
padding: 8px 10px;
border-radius: 10px;
border-left: 4px solid #214D12;
}  

/* ===========================
SIDEBAR: panel filtros con fondo (sin romper)
=========================== */

/* Fondo general sidebar (ya lo tienes, esto refuerza) */
section[data-testid="stSidebar"]{
background: linear-gradient(180deg,#F3F7F2 0%, #EEF4EC 100%) !important;
}

/* Contenedor interno: aplica "panel" suave */
section[data-testid="stSidebar"] .block-container{
background: transparent !important;
}

/* ✅ Deja el sidebar limpio y sin desbordes */
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{
background: transparent !important;
border: none !important;
border-radius: 0 !important;
padding: 0 !important;
box-shadow: none !important;
}

/* Espaciado limpio entre controles del sidebar */
section[data-testid="stSidebar"] .stMultiSelect,
section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stTextInput,
section[data-testid="stSidebar"] .stNumberInput,
section[data-testid="stSidebar"] .stFileUploader,
section[data-testid="stSidebar"] .stButton{
margin-bottom: 12px;
}                        

/* Ajuste: que no meta tarjeta al logo (solo suaviza) */
section[data-testid="stSidebar"] .logo-el,
section[data-testid="stSidebar"] .logo-el *{
background: transparent !important;
box-shadow: none !important;
border: none !important;
padding: 0 !important;
}      

/* ===========================
PREMIUM: inputs / selects
=========================== */

/* Targets comunes de Streamlit (BaseWeb) */
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea{
border-radius: 12px !important;
border: 1px solid rgba(0,122,61,.25) !important;   /* verde suave */
background: rgba(255,255,255,.75) !important;
box-shadow: 0 6px 14px rgba(15,23,42,.05);
}

/* Focus (cuando haces click) */
section[data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within,
section[data-testid="stSidebar"] input:focus,
section[data-testid="stSidebar"] textarea:focus{
border: 1px solid rgba(0,122,61,.55) !important;
box-shadow: 0 0 0 4px rgba(0,122,61,.12) !important;
}

/* Chips del multiselect (tags seleccionados) */
section[data-testid="stSidebar"] [data-baseweb="tag"]{
background: rgba(0,122,61,.12) !important;
border: 1px solid rgba(0,122,61,.25) !important;
border-radius: 999px !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"] span{
color: #0F172A !important;
font-weight: 800 !important;
}
/* ===========================
PREMIUM: botón principal
=========================== */

/* Refuerza el primary dentro del sidebar */
section[data-testid="stSidebar"] button[kind="primary"]{
width: 100% !important;
border-radius: 14px !important;
padding: .70rem 1rem !important;
font-weight: 900 !important;
letter-spacing: .2px;
background: linear-gradient(90deg, #00A651, #007A3D) !important; /* verde vivo */
border: 1px solid rgba(255,255,255,.22) !important;
box-shadow: 0 14px 28px rgba(0,122,61,.22) !important;
}

section[data-testid="stSidebar"] button[kind="primary"]:hover{
transform: translateY(-1px) !important;
box-shadow: 0 18px 36px rgba(0,122,61,.28) !important;
}

/* ===========================
PREMIUM: headers tipo chip
=========================== */

section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4{
display: inline-flex !important;
align-items: center !important;
gap: 8px !important;
padding: 6px 10px !important;
border-radius: 999px !important;
background: rgba(0,122,61,.10) !important;
border: 1px solid rgba(0,122,61,.18) !important;
color: #0F172A !important;
font-weight: 900 !important;
margin-top: .6rem !important;
margin-bottom: .5rem !important;
}
.header-right{
display:flex;
align-items:center;
justify-content:flex-end;
gap:8px;
}
.app-updated, .app-badge{
line-height: 1;
display:inline-flex;
align-items:center;
}
/* ===== KPI RUTA (PLAN) ===== */
.route-kpi-grid{
display:grid;
grid-template-columns: repeat(5, minmax(0, 1fr));
gap: 14px;
margin-top: 8px;
}

.route-kpi-card{
background: var(--card);
border: 1px solid var(--line);
border-radius: 16px;
padding: 12px 14px;
box-shadow: var(--shadow);
position: relative;
overflow: hidden;
min-height: 86px;
}

.route-kpi-top{
display:flex;
align-items:center;
justify-content:space-between;
gap: 10px;
}

.route-kpi-title{
font-size: 14px;
font-weight: 900;
color: var(--muted);
margin: 2px 0 6px 0;
}

.route-kpi-value{
font-size: 30px;
font-weight: 950;
color: var(--text);
line-height: 1.05;
}

.route-kpi-ico{
    display:flex;
    align-items:center;
    justify-content:center;
    background: transparent;
    border: none;
    box-shadow: none;
    width: auto;
    height: auto;
    padding: 0;
    font-size: 29px;
    line-height: 1;
    user-select:none;
    flex: 0 0 auto;
}
/* responsive */
@media (max-width: 1100px){
.route-kpi-grid{ grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 640px){
.route-kpi-grid{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
/* ===== Botón ayuda (❓) sidebar ===== */
.help-wrap{
display:flex;
justify-content:center;
align-items:center;
margin: 8px 0 10px 0;
}
.help-btn{
width: 42px;
height: 42px;
border-radius: 999px;
border: 1px solid rgba(0,122,61,.30);
background: rgba(255,255,255,.85);
box-shadow: 0 10px 22px rgba(15,23,42,.10);
color: #0B4D2A;
font-weight: 950;
font-size: 18px;
display:flex;
align-items:center;
justify-content:center;
cursor: pointer;
transition: transform .16s ease, box-shadow .16s ease, background .16s ease;
}
.help-btn:hover{
transform: translateY(-1px);
background: rgba(0,122,61,.10);
box-shadow: 0 16px 34px rgba(15,23,42,.14);
}
.help-hint{
text-align:center;
font-size: 11px;
color: rgba(15,23,42,.60);
margin-top: 4px;
}     

/* ===== HELP BUTTON (FULL PREMIUM) ===== */
.help-wrap{
display:flex;
justify-content:center;
align-items:center;
margin: 10px 0 10px 0;
}

.help-fab{
width: 44px;
height: 44px;
border-radius: 999px;
border: 1px solid rgba(0,122,61,.28);
background: rgba(255,255,255,.92);
box-shadow: 0 10px 22px rgba(15,23,42,.10);
color: #0B4D2A;
font-weight: 950;
font-size: 18px;
display:flex;
align-items:center;
justify-content:center;
cursor: pointer;
transition: transform .16s ease, box-shadow .16s ease, background .16s ease, border-color .16s ease;
user-select:none;
}

.help-fab:hover{
transform: translateY(-2px);
background: rgba(0,122,61,.10);
border-color: rgba(0,122,61,.45);
box-shadow: 0 18px 36px rgba(15,23,42,.14);
}

.help-fab:active{
transform: translateY(0px) scale(0.98);
}

.help-hint{
text-align:center;
font-size: 11px;
color: rgba(15,23,42,.60);
margin-top: 6px;
}

/* Quitar estilo azul del link */
.help-wrap a{
text-decoration: none !important;
}  
/* ===== Icono de ayuda (?) libre arriba del logo ===== */
.sidebar-topbar{
display:flex;
align-items:center;
justify-content:flex-start;   /* izquierda */
gap:10px;
padding: 6px 4px 2px 4px;
margin: 0 0 6px 0;
}

/* Link del ? */
.help-ico{
color: #98A2B3;               /* gris elegante */
font-weight: 900;
font-size: 26px;
line-height: 1;
text-decoration: none !important;
background: transparent !important;
border: none !important;
padding: 0 !important;
cursor: pointer;
user-select:none;
}

/* Hover (sutil) */
.help-ico:hover{
color: #667085;
transform: translateY(-1px);
}

/* Quita “focus ring” azul feo al click */
.help-ico:focus{
outline: none !important;
box-shadow: none !important;
} 

.manual-backdrop{
position: fixed;
inset: 0;
background: rgba(15,23,42,.22);
z-index: 999998;
}         
/* ✅ Cuando el manual está abierto: bloquea scroll del sidebar */
body.manual-open section[data-testid="stSidebar"]{
overflow: hidden !important;
}
body.manual-open section[data-testid="stSidebar"] .block-container{
overflow: hidden !important;
} 
    /* ===== FIX: LOGO SIN MARCO (override final) ===== */
    .banner-logo{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    border-radius: 0 !important;
    height: auto !important;
    line-height: 0 !important;
    }

    .banner-logo img{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    outline: none !important;

    clip-path: none !important;
    transform: none !important;

    height: 32px !important;          /* ajusta 28–36 si quieres */
    width: auto !important;
    display: block !important;

    /* contraste sutil sobre verde, sin “caja” */
    filter: drop-shadow(0 2px 6px rgba(0,0,0,.28)) !important;
    opacity: 1 !important;
    } 
            
    /* ===========================
    DATAFRAME (Streamlit/BaseWeb): centrar TODO
    =========================== */

    /* 1) Celdas y headers (virtualizados) */
    div[data-testid="stDataFrame"] [role="gridcell"],
    div[data-testid="stDataFrame"] [role="columnheader"]{
        justify-content: center !important;
        text-align: center !important;
    }

    /* 2) Contenido interno de las celdas (suele ser un div/span) */
    div[data-testid="stDataFrame"] [role="gridcell"] > div,
    div[data-testid="stDataFrame"] [role="columnheader"] > div{
        width: 100% !important;
        justify-content: center !important;
        text-align: center !important;
    }

    /* 3) Por si renderiza como tabla HTML en algunos casos */
    div[data-testid="stDataFrame"] table td,
    div[data-testid="stDataFrame"] table th{
        text-align: center !important;
        vertical-align: middle !important;
    }       
    /* ✅ FIX: Título del banner en blanco + negrita */
    .banner-title{
        color: #FFFFFF !important;
        font-weight: 950 !important;   /* más fuerte que 800 */
        font-size: 30px !important;   /* prueba 28–34 */
        line-height: 1.15 !important; /* para que no se “corte” */
        text-shadow: 0 2px 10px rgba(0,0,0,.28);
    }  
    .kpi-card{
    padding:18px 16px 14px 16px;
    }

    .kpi-value{
    margin-top:6px;
    }                
        /* ===== KPI EJECUTIVOS DEL PLAN ===== */
    .plan-kpi-grid{
    display:grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin-top: 8px;
    margin-bottom: 8px;
    }

    .plan-kpi-card{
    background: linear-gradient(180deg, rgba(255,255,255,.98) 0%, rgba(255,255,255,.94) 100%);
    border: 1px solid rgba(15,23,42,.08);
    border-radius: 16px;
    padding: 14px 14px 12px 14px;
    box-shadow: 0 10px 22px rgba(15,23,42,.07), 0 2px 6px rgba(15,23,42,.04);
    position: relative;
    overflow: hidden;
    min-height: 122px;
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }

    .plan-kpi-card:hover{
    transform: translateY(-2px);
    box-shadow: 0 16px 30px rgba(15,23,42,.12), 0 3px 8px rgba(15,23,42,.05);
    border-color: rgba(15,23,42,.12);
    }

    .plan-kpi-topbar{
    height: 6px;
    border-radius: 999px;
    width: calc(100% - 24px);
    margin: 0 auto 12px auto;
    opacity: .98;
    }

    .plan-kpi-head{
    display:flex;
    align-items:flex-start;       
    justify-content:flex-start;
    gap:8px;
    margin-bottom: 6px;
    }

    .plan-kpi-title{
        font-size: 12px;
        font-weight: 900;
        color: rgba(15,23,42,.68);
        margin: 0;
        letter-spacing: .10px;
        line-height: 1.20;
        word-break: keep-all;
    }

    .plan-kpi-value{
    font-size: 30px;
    font-weight: 950;
    color: var(--text);
    line-height: 1.05;
    margin-top: 8px;
    }

    .plan-kpi-sub{
    font-size: 12px;
    color: rgba(15,23,42,.55);
    margin-top: 8px;
    line-height: 1.3;
    }

    .plan-kpi-progress{
    margin-top: 12px;
    width: 100%;
    height: 8px;
    background: rgba(15,23,42,.10);
    border-radius: 999px;
    overflow: hidden;
    }

    .plan-kpi-progress-bar{
        height: 100%;
        border-radius: 999px;
        transition: width .35s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,.10);
    }
    .plan-kpi-head{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:10px;
        margin-bottom: 4px;
    }

    .plan-kpi-title-wrap{
        display:flex;
        align-items:flex-start;
        gap:8px;
        width: 100%;
    }

    .plan-kpi-icon{
        font-size: 18px;
        line-height: 1;
        flex: 0 0 auto;
        margin-top: 2px;
    }        
    

    @media (max-width: 1100px){
    .plan-kpi-grid{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 640px){
    .plan-kpi-grid{ grid-template-columns: repeat(1, minmax(0, 1fr)); }
    }   
    /* ===========================
    TABLAS PRO — ATLAS 360
    =========================== */

    /* Contenedor general */
    div[data-testid="stDataFrame"]{
        border-radius: 18px !important;
        border: 1px solid rgba(15,23,42,.10) !important;
        box-shadow: 0 10px 24px rgba(15,23,42,.08) !important;
        overflow: hidden !important;
        background: #FFFFFF !important;
    }

    /* Fondo interno */
    div[data-testid="stDataFrame"] div[role="grid"]{
        background: #FFFFFF !important;
    }

    /* Header */
    div[data-testid="stDataFrame"] [role="columnheader"]{
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF2F6 100%) !important;
        color: #0F172A !important;
        font-weight: 900 !important;
        font-size: 13px !important;
        border-bottom: 1px solid rgba(15,23,42,.10) !important;
        justify-content: center !important;
        text-align: center !important;
    }

    /* Texto interno del header */
    div[data-testid="stDataFrame"] [role="columnheader"] > div{
        width: 100% !important;
        justify-content: center !important;
        text-align: center !important;
    }

    /* Celdas */
    div[data-testid="stDataFrame"] [role="gridcell"]{
        background: #FFFFFF !important;
        color: #0F172A !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border-bottom: 1px solid rgba(15,23,42,.06) !important;
        justify-content: center !important;
        text-align: center !important;
        align-items: center !important;
    }

    /* Texto interno de celdas */
    div[data-testid="stDataFrame"] [role="gridcell"] > div{
        width: 100% !important;
        justify-content: center !important;
        text-align: center !important;
        align-items: center !important;
    }

    /* Hover elegante */
    div[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"]{
        background: #F7FAF8 !important;
    }

    /* Índice / primera columna visual */
    div[data-testid="stDataFrame"] [role="gridcell"]:first-child,
    div[data-testid="stDataFrame"] [role="columnheader"]:first-child{
        color: #667085 !important;
        font-weight: 700 !important;
    }

    /* Scrollbar */
    div[data-testid="stDataFrame"] ::-webkit-scrollbar{
        height: 10px;
        width: 10px;
    }
    div[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb{
        background: rgba(33,77,18,.22);
        border-radius: 999px;
    }
    div[data-testid="stDataFrame"] ::-webkit-scrollbar-track{
        background: rgba(15,23,42,.04);
    }

    /* Tabla HTML fallback */
    div[data-testid="stDataFrame"] table{
        width: 100% !important;
        border-collapse: collapse !important;
    }
    div[data-testid="stDataFrame"] table th{
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF2F6 100%) !important;
        color: #0F172A !important;
        text-align: center !important;
        font-weight: 900 !important;
        font-size: 13px !important;
        padding: 10px 8px !important;
    }
    div[data-testid="stDataFrame"] table td{
        text-align: center !important;
        vertical-align: middle !important;
        font-size: 13px !important;
        padding: 9px 8px !important;
        color: #0F172A !important;
    }

    /* Reduce efecto gris del lienzo alrededor */
    .element-container:has(div[data-testid="stDataFrame"]){
        margin-bottom: 10px !important;
    }                                      
    </style>
    """, unsafe_allow_html=True)

def render_header():
    base_dir = Path(__file__).resolve().parent
    candidates = [
        base_dir / "assets" / "logo_ruteo.png",
        base_dir.parent / "assets" / "logo_ruteo.png",
    ]
    logo_path = next((p for p in candidates if p.exists()), None)

    logo_b64 = ""
    if logo_path:
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")

    logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Atlas360">' if logo_b64 else ""

    last_refresh = st.session_state.get("last_refresh")
    if last_refresh:
        fecha_chip = last_refresh.strftime("%d/%m/%Y %I:%M %p")
    else:
        fecha_chip = "Sin actualización"

    header_html = f"""
<div class="banner">
    <div class="banner-left">
        <div class="banner-logo">{logo_html}</div>
        <div class="banner-title">Enrutamiento Operativo por Cuadrillas</div>
        <div class="banner-subtitle">
            Planeación, priorización y monitoreo territorial de pedidos ANS
        </div>
    </div>
    <div class="banner-right">
        <div class="chip">Actualizado: {fecha_chip}</div>
    </div>
</div>
"""
    st.markdown(header_html, unsafe_allow_html=True)

render_header()
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# session defaults
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "rutas_general" not in st.session_state:
    st.session_state["rutas_general"] = None
if "df_asig_general" not in st.session_state:
    st.session_state["df_asig_general"] = None
if "plan_diario" not in st.session_state:
    st.session_state["plan_diario"] = None
if "filters_key" not in st.session_state:
    st.session_state["filters_key"] = 0

# ✅ NUEVO: estado del mapa PLAN
if "cid_sel_plan_mapa" not in st.session_state:
    st.session_state["cid_sel_plan_mapa"] = "(Todas)"
if "map_render_token_plan" not in st.session_state:
    st.session_state["map_render_token_plan"] = "init_plan"

# -----------------------------
# Sidebar: SOLO carga (primero)
# -----------------------------
with st.sidebar:
    from pathlib import Path

    MANUAL_MD_PATH = Path(__file__).resolve().parent / "docs" / "manual_usuario.md"

    def _leer_manual_md() -> str:
        try:
            if MANUAL_MD_PATH.exists():
                return MANUAL_MD_PATH.read_text(encoding="utf-8")
            return f"⚠️ No se encontró el manual en: {MANUAL_MD_PATH}"
        except Exception as e:
            return f"⚠️ Error leyendo manual: {e}"   
    # =========================
    # ✅ Icono de ayuda (PNG) sin cuadro + modal por query param
    # =========================
    def _img_b64(p: Path) -> str:
        return base64.b64encode(p.read_bytes()).decode("utf-8")

    # Detecta help_icon.png (tu favicon) en assets
    # Base del proyecto (directorio donde está app.py)
    base_dir = Path(__file__).resolve().parent

    help_candidates = [
        base_dir / "assets" / "help_icon.png",
        base_dir.parent / "assets" / "help_icon.png",
    ]
    help_icon_path = next((p for p in help_candidates if p.exists()), None)

    # ✅ Compatible: manual=1 (link) y open_manual=1 (postMessage/js)
        # ✅ Compatible: manual=1 (link) y open_manual=1 (postMessage/js)
    try:
        qp = st.query_params

        def _qp_is_one(key: str) -> bool:
            v = qp.get(key)
            if isinstance(v, (list, tuple)):
                v = v[0] if v else None
            return str(v) == "1"

        manual_on = _qp_is_one("manual") or _qp_is_one("open_manual")

        # =========================
        # ✅ MANUAL NATIVO (SIN IFRAME) — SI open_manual=1
        # =========================
        if manual_on:
            st.markdown("### 📘 Manual de Usuario")
            st.markdown(_leer_manual_md(), unsafe_allow_html=False)

            # Botón cerrar: limpia query params y vuelve a la app normal
            if st.button("✕ Cerrar manual", type="primary", use_container_width=True, key="btn_cerrar_manual"):
                try:
                    st.query_params.pop("manual", None)
                    st.query_params.pop("open_manual", None)
                except Exception:
                    st.experimental_set_query_params()
                st.rerun()

            # Detiene el resto del sidebar (para que no aparezca uploader / filtros encima)
            st.stop()

    except Exception:
        qp = st.experimental_get_query_params()
        manual_on = (qp.get("manual", ["0"])[0] == "1") or (qp.get("open_manual", ["0"])[0] == "1")

    # CSS del icono (sin caja, alineado izquierda, gris “elegante”)
    st.markdown("""
    <style>
    .sidebar-topbar{
    display:flex;
    align-items:center;
    justify-content:flex-start;
    padding: 6px 2px 2px 2px;
    margin: 0 0 6px 0;
    }
    a.help-link{
    display:inline-flex;
    align-items:center;
    gap:8px;
    text-decoration:none !important;
    }
    a.help-link img{
    width: 34px;
    height: 34px;
    opacity: .85;              /* gris visual */
    filter: grayscale(100%);    /* lo deja gris aunque el png tenga color */
    transition: transform .12s ease, opacity .12s ease;
    }
    a.help-link:hover img{
    opacity: 1;
    transform: translateY(-1px);
    }        
    /* ===== MANUAL OVERLAY (PRO / sin st.modal) ===== */
    .manual-overlay{
    position: fixed;
    top: 10px;
    left: 10px;
    width: 330px;                 /* ajusta si tu sidebar es más ancho */
    height: calc(100vh - 20px);
    z-index: 999999;
    pointer-events: auto;
    }

    .manual-panel{
    height: 100%;
    background: rgba(255,255,255,.96);
    border: 1px solid rgba(15,23,42,.10);
    border-left: 4px solid #214D12;
    border-radius: 18px;
    box-shadow: 0 18px 50px rgba(15,23,42,.18);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    }

    .manual-head{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap: 10px;
    padding: 12px 14px;
    background: linear-gradient(90deg, rgba(0,122,61,.10), rgba(255,255,255,.0));
    border-bottom: 1px solid rgba(15,23,42,.08);
    }

    .manual-title{
    font-weight: 950;
    color: #0F172A;
    font-size: 13px;
    letter-spacing: .2px;
    }

    .manual-close{
    width: 34px;
    height: 34px;
    border-radius: 12px;
    border: 1px solid rgba(0,122,61,.22);
    background: rgba(255,255,255,.9);
    font-weight: 950;
    cursor: pointer;
    }

    .manual-body{
    padding: 12px 14px;
    overflow: auto;               /* ✅ scroll interno */
    font-size: 12px;              /* ✅ evita “brinco” */
    line-height: 1.55;
    color: rgba(15,23,42,.78);
    }

    .manual-body h1{ font-size: 16px; margin: 6px 0 8px 0; }
    .manual-body h2{ font-size: 14px; margin: 10px 0 6px 0; }
    .manual-body h3{ font-size: 13px; margin: 10px 0 6px 0; }
    .manual-body ul{ margin: 6px 0 8px 18px; }
    .manual-body code{ background: rgba(0,122,61,.08); padding: 1px 6px; border-radius: 8px; }

    /* Scrollbar elegante */
    .manual-body::-webkit-scrollbar{ width: 10px; }
    .manual-body::-webkit-scrollbar-thumb{
    background: rgba(0,122,61,.22);
    border-radius: 999px;
    }
    </style>
    """, unsafe_allow_html=True)


    # Render del icono clickeable (SIN JS: Streamlit friendly)
    if help_icon_path:
        b64 = _img_b64(help_icon_path)
        st.markdown(
            f"""
            <div class="sidebar-topbar">
            <a class="help-link"
                href="?open_manual=1"
                target="_self"
                title="Abrir manual de usuario">
                <img src="data:image/png;base64,{b64}" />
            </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ✅ Sincroniza el estado del modal con el query param (manual/open_manual)
    if "show_manual" not in st.session_state:
        st.session_state["show_manual"] = bool(manual_on)
    else:
        # Si el usuario abrió/cerró por URL, reflejarlo en session_state
        if bool(st.session_state.get("show_manual")) != bool(manual_on):
            st.session_state["show_manual"] = bool(manual_on)

    if st.session_state.get("show_manual", False):
        _has_modal = False

        if _has_modal:
            with st.modal("📘 Manual de Usuario"):
                st.markdown(_leer_manual_md())
                c1, c2 = st.columns([1, 1])
                with c2:
                    if st.button("Cerrar", type="primary"):
                        st.session_state["show_manual"] = False
                        try:
                            st.query_params.pop("manual", None)
                            st.query_params.pop("open_manual", None)
                        except Exception:
                            st.experimental_set_query_params()
                        st.rerun()
        else:
            # ✅ Manual PRO: overlay fijo (HTML real) + bloquea scroll del sidebar
            manual_txt = _leer_manual_md()

            # Escape HTML
            safe = (
                manual_txt
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            # Markdown mínimo a HTML (títulos/bullets/párrafos)
            lines = safe.splitlines()
            out = []
            in_ul = False

            for ln in lines:
                s = ln.strip()

                if s.startswith("### "):
                    if in_ul:
                        out.append("</ul>")
                        in_ul = False
                    out.append(f"<h3>{s[4:]}</h3>")
                    continue

                if s.startswith("## "):
                    if in_ul:
                        out.append("</ul>")
                        in_ul = False
                    out.append(f"<h2>{s[3:]}</h2>")
                    continue

                if s.startswith("# "):
                    if in_ul:
                        out.append("</ul>")
                        in_ul = False
                    out.append(f"<h1>{s[2:]}</h1>")
                    continue

                is_bullet = s.startswith("- ") or s.startswith("* ")
                if is_bullet:
                    if not in_ul:
                        out.append("<ul>")
                        in_ul = True
                    out.append(f"<li>{s[2:]}</li>")
                    continue

                if in_ul:
                    out.append("</ul>")
                    in_ul = False

                if s == "":
                    out.append("<div style='height:8px'></div>")
                else:
                    out.append(f"<p>{s}</p>")

            if in_ul:
                out.append("</ul>")

            manual_html = "\n".join(out)
            # 🔥 IMPORTANTE: renderiza como HTML REAL (no como texto) usando components.html
            components.html(
                f"""
                <style>
                /* backdrop + overlay */
                .manual-backdrop{{
                    position: fixed;
                    inset: 0;
                    background: rgba(15,23,42,.22);
                    z-index: 999998;
                }}
                .manual-overlay{{
                    position: fixed;
                    top: 10px;
                    left: 10px;
                    width: 330px;
                    height: calc(100vh - 20px);
                    z-index: 999999;
                }}
                .manual-panel{{
                    height: 100%;
                    background: rgba(255,255,255,.96);
                    border: 1px solid rgba(15,23,42,.10);
                    border-left: 4px solid #214D12;
                    border-radius: 18px;
                    box-shadow: 0 18px 50px rgba(15,23,42,.18);
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }}
                .manual-head{{
                    display:flex;
                    align-items:center;
                    justify-content:space-between;
                    gap: 10px;
                    padding: 12px 14px;
                    background: linear-gradient(90deg, rgba(0,122,61,.10), rgba(255,255,255,0));
                    border-bottom: 1px solid rgba(15,23,42,.08);
                }}
                .manual-title{{
                    font-weight: 950;
                    color: #0F172A;
                    font-size: 13px;
                    letter-spacing: .2px;
                }}
                .manual-close{{
                    width: 34px;
                    height: 34px;
                    border-radius: 12px;
                    border: 1px solid rgba(0,122,61,.22);
                    background: rgba(255,255,255,.9);
                    font-weight: 950;
                    cursor: pointer;
                }}
                .manual-body{{
                    padding: 12px 14px;
                    overflow: auto;
                    font-size: 12px;
                    line-height: 1.55;
                    color: rgba(15,23,42,.78);
                }}
                .manual-body h1{{ font-size: 16px; margin: 6px 0 8px 0; }}
                .manual-body h2{{ font-size: 14px; margin: 10px 0 6px 0; }}
                .manual-body h3{{ font-size: 13px; margin: 10px 0 6px 0; }}
                .manual-body ul{{ margin: 6px 0 8px 18px; }}
                .manual-body::-webkit-scrollbar{{ width: 10px; }}
                .manual-body::-webkit-scrollbar-thumb{{ background: rgba(0,122,61,.22); border-radius: 999px; }}

                /* ✅ bloquear scroll sidebar cuando el manual está abierto */
                body.manual-open section[data-testid="stSidebar"]{{ overflow: hidden !important; }}
                body.manual-open section[data-testid="stSidebar"] .block-container{{ overflow: hidden !important; }}
                </style>

                <script>
                // Marca manual abierto (bloquea scroll)
                document.body.classList.add("manual-open");
                // Si recargan sin manual, intenta limpiar
                window.addEventListener("beforeunload", () => {{
                    document.body.classList.remove("manual-open");
                }});
                function closeManual(){{
                    document.body.classList.remove("manual-open");
                    // cierra quitando query param (recarga misma ruta)
                    const url = new URL(window.location.href);
                    url.searchParams.delete("open_manual");
                    url.searchParams.delete("manual");
                    window.location.href = url.toString();
                }}
                </script>

                <div class="manual-backdrop" onclick="closeManual()"></div>

                <div class="manual-overlay">
                <div class="manual-panel">
                    <div class="manual-head">
                    <div class="manual-title">📘 Manual de Usuario</div>
                    <button class="manual-close" onclick="closeManual()">✕</button>
                    </div>
                    <div class="manual-body">
                    {manual_html}
                    </div>
                </div>
                </div>
                """,
                height=10,
            )

    # ✅ Logo ELITE (busca en routing_app/assets y en ../assets)
    base_dir = Path(__file__).resolve().parent  # .../routing_app
    candidates = [
        base_dir / "assets" / "logo_elite_sin_fondo.png",
        base_dir.parent / "assets" / "logo_elite_sin_fondo.png",
    ]
    logo_path = next((p for p in candidates if p.exists()), None)

    # ✅ CSS: SIN margin-top negativo (evita scroll)
    st.markdown(
        """
        <style>
        /* Sidebar: quita aire arriba y evita barras raras */
        section[data-testid="stSidebar"]{ overflow-x: hidden !important; }
        section[data-testid="stSidebar"] .block-container{
            padding-top: 0.15rem !important;
            padding-bottom: 0.75rem !important;
        }

        /* Logo: centrado y pegado arriba SIN empujar layout */
        .logo-el{
            display:flex;
            justify-content:center;
            align-items:center;
            margin: 0.10rem 0 0.50rem 0 !important;
        }

        /* Reduce un poco el alto del uploader para no forzar scroll */
        section[data-testid="stSidebar"] .stFileUploader{
            padding: 8px 10px 2px 10px !important;
            margin-top: 6px !important;
        }

        /* Quita espacios grandes debajo de captions */
        section[data-testid="stSidebar"] .stCaption{
            margin-bottom: .35rem !important;
        }
        /* =========================
        ✨ Animaciones suaves (premium)
        ========================= */

        /* Animación de entrada (fade + lift) para el contenido principal */
        @keyframes fadeLift {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
        }

        /* Entrada más visible + un poquito más lenta */
        div[data-testid="stAppViewContainer"] > .main .block-container{
        animation: fadeLift .55s cubic-bezier(.22, 1, .36, 1);
        }

        /* Header un toque más elegante */
        .app-header{
        animation: fadeLift .55s cubic-bezier(.22, 1, .36, 1);
        }   

        /* Tarjetas (cards) y métricas: hover elegante */
    .card,
        div[data-testid="stMetric"]{
        transition: transform .22s cubic-bezier(.22, 1, .36, 1),
                    box-shadow .22s cubic-bezier(.22, 1, .36, 1),
                    border-color .22s ease;
        will-change: transform;
        }

        .card:hover,
        div[data-testid="stMetric"]:hover{
        transform: translateY(-4px);
        box-shadow: 0 18px 45px rgba(15,23,42,.14);
        border-color: rgba(0,0,0,.12);
        }

        /* Botones: hover con micro-interacción */
        .stButton>button{
        transition: transform .18s cubic-bezier(.22, 1, .36, 1),
                    box-shadow .18s cubic-bezier(.22, 1, .36, 1),
                    filter .18s ease;
        will-change: transform;
        }

        .stButton>button:hover{
        transform: translateY(-2px);
        box-shadow: 0 14px 30px rgba(15,23,42,.14);
        }

        .stButton>button:active{
        transform: translateY(0) scale(0.97);
        }

        /* Inputs (text, multiselect, selectbox): transición suave + foco */
        div[data-baseweb="select"],
        div[data-baseweb="input"],
        textarea{
        transition: box-shadow .15s ease, border-color .15s ease, transform .15s ease;
        }
        div[data-baseweb="select"]:focus-within,
        div[data-baseweb="input"]:focus-within,
        textarea:focus{
        box-shadow: 0 0 0 4px rgba(0,122,61,.18);
        transform: translateY(-1px);
        }

        /* Expander: hover sutil para sentirlo "clickeable" */
        details{
        transition: box-shadow .18s ease, transform .18s ease;
        }
        details:hover{
        transform: translateY(-1px);
        box-shadow: var(--shadow2);
        }

        /* Tabs: transición suave (ya tienes estilos, esto los hace más finos) */
        .stTabs [data-baseweb="tab"]{
        transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
        }
        .stTabs [data-baseweb="tab"]:hover{
        transform: translateY(-1px);
        box-shadow: var(--shadow);
        }

        /* Respeta accesibilidad: si el usuario prefiere menos animación */
        @media (prefers-reduced-motion: reduce){
        *{ animation: none !important; transition: none !important; }
        }
        /* ===========================
        TABS: Hover verde oscuro + animación
        =========================== */

        /* Tab normal */
        .stTabs [data-baseweb="tab"]{
        transition: background .18s ease, border-color .18s ease, transform .18s cubic-bezier(.22,1,.36,1), color .18s ease;
        }

        /* Hover (cuando pasas el mouse) */
        .stTabs [data-baseweb="tab"]:hover{
        background: rgba(0,122,61,.12) !important;         /* verde suave */
        border-color: rgba(0,122,61,.35) !important;        /* borde verde */
        transform: translateY(-1px);
        }

        /* Texto del tab en hover */
        .stTabs [data-baseweb="tab"]:hover p{
        color: #0B4D2A !important;                          /* verde oscuro */
        font-weight: 900;
        }

        /* Tab seleccionado (activo) */
        .stTabs [aria-selected="true"]{
        background: rgba(0,122,61,.16) !important;
        border-color: rgba(0,122,61,.55) !important;
        box-shadow: 0 10px 22px rgba(15,23,42,.10);
        }

        /* Texto del tab activo */
        .stTabs [aria-selected="true"] p{
        color: #064B27 !important;
        font-weight: 950;
        }
        /* ===========================
        FIX 1: Tab activo NO debe verse como hover permanente
        + FIX 2: Quitar "mordido" arriba de los tabs
        =========================== */

        /* 2) Corrige el contenedor del tab-list (quita mordida / aire raro) */
        .stTabs [data-baseweb="tab-list"]{
        padding-top: 8px !important;
        margin-top: 6px !important;
        padding-bottom: 6px !important;
        border-bottom: 1px solid rgba(15,23,42,.10) !important;
        }

        /* Evita que algo recorte arriba */
        .stTabs{
        overflow: visible !important;
        }

        /* Tab normal: un poquito más bajo para que no toque arriba */
        .stTabs [data-baseweb="tab"]{
        margin-top: 2px !important;
        }

        /* 1) Tab activo: estilo "premium" pero NO igual al hover */
        .stTabs [aria-selected="true"]{
        background: rgba(255,255,255,.92) !important;       /* blanco elegante */
        border: 1px solid rgba(0,122,61,.35) !important;    /* borde verde */
        box-shadow: 0 10px 22px rgba(15,23,42,.10) !important;
        transform: none !important;                         /* que no parezca hover */
        }

        /* Texto activo: verde oscuro */
        .stTabs [aria-selected="true"] p{
        color: #064B27 !important;
        font-weight: 950 !important;
        }

        /* Hover SOLO cuando NO está seleccionado */
        .stTabs [data-baseweb="tab"]:not([aria-selected="true"]):hover{
        background: rgba(0,122,61,.12) !important;
        border-color: rgba(0,122,61,.35) !important;
        transform: translateY(-1px);
        }
        .stTabs [data-baseweb="tab"]:not([aria-selected="true"]):hover p{
        color: #0B4D2A !important;
        font-weight: 900 !important;
        }

        /* Separación entre KPIs y el expander de auditoría */
        route-expander-gap{
        margin-top: 12px;
        }

        /* Fuerza cursor flecha en plotly */
        .js-plotly-plot, .js-plotly-plot * { cursor: default !important; }

        /* ===== MANUAL (fallback pro) ===== */
        .manual-box{
        background: rgba(255,255,255,.92);
        border: 1px solid rgba(15,23,42,.10);
        border-radius: 16px;
        box-shadow: 0 14px 30px rgba(15,23,42,.10);
        padding: 12px 14px;
        margin-top: 10px;
        }
        .manual-title{
        font-weight: 950;
        color: #0F172A;
        font-size: 14px;
        margin-bottom: 8px;
        }
        .manual-content{
        color: rgba(15,23,42,.78);
        font-size: 13px;
        line-height: 1.55;
        max-height: 52vh;         /* scroll “pro” */
        overflow: auto;
        padding-right: 6px;
        }
        .manual-content::-webkit-scrollbar{ width: 10px; }
        .manual-content::-webkit-scrollbar-thumb{
        background: rgba(0,122,61,.25);
        border-radius: 999px;
        }
        .manual-actions{
        display:flex;
        justify-content:flex-end;
        margin-top: 10px;
        }
        /* ✅ Manual: ocultar icono de ayuda antiguo del sidebar (sin eliminar código) */
        section[data-testid="stSidebar"] .sidebar-topbar,
        section[data-testid="stSidebar"] a.help-link{
        display: none !important;
        }
        /* ✅ Oculta SIEMPRE el contenedor del icono (aunque quede vacío) */
        section[data-testid="stSidebar"] .sidebar-topbar{
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        }

        /* ✅ Por si el link del icono existe */
        section[data-testid="stSidebar"] a.help-link{
        display: none !important;
        }
        /* ===========================
        TABLA HTML PRO — ATLAS 360
        =========================== */

        .atlas-table-wrap{
            background: #FFFFFF;
            border: 1px solid rgba(15,23,42,.10);
            border-radius: 18px;
            box-shadow: 0 10px 24px rgba(15,23,42,.08);
            overflow: auto;
            padding: 0;
        }

        .atlas-table{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 13px;
            color: #0F172A;
        }

        .atlas-table thead th{
            position: sticky;
            top: 0;
            z-index: 2;
            background: linear-gradient(180deg, #F8FBF8 0%, #ECF5EE 100%);
            color: #0F172A;
            font-weight: 950;
            font-size: 18px;
            letter-spacing: .15px;
            text-align: center;
            padding: 14px 12px;
            border-bottom: 1px solid rgba(15,23,42,.10);
            border-right: 1px solid rgba(15,23,42,.06);
        }

       .atlas-table tbody td,
       .atlas-table tbody th{
            text-align: center;
            vertical-align: middle;
            padding: 12px 12px;
            border-bottom: 1px solid rgba(15,23,42,.06);
            border-right: 1px solid rgba(15,23,42,.05);
            background: #FFFFFF;
            font-size: 18px;
            font-weight: 600;
        }

        /* Columna numérica más fuerte */
        .atlas-table tbody td:last-child{
            font-weight: 800;
            color: #0F172A;
        }

        .atlas-table tbody tr:hover td,
        .atlas-table tbody tr:hover th{
            background: #F7FAF8;
        }

        .atlas-table tbody th{
            color: #475467;
            font-weight: 700;
            background: #F9FAFB;
            width: 56px;
            font-size: 13px;
        }

        .atlas-table thead th:first-child{
            border-top-left-radius: 18px;
        }

        .atlas-table thead th:last-child{
            border-top-right-radius: 18px;
        }

        .atlas-table-wrap::-webkit-scrollbar{
            width: 10px;
            height: 10px;
        }
        .atlas-table-wrap::-webkit-scrollbar-thumb{
            background: rgba(33,77,18,.22);
            border-radius: 999px;
        }
        .atlas-table-wrap::-webkit-scrollbar-track{
            background: rgba(15,23,42,.04);
        }
        /* ===========================
        PANEL DE MODO DE VISUALIZACIÓN
        =========================== */
        .mode-card{
            background: linear-gradient(180deg, rgba(255,255,255,.98) 0%, rgba(255,255,255,.94) 100%);
            border: 1px solid rgba(15,23,42,.08);
            border-radius: 16px;
            padding: 14px 16px 12px 16px;
            box-shadow: 0 10px 22px rgba(15,23,42,.07), 0 2px 6px rgba(15,23,42,.04);
            margin-bottom: 10px;
        }

        .mode-card-title{
            font-size: 14px;
            font-weight: 950;
            color: #0F172A;
            margin-bottom: 4px;
        }

        .mode-card-sub{
            font-size: 12px;
            color: rgba(15,23,42,.62);
            margin-bottom: 10px;
            line-height: 1.4;
        }

        .mode-card-status{
            margin-top: 8px;
            font-size: 12px;
            font-weight: 700;
            color: #0B4D2A;
            background: rgba(0,122,61,.08);
            border: 1px solid rgba(0,122,61,.15);
            border-radius: 999px;
            padding: 6px 10px;
            display: inline-block;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ✅ Logo ELITE
    if logo_path:
        st.markdown('<div class="logo-el">', unsafe_allow_html=True)
        st.image(str(logo_path), width=300)   # 240–260 suele evitar scroll
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### ⚙️ Configuración")
    st.caption("Carga tu archivo para iniciar")

    uploaded = st.file_uploader(
        "📎 Excel (.xlsx)",
        type=["xlsx"],
        key=f"uploader_{st.session_state.uploader_key}"
    )

    if uploaded is None:
        st.caption("⬆️ Sube el Excel para iniciar el análisis.")
        st.stop()
# -----------------------------
# Cargar DF (ANTES de filtros)
# -----------------------------
try:
    file_bytes = uploaded.getvalue()
    df, df_ok, df_bad = _preparar_df(file_bytes)
    tz = pytz.timezone("America/Bogota")
    st.session_state["last_refresh"] = datetime.now(tz)

    if DEBUG_UI:
        st.subheader("🧪 DEBUG: Columnas detectadas")
        st.write(df.columns.tolist())

except Exception as e:
    st.error(f"No se pudo cargar el Excel: {e}")
    st.stop()
# -----------------------------
# Sidebar: filtros (ya existe df_ok)
# -----------------------------
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🧪 Filtros  <span style='background:rgba(0,122,61,.12);border:1px solid rgba(0,122,61,.22);padding:3px 8px;border-radius:999px;font-size:12px;font-weight:900;'>Panel</span>", unsafe_allow_html=True)
    st.caption("Ajusta el universo de pedidos")

    fk = st.session_state["filters_key"]

    estado_opts = sorted(df_ok["estado"].dropna().unique().tolist()) if "estado" in df_ok.columns else []
    actividad_opts = sorted(df_ok["actividad"].dropna().unique().tolist()) if "actividad" in df_ok.columns else []
    zona_opts = sorted(df_ok["zona"].dropna().unique().tolist()) if "zona" in df_ok.columns else []

    concepto_sel = st.multiselect("CONCEPTO", sorted(list(CONCEPTOS_RUTEO)),
                                default=sorted(list(CONCEPTOS_RUTEO)), key=f"f_concepto_{fk}")
    estado_sel = st.multiselect("ESTADO", estado_opts, default=[], key=f"f_estado_{fk}")
    actividad_sel = st.multiselect("ACTIVIDAD", actividad_opts, default=[], key=f"f_actividad_{fk}")
    zona_sel = st.multiselect("ZONA", zona_opts, default=[], key=f"f_zona_{fk}")

    # ============================================================
    # ✅ PUNTO 2: Filtro REPORTE_TECNICO (SIN marca_temporal)
    # - Va después de ZONA y antes del filtro rápido KPI (como pediste)
    # - Regla: si NO selecciona nada => muestra TODO
    # - Si selecciona "SIN DATOS" => filtra solo esos
    # ============================================================

    col_rep = _pick_col_reporte_operativo(df_ok)
    rep_opts = (
        sorted(
            df_ok[col_rep]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("", "SIN DATOS")
            .unique()
            .tolist()
        )
        if col_rep else []
    )

    st.markdown("#### 🧾 Filtro técnico")

    rep_sel_ui = st.multiselect(
        "REPORTE TECNICO",
        rep_opts,
        default=[],  # ✅ vacío => NO filtra (muestra TODO)
        key=f"f_reporte_{fk}",
        help="Si no eliges nada verás TODOS. Si eliges 'SIN DATOS' verás solo los programables."
    )

    # ✅ (UI) Se oculta filtro rápido KPI para no confundir al usuario final
    #     Mantengo la variable para NO romper la lógica más abajo.
    kpi_estado = []

    # --- Control de aplicar filtros (para evitar reruns pesados) ---
    if "aplicar_filtros_ok" not in st.session_state:
        st.session_state["aplicar_filtros_ok"] = False

    if st.button("✅ Aplicar filtros", type="primary", use_container_width=True, key=f"btn_aplicar_{fk}"):
        st.session_state["aplicar_filtros_ok"] = True
        tz = pytz.timezone("America/Bogota")
        st.session_state["last_refresh"] = datetime.now(tz)
        st.rerun()

    st.markdown("---")
    if st.button("🧹 Limpiar filtros", use_container_width=True, key=f"btn_limpiar_{fk}"):
        st.session_state["rutas_general"] = None
        st.session_state["df_asig_general"] = None
        st.session_state["plan_diario"] = None
        st.session_state["aplicar_filtros_ok"] = False  # ✅ ESTA ES LA CLAVE
        st.session_state["filters_key"] = fk + 1
        st.rerun()

# -----------------------------
# Resumen de carga (hero cards)
# -----------------------------
st.markdown('<div class="section-title">Resumen de carga</div>', unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)

total_excel = len(df)
validos = len(df_ok)
invalidos = len(df_bad)
salud_geo = (validos / total_excel * 100) if total_excel > 0 else 0

if salud_geo >= 95:
    color_salud = "#12B76A"
    ico_salud = "🌍"
    sub_salud = "Cobertura geográfica excelente"
elif salud_geo >= 85:
    color_salud = "#F79009"
    ico_salud = "⚠️"
    sub_salud = "Cobertura geográfica con atención"
else:
    color_salud = "#D92D20"
    ico_salud = "🚨"
    sub_salud = "Cobertura geográfica crítica"

if invalidos == 0:
    sub_invalidos = "Sin errores geográficos"
    color_invalidos = "#12B76A"   # verde
    ico_invalidos = "✅"
else:
    sub_invalidos = "Requieren corrección geográfica"
    color_invalidos = "#F79009"   # naranja
    ico_invalidos = "⚠️"   

hero_html = f"""
<div class="hero-kpi-grid">
<div class="hero-kpi-card" style="--hero-kpi:#667085;">
<div class="hero-kpi-head">
<div class="hero-kpi-title">Pedidos en Excel</div>
<div class="hero-kpi-ico">📦</div>
</div>
<div class="hero-kpi-value">{total_excel:,}</div>
<div class="hero-kpi-sub">Universo total cargado</div>
</div>

<div class="hero-kpi-card" style="--hero-kpi:#12B76A;">
<div class="hero-kpi-head">
<div class="hero-kpi-title">Pedidos válidos</div>
<div class="hero-kpi-ico">✅</div>
</div>
<div class="hero-kpi-value">{validos:,}</div>
<div class="hero-kpi-sub">Con lat / lng correctos</div>
</div>

<div class="hero-kpi-card" style="--hero-kpi:{color_invalidos};">
<div class="hero-kpi-head">
<div class="hero-kpi-title">Pedidos inválidos</div>
<div class="hero-kpi-ico">{ico_invalidos}</div>
</div>
<div class="hero-kpi-value">{invalidos:,}</div>
<div class="hero-kpi-sub">{sub_invalidos}</div>
</div>

<div class="hero-kpi-card" style="--hero-kpi:{color_salud};">
<div class="hero-kpi-head">
<div class="hero-kpi-title">Salud geográfica</div>
<div class="hero-kpi-ico">{ico_salud}</div>
</div>
<div class="hero-kpi-value">{salud_geo:.1f}%</div>
<div class="hero-kpi-sub">{sub_salud}</div>
<div class="hero-kpi-progress">
<div class="hero-kpi-progress-bar" style="width:{salud_geo:.1f}%; background:{color_salud};"></div>
</div>
</div>
"""

st.markdown(hero_html, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)    
# -----------------------------
# Aviso de invalidos (card)
# -----------------------------
if len(df_bad) > 0:
    st.markdown(f"""
    <div class="card">
    <div style="font-weight:900; color:#0F172A; font-size:14px;">
        ⚠️ Filas sin lat/lng Inválidos: {len(df_bad)}
    </div>
    <div style="color:rgba(15,23,42,.70); font-size:13px; margin-top:6px;">
        Puedes ver el detalle y corregir coordenadas en el Excel origen.
    </div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Ver filas inválidas"):
        st.dataframe(df_bad.head(100), use_container_width=True)

# -----------------------------
# Zona geo sin filtros
# -----------------------------
st.markdown('<div class="section-title">🧭 Pedidos por zona geográfica (Vista general)</div>', unsafe_allow_html=True)
zona_geo_counts = df_ok["zona_geo"].value_counts(dropna=False).reset_index()
zona_geo_counts.columns = ["Zona geográfica", "Pedidos"]
render_tabla_html_pro(zona_geo_counts, height=220)


# -----------------------------
# Aplicar filtros (solo cuando el usuario lo pida)
# -----------------------------
if not st.session_state.get("aplicar_filtros_ok", False):
    st.info("Ajusta los filtros y pulsa **✅ Aplicar filtros**.")
    st.stop()

df_filtrado = aplicar_filtros(
    df_ok,
    conceptos=concepto_sel,
    estados=estado_sel,
    actividades=actividad_sel,
    zonas=zona_sel
)

# ✅ PUNTO 2 (parte B): aplicar filtros técnicos (reporte_tecnico / ejecutados)
# Normaliza SIN DATOS => "" para filtrar exacto
if rep_sel_ui and col_rep:
    rep_real = df_filtrado[col_rep].fillna("").astype(str).str.strip()
    # para comparar, convertimos "" a "SIN DATOS" en una serie auxiliar
    rep_ui = rep_real.replace("", "SIN DATOS")
    df_filtrado = df_filtrado[rep_ui.isin(rep_sel_ui)].copy()

# ✅ PUNTO 1 (base): dedupe por pedido antes de rutas/plan/kpis
df_filtrado = _dedupe_por_pedido(df_filtrado)
df_programable, df_excluidos_rt = _split_operativo_vs_excluidos(df_filtrado)

if DEBUG_UI:
    col_flag_dbg = _pick_col_flag_reporte(df_filtrado)
    col_rep_dbg = _pick_col_reporte_operativo(df_filtrado)

    st.write("DEBUG col_flag_reporte:", col_flag_dbg)
    st.write("DEBUG col_reporte_operativo:", col_rep_dbg)

    if col_flag_dbg:
        st.write(
            "DEBUG valores flag:",
            df_filtrado[col_flag_dbg]
            .fillna("")
            .astype(str)
            .map(_canon_rt_text)
            .value_counts(dropna=False)
            .head(20)
        )

    if col_rep_dbg:
        st.write(
            "DEBUG valores reporte operativo:",
            df_filtrado[col_rep_dbg]
            .fillna("")
            .astype(str)
            .map(_canon_rt_text)
            .replace("", "SIN DATOS")
            .value_counts(dropna=False)
            .head(20)
        )
    if USAR_REGLA_REPORTE_TECNICO and len(df_programable) == 0:
        st.warning("DEBUG: la regla actual de REPORTE_TECNICO dejó 0 pedidos programables.")
# filtro KPI
if kpi_estado:
    df_tmp = df_filtrado.copy()
    est_norm = (
        df_tmp["estado"].fillna("").astype(str).str.strip().str.upper()
        if "estado" in df_tmp.columns
        else pd.Series([""] * len(df_tmp), index=df_tmp.index)
    )

    mask = pd.Series(False, index=df_tmp.index)

    if "VENCIDO" in kpi_estado:
        mask |= (est_norm == "VENCIDO")
    if "ALERTA" in kpi_estado:
        mask |= (est_norm == "ALERTA")
    if "A TIEMPO" in kpi_estado:
        mask |= est_norm.isin(["A TIEMPO", "ATIEMPO"])
    if "ALERTA_0 DÍAS" in kpi_estado:
        mask |= est_norm.isin(["ALERTA_0", "ALERTA_0 DIAS", "ALERTA 0 DIAS", "ALERTA_0 DÍAS", "ALERTA 0 DÍAS"])
    if "SIN FECHA" in kpi_estado:
        col_fecha = (
            "FECHA_LIMITE_ANS" if "FECHA_LIMITE_ANS" in df_tmp.columns
            else ("fecha_limite_ans" if "fecha_limite_ans" in df_tmp.columns else None)
        )
        if col_fecha:
            mask |= pd.to_datetime(df_tmp[col_fecha], errors="coerce").isna()

    df_filtrado = df_tmp[mask].copy()

# -----------------------------
# Vista unificada: KPIs + tabla zona
# -----------------------------
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

ver_universo_total = st.toggle(
    "Cantidad de pedidos por estado",
    value=False,
    key="toggle_vista_operativa_general"
)

if ver_universo_total:
    texto_vista_actual = "Vista: universo filtrado total."
    df_base_vista = df_filtrado
else:
    texto_vista_actual = "Vista: universo programable real."
    df_base_vista = df_programable

st.caption(texto_vista_actual)

# -----------------------------
# KPI ANS (card)
# -----------------------------
st.markdown('<div class="section-title">📊 Resumen ANS</div>', unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)

st.caption(texto_vista_actual)

k = _kpi_estado_counts(df_base_vista)
render_kpis(k)

if USAR_REGLA_REPORTE_TECNICO:
    excluidos_cnt = len(df_excluidos_rt)
    total_base_cnt = len(df_filtrado)
    operativos_cnt = len(df_programable)

    st.markdown(
        f"""
        <div style="margin-top:10px; font-size:13px; color:rgba(15,23,42,.78); line-height:1.5;">
            • Universo filtrado: <b>{total_base_cnt:,}</b><br>
            • Excluidos por <b>REPORTE_TECNICO</b> distinto de <b>SIN DATOS</b>: <b>{excluidos_cnt:,}</b><br>
            • Universo operativo real: <b>{operativos_cnt:,}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown('</div>', unsafe_allow_html=True)


# Zona geo con filtros
st.markdown('<div class="section-title">🧭 Pedidos por zona geográfica</div>', unsafe_allow_html=True)
st.caption(texto_vista_actual)

zona_geo_counts_f = df_base_vista["zona_geo"].value_counts(dropna=False).reset_index()
zona_geo_counts_f.columns = ["Zona geográfica", "Pedidos"]
render_tabla_html_pro(zona_geo_counts_f, height=220)

if len(df_filtrado) == 0:
    st.warning("No hay registros filtrados. Ajusta filtros.")
    st.stop()

# -----------------------------
# Tabs
# -----------------------------
tab_mapa, tab_cuadrillas, tab_plan, tab_datos, tab_dashboard, tab_cc_ans, tab_manual = st.tabs(
    ["🗺️ Mapa", "👥 Cuadrillas", "📌 Plan Diario ANS", "📄 Datos", "📊 Dashboard", "🎯 Centro de Control ANS", "📘 Manual"]
)
# ========= TAB MAPA GENERAL =========
with tab_mapa:

    # -----------------------------
    # Bodega / Origen
    # -----------------------------
    st.markdown('<div class="section-title">🏭 Bodega / Origen</div>', unsafe_allow_html=True)

    zona_unica = zona_sel[0] if isinstance(zona_sel, list) and len(zona_sel) == 1 else None
    zona_unica_norm = str(zona_unica).strip().upper() if zona_unica else None

    BODEGAS_FIJAS = {"METROPOLITANA SUR": (6.19739, -75.58916)}
    BODEGAS_DIRECCION_FIJA = {"METROPOLITANA SUR": "Cl 12 Sur # 51B-29, San Fernando, Medellín"}

    origen_scope = zona_unica_norm if zona_unica_norm else "__MULTI__"
    if st.session_state.get("origen_scope") != origen_scope:
        st.session_state["origen_scope"] = origen_scope
        st.session_state["bodega_lat"] = None
        st.session_state["bodega_lng"] = None

    editar_manual = st.toggle(
        "✍️ Editar coordenadas manualmente",
        value=False,
        help="Si está OFF y la zona tiene bodega fija, se fuerzan las coordenadas oficiales."
    )

    if zona_unica_norm and zona_unica_norm in BODEGAS_FIJAS and not editar_manual:
        default_lat, default_lng = BODEGAS_FIJAS[zona_unica_norm]
        origen_modo = f"📌 Origen fijo (bodega real) para {zona_unica}"
        st.session_state["bodega_lat"] = float(default_lat)
        st.session_state["bodega_lng"] = float(default_lng)
    else:
        sugerido = sugerir_origen_por_df(df_programable if len(df_programable) > 0 else df_filtrado)
        if sugerido and (st.session_state.get("bodega_lat") is None or st.session_state.get("bodega_lng") is None):
            default_lat, default_lng = sugerido
            origen_modo = "📍 Origen sugerido (centro de pedidos filtrados)"
            st.session_state["bodega_lat"] = float(default_lat)
            st.session_state["bodega_lng"] = float(default_lng)
        else:
            if st.session_state.get("bodega_lat") is None or st.session_state.get("bodega_lng") is None:
                st.session_state["bodega_lat"] = 6.19739
                st.session_state["bodega_lng"] = -75.58916
            origen_modo = "📍 Origen manual (o fallback)"

    st.markdown('<div class="card">', unsafe_allow_html=True)
    c0, c1, c2, c3 = st.columns([1.4, 1, 1, 2.2], vertical_alignment="center")

    with c0:
        st.caption(origen_modo)

    with c1:
        bodega_lat = st.number_input(
            "Bodega - Latitud",
            format="%.6f",
            key="bodega_lat",
            disabled=(zona_unica_norm in BODEGAS_FIJAS and not editar_manual)
        )

    with c2:
        bodega_lng = st.number_input(
            "Bodega - Longitud",
            format="%.6f",
            key="bodega_lng",
            disabled=(zona_unica_norm in BODEGAS_FIJAS and not editar_manual)
        )

    with c3:
        if zona_unica_norm and zona_unica_norm in BODEGAS_DIRECCION_FIJA and (zona_unica_norm in BODEGAS_FIJAS) and not editar_manual:
            st.markdown(f"📍 **Dirección:** {BODEGAS_DIRECCION_FIJA[zona_unica_norm]}")
        else:
            st.caption("📍 Dirección (aprox) — se resuelve solo si la solicitas (evita lentitud).")

            # ✅ Botón bajo demanda (no bloquea el render normal)
            if st.button("📍 Resolver dirección (aprox)", use_container_width=True, key="btn_resolver_dir"):
                try:
                    direccion_bodega = obtener_direccion_por_latlng(float(bodega_lat), float(bodega_lng))
                    if direccion_bodega:
                        st.success(f"📍 Dirección (aprox): {direccion_bodega}")
                    else:
                        st.warning("📍 Dirección: no se pudo resolver.")
                except Exception as e:
                    st.error(f"📍 Error resolviendo dirección: {e}")
    st.markdown('</div>', unsafe_allow_html=True)


    st.markdown('<div class="section-title">🗺️ Mapa General</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        n_cuadrillas_general = st.number_input("Cuadrillas (GENERAL)", 1, 20, 8, 1, key="n_cuadrillas_general")
    with g2:
        respetar_zonas_geo_general = st.toggle(
            "No mezclar zona_geo (GENERAL)",
            value=True,
            key="respetar_zonas_geo_general"
        )

    if st.button("🧭 Generar rutas (MAPA GENERAL)", type="primary", use_container_width=True, key="btn_gen_general"):
        # ✅ PUNTO 1: base sin duplicados
        df_base_rutas = _dedupe_por_pedido(df_programable)

        df_asig = asignar_cuadrillas_kmeans(df_base_rutas, n_cuadrillas=int(n_cuadrillas_general))
        rutas = generar_rutas_por_cuadrilla(df_asig, start_lat=bodega_lat, start_lng=bodega_lng)
        registrar_evento("generar_rutas", "Proceso ejecutado correctamente")

        # ✅ PUNTO 1 (verificación suave): no debería haber pedidos repetidos entre cuadrillas
        col_ped = _pick_col(df_asig, ["PEDIDO", "pedido"])
        if col_ped:
            dups = df_asig[col_ped].astype(str).duplicated().sum()
            if dups > 0:
                st.warning(f"Se detectaron {dups} pedidos duplicados después de asignar cuadrillas. Revisa el origen.")
        st.session_state["df_asig_general"] = df_asig
        st.session_state["rutas_general"] = rutas

        # ✅ AQUÍ PEGAS ESTO (justo después de guardar rutas)
        st.session_state["cid_sel_mapa_general"] = "(Selecciona)"
        st.session_state["map_render_token_general"] = datetime.now(pytz.timezone("America/Bogota")).strftime("%Y%m%d%H%M%S%f")

    st.markdown('</div>', unsafe_allow_html=True)
    # ✅ Estado UI para no romper el mapa en reruns
    if "cid_sel_mapa_general" not in st.session_state:
        st.session_state["cid_sel_mapa_general"] = "(Selecciona)"
    if "map_render_token_general" not in st.session_state:
        st.session_state["map_render_token_general"] = "init"

    rutas = st.session_state.get("rutas_general")
    if not rutas:
        st.info("Pulsa **Generar rutas (MAPA GENERAL)** para ver el mapa general.")
    else:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        cids = sorted(list(rutas.keys()))
        #opciones = ["(Todas)", "(Selecciona)"] + cids
        opciones = ["(Todas)", "(Selecciona)"] + cids

        # ✅ Evita warning: no mezclar default (index) + session_state (key)
        if st.session_state.get("cid_sel_mapa_general") not in opciones:
            st.session_state["cid_sel_mapa_general"] = "(Selecciona)"

        cid_sel = st.selectbox(
            "Ver en el mapa (GENERAL)",
            opciones,
            key="cid_sel_mapa_general"
        )

        # ✅ Solo cambia el token si cambian inputs reales (NO usar datetime)
        token_now = f"{cid_sel}"
        prev = st.session_state.get("map_render_token_general")

        if token_now != prev:
            st.session_state["map_render_token_general"] = token_now

        # ✅ SIEMPRE renderizar un iframe (evita que Streamlit “re-use” el del otro tab)
        if cid_sel == "(Selecciona)":
            #st.info("Selecciona una cuadrilla o elige **(Todas)**.")
            st.info("Selecciona una cuadrilla para visualizar el mapa.")
            ph = f"<!-- MAP_GENERAL_PLACEHOLDER {st.session_state.get('map_render_token_general','init')} -->"
            components.html(ph, height=1, scrolling=False)

        elif cid_sel == "(Todas)":
            m = construir_mapa_rutas(
                rutas,
                bodega_lat=bodega_lat,
                bodega_lng=bodega_lng,
                color_mode="cuadrilla",
                tile_mode="calles",
                force_cluster=True   # ✅ clave para que no se muera el navegador
            )

            html_map = m.get_root().render()
            html_map = html_map.replace(
                "</body>",
                f"<script>window.__map_token_general='{st.session_state['map_render_token_general']}|ALL';</script></body>"
            )
            components.html(html_map, height=650, scrolling=False)

        else:
            rutas_mapa = {cid_sel: rutas[cid_sel]}
            m = construir_mapa_rutas(
                rutas_mapa,
                bodega_lat=bodega_lat,
                bodega_lng=bodega_lng,
                color_mode="cuadrilla",
                tile_mode="calles",
                force_cluster=False
            )

            html_map = m.get_root().render()
            html_map = html_map.replace(
                "</body>",
                f"<script>window.__map_token_general='{st.session_state['map_render_token_general']}';</script></body>"
            )
            components.html(html_map, height=650, scrolling=False)

        st.markdown('</div>', unsafe_allow_html=True)

# ========= TAB CUADRILLAS GENERAL =========
with tab_cuadrillas:
    st.markdown('<div class="section-title">👥 Cuadrillas (General)</div>', unsafe_allow_html=True)

    rutas = st.session_state.get("rutas_general")
    if not rutas:
        st.info("Primero genera rutas en el tab **🗺️ Mapa (GENERAL)**.")
    else:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        cids = sorted(list(rutas.keys()))
        cid_sel = st.selectbox("Selecciona cuadrilla (GENERAL)", cids, index=0, key="cid_sel_tab_general")

        df_ruta = rutas[cid_sel]
        #st.dataframe(df_ruta, use_container_width=True, height=520)
        col_estado_ruta = _pick_col(df_ruta, ["estado", "ESTADO", "estado_ans", "ESTADO_ANS"])

        if col_estado_ruta:
            st.dataframe(
                df_ruta.style.applymap(_color_estado_tabla, subset=[col_estado_ruta]),
                use_container_width=True,
                height=520
            )
        else:
            st.dataframe(df_ruta, use_container_width=True, height=520)

        urls = urls_google_maps_cuadrilla_tramos(
            df_ruta,
            start_lat=bodega_lat,
            start_lng=bodega_lng,
            max_paradas_por_tramo=9,
            travelmode="driving"
        )

        if len(urls) == 1:
            st.link_button("🧭 Abrir ruta en Google Maps (Cuadrilla)", urls[0], use_container_width=True)
        elif len(urls) > 1:
            st.info(f"Google Maps en celular limita paradas por ruta. Se generaron {len(urls)} tramos.")
            for i, u in enumerate(urls, start=1):
                st.link_button(f"🧭 Abrir ruta — TRAMO {i}", u, use_container_width=True)

        excel_bytes = exportar_rutas_excel_bytes(rutas)
        st.download_button(
            "⬇️ Descargar Excel (GENERAL)",
            data=excel_bytes,
            file_name="rutas_general.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_excel_general"
        )

        st.markdown('</div>', unsafe_allow_html=True)

# ========= TAB PLAN DIARIO =========
with tab_plan:
    st.markdown('<div class="section-title">📌 Plan Diario ANS</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    p1, p2 = st.columns(2)
    with p1:
        n_plan = st.number_input("Cuadrillas (PLAN)", 1, 20, 8, 1, key="n_plan")
    with p2:
        cap_plan = st.number_input("Pedidos por cuadrilla (PLAN)", 5, 50, 15, 1, key="cap_plan")

    respetar_plan_zona = st.toggle("No mezclar zona_geo (PLAN)", value=True, key="respetar_plan_zona")

    if st.button("📌 Generar Plan Diario", type="primary", use_container_width=True, key="btn_gen_plan"):
        from src.trazabilidad import plan_diario_8x15

        # ✅ PUNTO 1: base sin duplicados
        df_base_plan = _dedupe_por_pedido(df_programable)

        # ✅ CORRECCIÓN: quitamos argumentos repetidos (sin cambiar tu lógica)
        plan = plan_diario_8x15(
            df_in=df_base_plan,
            n_cuadrillas=int(n_plan),
            cap_por_cuadrilla=int(cap_plan),
            origen_lat=bodega_lat,
            origen_lng=bodega_lng,
            col_pedido="PEDIDO",
            col_estado="estado",
            col_fecha_limite="FECHA_LIMITE_ANS" if "FECHA_LIMITE_ANS" in df_programable.columns else "fecha_limite_ans",
            col_zona_geo="zona_geo",
            col_lat="lat",
            col_lng="lng",
            respetar_zona_geo=bool(respetar_plan_zona)
        )

        # ✅ PUNTO 1 (verificación suave): no debería repetirse pedido entre cuadrillas del plan
        try:
            df_plan_all_chk = pd.concat(plan.values(), ignore_index=True)
            col_ped_plan = _pick_col(df_plan_all_chk, ["PEDIDO", "pedido"])
            if col_ped_plan:
                dup_cnt = df_plan_all_chk[col_ped_plan].astype(str).duplicated().sum()
                if dup_cnt > 0:
                    st.warning(f"Plan generado con {dup_cnt} pedidos duplicados. Revisa el origen / filtros.")
        except Exception:
            pass

        st.session_state["plan_diario"] = plan
        st.session_state["cid_sel_plan_mapa"] = "(Todas)"
        st.session_state["map_render_token_plan"] = datetime.now(
            pytz.timezone("America/Bogota")
        ).strftime("%Y%m%d%H%M%S%f")
        st.success(f"Plan generado: {len(plan)} cuadrillas.")

    st.markdown('</div>', unsafe_allow_html=True)

    plan = st.session_state.get("plan_diario")
    if not plan:
        st.info("Pulsa **Generar Plan Diario**.")
    else:
        df_plan_all = pd.concat(plan.values(), ignore_index=True)

        st.markdown('<div class="section-title">📌 Resumen (PLAN)</div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)

        res_plan = df_plan_all.groupby(["cuadrilla_id", "zona_geo"]).size().reset_index(name="pedidos")
        res_plan.columns = ["Cuadrilla", "Zona geográfica", "Cantidad pedidos"]

        render_tabla_html_pro(res_plan, height=240)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">👥 Detalle por cuadrilla (PLAN)</div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)

        cids_plan = sorted(plan.keys())
        cid_p = st.selectbox("Cuadrilla (PLAN)", cids_plan, index=0, key="cid_p")

        # 🔎 Buscador interno dentro del PLAN
        buscar_plan = st.text_input(
            "🔎 Buscar pedido o cliente en esta cuadrilla",
            key="buscar_plan"
        )
        df_p = plan[cid_p].copy()

        # ✅ Buscador rápido: si son números -> filtra por PEDIDO; si no -> filtra por CLIENTE
        df_mostrar = df_p.copy()
        if buscar_plan:
            q = buscar_plan.strip()

            col_ped = "PEDIDO" if "PEDIDO" in df_mostrar.columns else ("pedido" if "pedido" in df_mostrar.columns else None)
            col_cli = "CLIENTE" if "CLIENTE" in df_mostrar.columns else ("cliente" if "cliente" in df_mostrar.columns else None)

            if q.isdigit() and col_ped:
                df_mostrar = df_mostrar[df_mostrar[col_ped].astype(str).str.contains(q, na=False)].copy()
            else:
                ql = q.lower()
                if col_cli:
                    df_mostrar = df_mostrar[df_mostrar[col_cli].astype(str).str.lower().str.contains(ql, na=False)].copy()
                else:
                    df_mostrar = df_mostrar[
                        df_mostrar.astype(str)
                        .apply(lambda row: row.str.lower().str.contains(ql, na=False))
                        .any(axis=1)
                    ].copy()

        st.write(f"Registros en cuadrilla {cid_p}: **{len(df_mostrar)}**")
        #st.dataframe(df_mostrar, use_container_width=True, height=520)
        col_estado_plan = _pick_col(df_mostrar, ["estado", "ESTADO", "estado_ans", "ESTADO_ANS"])

        if col_estado_plan:
            st.dataframe(
                df_mostrar.style.applymap(_color_estado_tabla, subset=[col_estado_plan]),
                use_container_width=True,
                height=520
            )
        else:
            st.dataframe(df_mostrar, use_container_width=True, height=520)

        # ==============================
        # 📏 Indicadores de Ruta (PLAN)
        # ==============================
        st.markdown("### 📏 Indicadores de ruta (PLAN)")

        def _haversine_km(lat1, lon1, lat2, lon2):
            import math
            R = 6371.0
            try:
                lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
            except Exception:
                return None
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            return 2 * R * math.asin(math.sqrt(a))

        def _asegurar_dist_prev(df_route: pd.DataFrame, origen_lat: float, origen_lng: float, col_lat="lat", col_lng="lng"):
            if df_route is None or df_route.empty:
                return df_route

            dfx = df_route.copy()

            if col_lat not in dfx.columns or col_lng not in dfx.columns:
                return dfx

            if "dist_prev_km" in dfx.columns:
                s = pd.to_numeric(dfx["dist_prev_km"], errors="coerce")
                if s.notna().any():
                    dfx["dist_prev_km"] = s
                    return dfx

            lats = pd.to_numeric(dfx[col_lat], errors="coerce")
            lngs = pd.to_numeric(dfx[col_lng], errors="coerce")

            dist = []
            prev_lat, prev_lng = float(origen_lat), float(origen_lng)
            for la, lo in zip(lats, lngs):
                if pd.isna(la) or pd.isna(lo):
                    dist.append(None)
                    continue
                dkm = _haversine_km(prev_lat, prev_lng, la, lo)
                dist.append(dkm)
                prev_lat, prev_lng = float(la), float(lo)

            dfx["dist_prev_km"] = pd.to_numeric(pd.Series(dist), errors="coerce")
            return dfx

        df_ind = _asegurar_dist_prev(df_p, bodega_lat, bodega_lng, col_lat="lat", col_lng="lng")

        dist_series = pd.to_numeric(df_ind.get("dist_prev_km", pd.Series(dtype=float)), errors="coerce")
        dist_valid = dist_series.dropna()

        total_paradas = len(df_ind)
        total_km = float(dist_valid.sum()) if len(dist_valid) else 0.0
        avg_km = float(dist_valid.mean()) if len(dist_valid) else 0.0
        max_km = float(dist_valid.max()) if len(dist_valid) else 0.0
        prim_km = float(dist_valid.iloc[0]) if len(dist_valid) else 0.0

        cards = [
            ("Paradas", "🛵", f"{int(total_paradas)}"),
            ("Total ruta(km)", "🗺️", f"{total_km:,.1f}"),
            ("Prom.tramo(km)", "📏", f"{avg_km:,.1f}"),
            ("Tramo máx(km)", "🚧", f"{max_km:,.1f}"),
            ("Bodega→1ra(km)", "🏭", f"{prim_km:,.1f}"),
        ]

        parts = ['<div class="route-kpi-grid">']
        for title, ico, val in cards:
            parts.append(
                f'<div class="route-kpi-card">'
                f'  <div class="route-kpi-top">'
                f'    <div class="route-kpi-title">{title}</div>'
                f'    <div class="route-kpi-ico">{ico}</div>'
                f'  </div>'
                f'  <div class="route-kpi-value">{val}</div>'
                f'</div>'
            )
        parts.append("</div>")

        st.markdown("".join(parts), unsafe_allow_html=True)

        with st.expander("Ver detalle de tramos (auditoría)"):
            df_tramos = df_ind.copy()

            if "ORDEN_VISITA" in df_tramos.columns:
                df_tramos["ORDEN_VISITA"] = pd.to_numeric(df_tramos["ORDEN_VISITA"], errors="coerce")
                df_tramos = df_tramos.sort_values("ORDEN_VISITA", ascending=True, na_position="last")

            cols_tramos = []
            for c in ["ORDEN_VISITA", "PEDIDO", "pedido", "zona_geo", "estado_ans", "estado", "lat", "lng", "dist_prev_km"]:
                if c in df_tramos.columns and c not in cols_tramos:
                    cols_tramos.append(c)

            if cols_tramos:
                df_show = df_tramos[cols_tramos].copy()
                if "dist_prev_km" in df_show.columns:
                    df_show["dist_prev_km"] = pd.to_numeric(df_show["dist_prev_km"], errors="coerce").round(2)
                st.dataframe(df_show, use_container_width=True, height=320)
            else:
                st.dataframe(df_tramos.head(50), use_container_width=True)

        st.caption("💡 Distancia estimada “en línea recta”. Sirve para revisar que la ruta tenga sentido; al conducir puede ser mayor.")

        # ------------------------------
        # WhatsApp (tu bloque intacto)
        # ------------------------------
        st.markdown("### 📲 WhatsApp — Guía de visita (copiar y pegar)")
        import re

        df_w = df_p.copy()

        if "ORDEN_VISITA" in df_w.columns:
            df_w["ORDEN_VISITA"] = pd.to_numeric(df_w["ORDEN_VISITA"], errors="coerce")
            df_w = df_w.sort_values("ORDEN_VISITA", ascending=True)

        def _norm(s: str) -> str:
            return re.sub(r"[^A-Z0-9]+", "", str(s or "").upper())

        def _pick_col_norm(df_: pd.DataFrame, candidates: list[str]) -> str | None:
            if df_ is None or df_.empty:
                return None
            cols_ = list(df_.columns)
            norm_map = {_norm(c): c for c in cols_}
            for cand in candidates:
                if cand in cols_:
                    return cand
                key = _norm(cand)
                if key in norm_map:
                    return norm_map[key]
                for nk, real in norm_map.items():
                    if nk.startswith(key):
                        return real
            return None

        def _pick_celular_contacto(df_: pd.DataFrame) -> str | None:
            if df_ is None or df_.empty:
                return None
            cols_ = list(df_.columns)

            def _is_tel(c: str) -> bool:
                return "TELEFONO" in str(c).upper()

            for c in cols_:
                if _is_tel(c):
                    continue
                if str(c).strip().upper() == "CELULAR_CONTACTO":
                    return c

            for c in cols_:
                if _is_tel(c):
                    continue
                if _norm(c) in ("CELULARCONTACTO", "CELULARCONTAC", "CELULARCONTACT"):
                    return c

            for c in cols_:
                if _is_tel(c):
                    continue
                if str(c).strip().lower() == "celular":
                    return c

            for c in cols_:
                up = str(c).upper()
                if "CELULAR" in up and not _is_tel(c):
                    return c
            return None

        def _safe(v):
            return "" if pd.isna(v) else str(v).strip()

        df_src_base = df if isinstance(df, pd.DataFrame) and len(df) > 0 else df_filtrado

        col_pedido_plan = _pick_col_norm(df_w, ["PEDIDO", "pedido"])
        col_pedido_src = _pick_col_norm(df_src_base, ["PEDIDO", "pedido"])

        col_nombre_src = _pick_col_norm(df_src_base, ["NOMBRE_CLIENTE", "nombre_cliente", "CLIENTE", "cliente"])
        col_cel_src = _pick_celular_contacto(df_src_base)
        col_dir_src = _pick_col_norm(df_src_base, ["DIRECCION", "direccion"])
        col_fecha_src = _pick_col_norm(df_src_base, ["FECHA_LIMITE_ANS", "fecha_limite_ans"])

        df_w_enriched = df_w.copy()
        if col_pedido_plan and col_pedido_src:
            try:
                src_cols = [col_pedido_src]
                for c in [col_nombre_src, col_cel_src, col_dir_src, col_fecha_src]:
                    if c and c not in src_cols:
                        src_cols.append(c)

                df_src_small = df_src_base[src_cols].copy()
                df_w_enriched[col_pedido_plan] = df_w_enriched[col_pedido_plan].astype(str)
                df_src_small[col_pedido_src] = df_src_small[col_pedido_src].astype(str)

                df_w_enriched = df_w_enriched.merge(
                    df_src_small,
                    how="left",
                    left_on=col_pedido_plan,
                    right_on=col_pedido_src,
                    suffixes=("", "_SRC")
                )
            except Exception:
                df_w_enriched = df_w.copy()

        col_pedido_out = col_pedido_plan
        col_nombre_out = col_nombre_src if (col_nombre_src and col_nombre_src in df_w_enriched.columns) else _pick_col_norm(df_w_enriched, ["NOMBRE_CLIENTE", "nombre_cliente", "cliente", "CLIENTE"])
        col_cel_out = _pick_celular_contacto(df_w_enriched)

        col_dir_src = _pick_col_norm(df_src_base, ["DIRECCION", "direccion"])
        col_fecha_src = _pick_col_norm(df_src_base, ["FECHA_LIMITE_ANS", "fecha_limite_ans"])
        col_dir_out = col_dir_src if (col_dir_src and col_dir_src in df_w_enriched.columns) else _pick_col_norm(df_w_enriched, ["DIRECCION", "direccion"])
        col_fecha_out = col_fecha_src if (col_fecha_src and col_fecha_src in df_w_enriched.columns) else _pick_col_norm(df_w_enriched, ["FECHA_LIMITE_ANS", "fecha_limite_ans"])

        header = (
            f"📌 PLAN CUADRILLA {cid_p}\n"
            f"🏭 Bodega (referencia):Cl 12 Sur # 51B-29. \n"
            f"🧭 Abre el link y toca INICIAR.\n"
            f"✅ Sigue el orden PARADA 1, 2, 3... (orden ANS).\n\n"
        )

        lines = []
        for i, (_, r) in enumerate(df_w_enriched.iterrows(), start=1):
            pedido = _safe(r.get(col_pedido_out)) if col_pedido_out else ""
            nombre = _safe(r.get(col_nombre_out)) if col_nombre_out else ""
            cel = _safe(r.get(col_cel_out)) if col_cel_out else ""
            dire = _safe(r.get(col_dir_out)) if col_dir_out else ""
            fecha = _safe(r.get(col_fecha_out)) if col_fecha_out else ""
            lat_v = _safe(r.get("lat"))
            lng_v = _safe(r.get("lng"))

            nav_link = f"https://www.google.com/maps/dir/?api=1&destination={lat_v},{lng_v}&travelmode=driving" if lat_v and lng_v else ""
            if cel.upper() in ("SIN DATOS", "N/A", "NA", "NONE", "NULL", "0"):
                cel = ""

            lines.append(
                f"PARADA {i}\n"
                f"PEDIDO: {pedido}\n"
                f"NOMBRE_CLIENTE: {nombre}\n"
                f"CELULAR_CONTACTO: {cel}\n"
                f"DIRECCION: {dire}\n"
                f"FECHA_LIMITE_ANS: {fecha}\n"
                + (f"🧭 IR: {nav_link}\n" if nav_link else "")
                + f"---"
            )

        txt_whatsapp = header + "\n".join(lines)
        st.text_area("Copia esto y pégalo en WhatsApp:", value=txt_whatsapp, height=360)

        # ------------------------------
        # Descargas (tu bloque intacto)
        # ------------------------------
        st.markdown("### 🧾 Descargar planillas (PLAN 8×15)")

        all_cols_plan = df_p.columns.tolist()

        esenciales_plan_pref = [
            "ORDEN_VISITA", "route_order",
            "PEDIDO", "pedido",
            "estado", "estado_ans", "prioridad_ans",
            "FECHA_LIMITE_ANS", "fecha_limite_ans",
            "zona_geo", "zona",
            "direccion", "cliente", "actividad",
            "celular_contacto", "celular",
            "lat", "lng", "cuadrilla_id"
        ]

        default_cols_plan = [c for c in all_cols_plan if c in esenciales_plan_pref]
        if not default_cols_plan:
            default_cols_plan = all_cols_plan[:12]

        ss_key_cols_plan = f"cols_sel_plan_{cid_p}"
        if ss_key_cols_plan not in st.session_state:
            st.session_state[ss_key_cols_plan] = default_cols_plan[:]

        pc1, pc2 = st.columns(2)
        with pc1:
            if st.button("✅ Todas (PLAN)", use_container_width=True, key=f"btn_cols_all_plan_{cid_p}"):
                st.session_state[ss_key_cols_plan] = all_cols_plan[:]
                st.session_state[f"print_cols_plan_{cid_p}"] = all_cols_plan[:]
                st.rerun()

        with pc2:
            if st.button("🧹 Vaciar (PLAN)", use_container_width=True, key=f"btn_cols_clear_plan_{cid_p}"):
                st.session_state[ss_key_cols_plan] = []
                st.session_state[f"print_cols_plan_{cid_p}"] = []
                st.rerun()

        key_ms_plan = f"print_cols_plan_{cid_p}"
        if key_ms_plan not in st.session_state:
            st.session_state[key_ms_plan] = st.session_state[ss_key_cols_plan]

        cols_sel_plan = st.multiselect(
            "Elige columnas para imprimir (PLAN)",
            options=all_cols_plan,
            key=key_ms_plan
        )
        st.session_state[ss_key_cols_plan] = cols_sel_plan

        def _filtrar_cols_df(df_in: pd.DataFrame, cols: list) -> pd.DataFrame:
            if not cols:
                return df_in
            cols_ok = [c for c in cols if c in df_in.columns]
            return df_in[cols_ok].copy() if cols_ok else df_in.copy()

        rutas_plan_print = {int(cid): _filtrar_cols_df(dfc, cols_sel_plan) for cid, dfc in plan.items()}
        excel_plan_bytes = exportar_rutas_excel_bytes(rutas_plan_print)

        st.download_button(
            "⬇️ Descargar Excel (PLAN COMPLETO 8×15)",
            data=excel_plan_bytes,
            file_name="plan_diario_8x15.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_excel_plan_completo"
        )

        rutas_plan_1 = {int(cid_p): _filtrar_cols_df(df_p, cols_sel_plan)}
        excel_plan_1_bytes = exportar_rutas_excel_bytes(rutas_plan_1)

        st.download_button(
            f"⬇️ Descargar Excel (PLAN Cuadrilla {cid_p})",
            data=excel_plan_1_bytes,
            file_name=f"plan_cuadrilla_{cid_p}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"dl_excel_plan_{cid_p}"
        )

        try:
            urls_plan = urls_google_maps_cuadrilla_tramos(
                df_p,
                start_lat=bodega_lat,
                start_lng=bodega_lng,
                max_paradas_por_tramo=9,
                travelmode="driving"
            )

            if len(urls_plan) == 1:
                st.link_button(
                    f"🧭 Abrir ruta en Google Maps (PLAN Cuadrilla {cid_p})",
                    urls_plan[0],
                    use_container_width=True
                )
            elif len(urls_plan) > 1:
                st.info(f"📍 Para una mejor visualización, la ruta está organizada en {len(urls_plan)} tramos. Ábrelos en orden.")
                for i, u in enumerate(urls_plan, start=1):
                    st.link_button(
                        f"🧭 Abrir ruta — PLAN TRAMO {i}",
                        u,
                        use_container_width=True
                    )
        except Exception:
            pass
        # ==============================
        # KPIs ejecutivos del PLAN 8x15
        # ==============================
        st.markdown("### 📌 KPIs del Plan Diario")

        total_objetivo_plan = int(n_plan) * int(cap_plan)
        total_asignado_plan = len(df_plan_all)

        pedidos_por_cuadrilla = (
            df_plan_all.groupby("cuadrilla_id")
            .size()
            .reset_index(name="pedidos")
        )

        cuadrillas_completas = int((pedidos_por_cuadrilla["pedidos"] >= int(cap_plan)).sum())

        salud_geo_plan = 0.0
        if total_objetivo_plan > 0:
            salud_geo_plan = (total_asignado_plan / total_objetivo_plan) * 100

        salud_geo_plan_show = min(salud_geo_plan, 100)

        color_salud_plan = "#12B76A" if salud_geo_plan >= 95 else "#F79009" if salud_geo_plan >= 85 else "#D92D20"

        parts_plan = ['<div class="plan-kpi-grid">']

        parts_plan.append(
            f'<div class="plan-kpi-card">'
            f'<div class="plan-kpi-topbar" style="background:#667085;"></div>'
            f'<div class="plan-kpi-head"><div class="plan-kpi-title">🎯 Objetivo 8×15</div></div>'
            f'<div class="plan-kpi-value">{total_objetivo_plan:,}</div>'
            f'<div class="plan-kpi-sub">Capacidad objetivo del plan</div>'
            f'</div>'
        )

        parts_plan.append(
            f'<div class="plan-kpi-card">'
            f'<div class="plan-kpi-topbar" style="background:#2E90FA;"></div>'
            f'<div class="plan-kpi-head"><div class="plan-kpi-title">🚚 Pedidos asignados</div></div>'
            f'<div class="plan-kpi-value">{total_asignado_plan:,}</div>'
            f'<div class="plan-kpi-sub">Pedidos incluidos en la ejecución</div>'
            f'</div>'
        )

        parts_plan.append(
            f'<div class="plan-kpi-card">'
            f'<div class="plan-kpi-topbar" style="background:#F79009;"></div>'
            f'<div class="plan-kpi-head"><div class="plan-kpi-title">✅ Cuadrillas completas</div></div>'
            f'<div class="plan-kpi-value">{cuadrillas_completas}/{int(n_plan)}</div>'
            f'<div class="plan-kpi-sub">Con {int(cap_plan)} pedidos asignados</div>'
            f'</div>'
        )

        parts_plan.append(
            f'<div class="plan-kpi-card">'
            f'<div class="plan-kpi-topbar" style="background:{color_salud_plan};"></div>'
            f'<div class="plan-kpi-head"><div class="plan-kpi-title">🌍 Salud geográfica 8×15</div></div>'
            f'<div class="plan-kpi-value">{salud_geo_plan:.1f}%</div>'
            f'<div class="plan-kpi-sub">Cobertura del plan frente al objetivo</div>'
            f'<div class="plan-kpi-progress">'
            f'<div class="plan-kpi-progress-bar" style="width:{salud_geo_plan_show:.1f}%; background:{color_salud_plan};"></div>'
            f'</div>'
            f'</div>'
        )

        parts_plan.append("</div>")
        st.markdown("".join(parts_plan), unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        st.markdown("### 🗺️ Mapa del Plan ANS")

        rutas_plan = {}
        for cid, dfc in plan.items():
            tmp = dfc.copy()
            if "route_order" not in tmp.columns and "ORDEN_VISITA" in tmp.columns:
                tmp["route_order"] = tmp["ORDEN_VISITA"]
            rutas_plan[int(cid)] = tmp

        cids_plan_map = sorted(list(rutas_plan.keys()))
        opciones_plan_map = ["(Todas)"] + cids_plan_map

        # ✅ si el valor actual ya no existe, lo resetea
        if st.session_state.get("cid_sel_plan_mapa") not in opciones_plan_map:
            st.session_state["cid_sel_plan_mapa"] = "(Todas)"

        cid_sel_plan = st.selectbox(
            "Ver mapa",
            opciones_plan_map,
            key="cid_sel_plan_mapa"
        )

        # ✅ token estable de rerender
        token_now_plan = f"{cid_sel_plan}_{int(bool(respetar_plan_zona))}_{len(rutas_plan)}"
        prev_plan = st.session_state.get("map_render_token_plan")

        if token_now_plan != prev_plan:
            st.session_state["map_render_token_plan"] = token_now_plan

        if cid_sel_plan == "(Todas)":
            rutas_plan_view = rutas_plan
            token_plan = f"{st.session_state['map_render_token_plan']}|ALL_PLAN"
            force_cluster_plan = True
        else:
            rutas_plan_view = {int(cid_sel_plan): rutas_plan[int(cid_sel_plan)]}
            token_plan = f"{st.session_state['map_render_token_plan']}|{cid_sel_plan}"
            force_cluster_plan = False

        m_plan = construir_mapa_rutas(
            rutas_plan_view,
            bodega_lat=bodega_lat,
            bodega_lng=bodega_lng,
            color_mode="estado",
            force_cluster=force_cluster_plan
        )

        html_plan = m_plan.get_root().render()
        html_plan = html_plan.replace(
            "</body>",
            f"<script>window.__plan_map_token='{token_plan}';</script></body>"
        )
        components.html(html_plan, height=650, scrolling=False)
        st.markdown('</div>', unsafe_allow_html=True)
       
# ========= TAB DATOS =========
with tab_datos:
    st.markdown('<div class="section-title">📄 Datos filtrados</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    col_ped_df = _pick_col(df_filtrado, ["PEDIDO", "pedido"])
    pedido_buscar = st.text_input(
        "🔎 Buscar pedido (opcional)",
        value="",
        help="Escribe un pedido para filtrar rápidamente la tabla."
    ).strip()

    df_view = df_filtrado.copy()

    df_asig_general = st.session_state.get("df_asig_general")
    if isinstance(df_asig_general, pd.DataFrame) and len(df_asig_general) > 0 and col_ped_df:
        col_ped_asig = _pick_col(df_asig_general, ["PEDIDO", "pedido"])
        if col_ped_asig and "cuadrilla_id" in df_asig_general.columns:
            map_gen = (
                df_asig_general[[col_ped_asig, "cuadrilla_id"]]
                .dropna()
                .astype({col_ped_asig: str})
                .drop_duplicates(subset=[col_ped_asig])
                .set_index(col_ped_asig)["cuadrilla_id"]
                .to_dict()
            )
            df_view = _insertar_col_despues(
                df_view,
                col_ref=col_ped_df,
                new_col="cuadrilla_general",
                values=(
                    df_view[col_ped_df].astype(str).map(map_gen)
                    .apply(lambda x: "" if pd.isna(x) else str(int(float(x))))
                )
            )

    plan = st.session_state.get("plan_diario")
    if isinstance(plan, dict) and len(plan) > 0 and col_ped_df:
        try:
            df_plan_all2 = pd.concat(plan.values(), ignore_index=True)
            col_ped_plan2 = _pick_col(df_plan_all2, ["PEDIDO", "pedido"])
            if col_ped_plan2 and "cuadrilla_id" in df_plan_all2.columns:
                map_plan = (
                    df_plan_all2[[col_ped_plan2, "cuadrilla_id"]]
                    .dropna()
                    .astype({col_ped_plan2: str})
                    .drop_duplicates(subset=[col_ped_plan2])
                    .set_index(col_ped_plan2)["cuadrilla_id"]
                    .to_dict()
                )
                df_view = _insertar_col_despues(
                    df_view,
                    col_ref=col_ped_df,
                    new_col="cuadrilla_plan",
                    values=(
                        df_view[col_ped_df].astype(str).map(map_plan)
                        .apply(lambda x: "" if pd.isna(x) else str(int(float(x))))
                    )
                )
        except Exception:
            pass

    if pedido_buscar and col_ped_df:
        df_view = df_view[df_view[col_ped_df].astype(str).str.contains(pedido_buscar, na=False)].copy()

    for c in ["cuadrilla_plan", "cuadrilla_general", "cuadrilla_id"]:
        if c in df_view.columns:
            s = pd.to_numeric(df_view[c], errors="coerce").astype("Int64")
            df_view[c] = s.astype(str).replace("<NA>", "")

    st.write(f"Registros: **{len(df_view)}**")
    st.dataframe(df_view, use_container_width=True, height=650)

    st.markdown('</div>', unsafe_allow_html=True)

# ========= TAB DASHBOARD (PRO) =========
with tab_dashboard:
    st.markdown('<div class="section-title">📊 Dashboard Operativo</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    import plotly.express as px

    PLOTLY_CFG = {"displayModeBar": False, "responsive": True}
    CORP_GREEN = "#12B76A"

    df_dash = df_programable.copy()
    df_dash_excl = df_excluidos_rt.copy()

    col_estado    = _pick_col(df_dash, ["estado", "ESTADO"])
    col_zona_geo  = _pick_col(df_dash, ["zona_geo", "ZONA_GEO", "zona", "ZONA"])
    col_actividad = _pick_col(df_dash, ["actividad", "ACTIVIDAD"])
    col_pedido    = _pick_col(df_dash, ["PEDIDO", "pedido"])
    col_cliente   = _pick_col(df_dash, ["CLIENTE", "cliente", "NOMBRE_CLIENTE", "nombre_cliente"])
    col_dir       = _pick_col(df_dash, ["DIRECCION", "direccion"])
    col_fecha     = _pick_col(df_dash, ["FECHA_LIMITE_ANS", "fecha_limite_ans"])

    def _canon_estado_dash(x: str) -> str:
        s = str(x or "").strip().upper()
        if s == "VENCIDO":
            return "VENCIDO"
        if s in ("ALERTA_0", "ALERTA_0 DIAS", "ALERTA 0 DIAS", "ALERTA_0 DÍAS", "ALERTA 0 DÍAS"):
            return "ALERTA_0"
        if s == "ALERTA":
            return "ALERTA"
        if s in ("A TIEMPO", "ATIEMPO"):
            return "A TIEMPO"
        return "SIN FECHA"

    EST_ORDER = ["VENCIDO", "ALERTA_0", "ALERTA", "A TIEMPO", "SIN FECHA"]
    EST_COLORS = {
        "VENCIDO":   "#D92D20",
        "ALERTA_0":  "#F79009",
        "ALERTA":    "#EAAA08",
        "A TIEMPO":  "#12B76A",
        "SIN FECHA": "#2E90FA",
    }

    if col_estado:
        df_dash["_estado_canon"] = df_dash[col_estado].apply(_canon_estado_dash)
    else:
        df_dash["_estado_canon"] = "SIN FECHA"

    total = len(df_dash)
    if total == 0:
        st.info("No hay datos para el dashboard con los filtros actuales.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # -----------------------------
    # ✅ Filtros locales del dashboard (DENTRO del tab)
    # -----------------------------
    st.markdown("### 🎛️ Filtros del dashboard")

    f1, f2, f3 = st.columns([1.25, 1.05, 1.25])

    with f1:
        zona_opts = sorted(df_dash[col_zona_geo].dropna().astype(str).unique().tolist()) if col_zona_geo else []
        zona_local = st.multiselect("ZONA GEO", zona_opts, default=[], key="dash_zona_geo")

    with f2:
        estado_local = st.multiselect("ESTADO", EST_ORDER, default=[], key="dash_estado")

    with f3:
        act_opts = sorted(df_dash[col_actividad].dropna().astype(str).unique().tolist()) if col_actividad else []
        act_local = st.multiselect("ACTIVIDAD", act_opts, default=[], key="dash_actividad")

    if col_zona_geo and zona_local:
        df_dash = df_dash[df_dash[col_zona_geo].astype(str).isin(zona_local)].copy()

    if estado_local:
        df_dash = df_dash[df_dash["_estado_canon"].isin(estado_local)].copy()

    if col_actividad and act_local:
        df_dash = df_dash[df_dash[col_actividad].astype(str).isin(act_local)].copy()

    total = len(df_dash)
    if total == 0:
        st.info("No hay datos en el dashboard con estos filtros locales.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    TOP_N_DEFAULT = 10

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    k_local = _kpi_estado_counts(df_dash)
    render_kpis(k_local)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    urg_mask = df_dash["_estado_canon"].isin(["VENCIDO", "ALERTA_0"])
    urg_cnt = int(urg_mask.sum())
    urg_pct = round((urg_cnt / total) * 100, 1) if total > 0 else 0

    zona_top = ""
    if col_zona_geo and total > 0:
        zona_top = df_dash[col_zona_geo].fillna("SIN ZONA").astype(str).value_counts().index[0]

    act_top = ""
    if col_actividad and total > 0:
        act_top = df_dash[col_actividad].fillna("SIN ACTIVIDAD").astype(str).value_counts().index[0]

    excluidos_total = len(df_dash_excl)

    excl_urg_cnt = 0
    if len(df_dash_excl) > 0:
        col_estado_excl = _pick_col(df_dash_excl, ["estado", "ESTADO"])
        if col_estado_excl:
            est_excl = df_dash_excl[col_estado_excl].fillna("").astype(str).str.strip().str.upper()
            excl_urg_cnt = int(
                est_excl.isin(["VENCIDO", "ALERTA_0", "ALERTA_0 DIAS", "ALERTA 0 DIAS", "ALERTA_0 DÍAS", "ALERTA 0 DÍAS"]).sum()
            )

    st.markdown(
        f"""
        <div class="card" style="border-left:6px solid #214D12; margin-top:6px;">
        <div style="font-weight:950; font-size:14px; color:#0F172A;">📌 Resumen Operativo</div>
        <div style="margin-top:8px; color:rgba(15,23,42,.78); font-size:13px; line-height:1.5;">
            • <b>{urg_cnt:,}</b> urgentes operativos reales (<b>{urg_pct}%</b>) en <b>VENCIDO</b> + <b>ALERTA_0</b><br>
            • <b>{excluidos_total:,}</b> pedidos con <b>REPORTE_TECNICO</b> ya registrado fueron excluidos de programación<br>
            • <b>{excl_urg_cnt:,}</b> urgentes no fueron programados por presentar reporte técnico<br>
            • Zona más cargada: <b>{zona_top}</b><br>
            • Actividad más repetida: <b>{act_top}</b><br>
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    dtab1, dtab2, dtab3, dtab4 = st.tabs([
        "📌 ANS (Estados)",
        "🧭 Zonas",
        "🧩 Actividades",
        "🧱 Estados por zona"
    ])

    with dtab1:
        c1, c2 = st.columns(2, gap="small")

        e = (
            df_dash["_estado_canon"].value_counts()
            .reindex(EST_ORDER, fill_value=0)
            .reset_index()
        )
        e.columns = ["estado", "pedidos"]
        e["%"] = (e["pedidos"] / total * 100).round(1)

        with c1:
            st.markdown("#### 🍩 % por estado (ANS)")
            e_pie = e[e["pedidos"] > 0].copy()
            fig_pie = px.pie(
                e_pie,
                names="estado",
                values="pedidos",
                hole=0.60,
                color="estado",
                color_discrete_map=EST_COLORS
            )
            fig_pie.update_traces(textinfo="percent", textposition="inside")
            fig_pie.update_layout(height=330, margin=dict(l=12, r=12, t=18, b=12), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_CFG)

        with c2:
            st.markdown("#### 🚦 Estado (conteo)")
            e_sorted = e.sort_values("pedidos", ascending=False).copy()
            order_estados = e_sorted["estado"].tolist()

            fig_e = px.bar(
                e_sorted,
                x="estado",
                y="pedidos",
                color="estado",
                color_discrete_map=EST_COLORS,
                text="pedidos",
                category_orders={"estado": order_estados}
            )

            fig_e.update_traces(textposition="outside", cliponaxis=False)

            fig_e.update_layout(
                height=330,
                margin=dict(l=12, r=12, t=18, b=12),
                showlegend=False,
                yaxis_title=None,
                xaxis_title=None
            )

            fig_e.update_yaxes(
                visible=False,
                showticklabels=False,
                showgrid=False,
                zeroline=False,
                title_text=None
            )

            st.plotly_chart(fig_e, use_container_width=True, config=PLOTLY_CFG)    

    with dtab2:
        st.markdown("#### 🧭 Top zonas (zona_geo)")
        if col_zona_geo:
            z = (
                df_dash[col_zona_geo].fillna("SIN ZONA").astype(str)
                .value_counts().head(TOP_N_DEFAULT).reset_index()
            )
            z.columns = ["zona_geo", "pedidos"]
            z["%"] = (z["pedidos"] / total * 100).round(1)

            fig_z = px.bar(
                z.sort_values("pedidos", ascending=True),
                x="pedidos",
                y="zona_geo",
                orientation="h",
                text=z.sort_values("pedidos", ascending=True)["%"].astype(str) + "%",
                labels={"zona_geo": "Zona geográfica", "pedidos": "Pedidos"}
            )
            fig_z.update_traces(marker_color=CORP_GREEN)
            fig_z.update_traces(textposition="inside", insidetextanchor="middle")
            fig_z.update_xaxes(visible=False)
            fig_z.update_layout(height=400, margin=dict(l=12, r=12, t=18, b=12), showlegend=False, xaxis_title=None
            )
            st.plotly_chart(fig_z, use_container_width=True, config=PLOTLY_CFG)
        else:
            st.info("No existe la columna zona_geo.")

    with dtab3:
        st.markdown("#### 🧩 Top actividades")
        if col_actividad:
            a = (
                df_dash[col_actividad].fillna("SIN ACTIVIDAD").astype(str)
                .value_counts().head(TOP_N_DEFAULT).reset_index()
            )
            a.columns = ["Actividad", "pedidos"]
            a["%"] = (a["pedidos"] / total * 100).round(1)

            fig_a = px.bar(
                a.sort_values("pedidos", ascending=True),
                x="pedidos",
                y="Actividad",
                orientation="h",
                text=a.sort_values("pedidos", ascending=True)["%"].astype(str) + "%"
            )
            fig_a.update_traces(marker_color=CORP_GREEN)
            fig_a.update_traces(textposition="inside", insidetextanchor="middle")
            fig_a.update_xaxes(visible=False)
            fig_a.update_layout(height=440, margin=dict(l=12, r=12, t=18, b=12), showlegend=False)
            st.plotly_chart(fig_a, use_container_width=True, config=PLOTLY_CFG)
        else:
            st.info("No existe la columna actividad.")

    with dtab4:
        st.markdown("#### 🧱 Estados por zona")
        if col_zona_geo:
            tmp = df_dash.copy()
            tmp["_zona"] = tmp[col_zona_geo].fillna("SIN ZONA").astype(str)
            tmp["_est"] = tmp["_estado_canon"]

            grp = tmp.groupby(["_zona", "_est"]).size().reset_index(name="pedidos")

            top_zonas = tmp["_zona"].value_counts().head(TOP_N_DEFAULT).index.tolist()
            grp = grp[grp["_zona"].isin(top_zonas)]

            fig_stack = px.bar(
                grp,
                x="_zona",
                y="pedidos",
                color="_est",
                color_discrete_map=EST_COLORS,
                barmode="stack",
                labels={
                    "_zona": "Zona geográfica",
                    "_est": "Estado",
                    "pedidos": "Pedidos" 
                }
            )
            fig_stack.update_layout(
                height=440,
                margin=dict(l=12, r=12, t=18, b=12),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
                xaxis_title=None,
                yaxis_title=None,
            )
            fig_stack.update_yaxes(showticklabels=False, showgrid=False, zeroline=False)
            fig_stack.update_xaxes(showgrid=False, zeroline=False)
            st.plotly_chart(fig_stack, use_container_width=True, config=PLOTLY_CFG)
        else:
            st.info("No existe la columna zona_geo.")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("### 📋 Detalle operativo (VENCIDO + ALERTA_0)")

    urg = df_dash[urg_mask].copy()
    if col_fecha and col_fecha in urg.columns:
        urg["_fecha"] = pd.to_datetime(urg[col_fecha], errors="coerce")
        urg = urg.sort_values("_fecha", ascending=True, na_position="last").drop(columns=["_fecha"], errors="ignore")

    cols_show = []
    for c in [col_pedido, col_cliente, col_dir, col_zona_geo, col_actividad, col_fecha, col_estado]:
        if c and c in urg.columns and c not in cols_show:
            cols_show.append(c)

    urg_view = urg[cols_show].head(50) if cols_show else urg.head(50)
    st.dataframe(urg_view, use_container_width=True, height=520)

    df_dash.drop(columns=["_estado_canon"], errors="ignore", inplace=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ========= TAB CENTRO DE CONTROL ANS =========
with tab_cc_ans:
    try:
        plan = st.session_state.get("plan_diario")

        if not plan:
            st.info("Primero debes generar el Plan Diario ANS para alimentar el Centro de Control.")
        else:
            df_plan_base = pd.concat(plan.values(), ignore_index=True)
            df_corte_actual = df_programable.copy()

            df_seguimiento = construir_seguimiento_plan(df_plan_base, df_corte_actual)
            resumen = resumir_seguimiento(df_seguimiento)

            render_centro_control_ans(df_seguimiento, resumen)

    except Exception as e:
        st.error("No se pudo cargar el módulo Centro de Control ANS.")
        st.exception(e)

# ========= TAB MANUAL =========
with tab_manual:
    st.markdown('<div class="section-title">📘 Manual de Usuario</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    # ✅ Ruta absoluta al archivo (no depende de dónde ejecutes streamlit)
    BASE_DIR = Path(__file__).resolve().parent
    RUTA_IMG = BASE_DIR / "assets" / "Flujo_de_trabajo_v5.png"

    try:
        manual_text = _leer_manual_md()

        # Dividimos el texto en dos partes usando el marcador
        partes = manual_text.split("[[IMAGEN_FLUJO]]")

        # Parte antes de la imagen
        st.markdown(partes[0], unsafe_allow_html=False)

        # 👇 Imagen centrada (si existe). Si no existe, NO rompe el manual.
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            if RUTA_IMG.exists():
                st.image(str(RUTA_IMG), width=900)
            else:
                st.warning(f"No se encontró la imagen: {RUTA_IMG}")

        # Parte después de la imagen
        if len(partes) > 1:
            st.markdown(partes[1], unsafe_allow_html=False)

    except Exception as e:
        st.warning(f"No se pudo cargar el manual: {e}")

    st.markdown('</div>', unsafe_allow_html=True)