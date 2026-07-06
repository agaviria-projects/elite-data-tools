import streamlit as st
import pandas as pd

from src.cc_ans_ui import render_centro_control_ans
from src.cc_ans_metrics import construir_seguimiento_plan, resumir_seguimiento


st.set_page_config(page_title="Test Centro de Control ANS", layout="wide")

# =========================
# PLAN BASE SIMULADO
# =========================
df_plan = pd.DataFrame([
    {"id_pedido": "12345678", "zona": "NORTE",     "ans_limite": "2026-03-09 14:00:00", "estado_inicial": "PENDIENTE"},
    {"id_pedido": "22222222", "zona": "SUR",       "ans_limite": "2026-03-09 18:00:00", "estado_inicial": "PENDIENTE"},
    {"id_pedido": "33333333", "zona": "CENTRO",    "ans_limite": "2026-03-09 10:00:00", "estado_inicial": "PENDIENTE"},
    {"id_pedido": "44444444", "zona": "OCCIDENTE", "ans_limite": "",                    "estado_inicial": "PENDIENTE"},
])

# =========================
# CORTE ACTUAL SIMULADO
# (Google Sheets / Formulario técnico)
# =========================
df_corte = pd.DataFrame([
    {
        "Número del Pedido": "12345678",
        "Marca temporal": "2026-03-09 11:42:00",
        "Nombre del Técnico": "Juan Guillermo Ramirez Camacho",
        "Actividad": "ALEGA-(LEGALIZACION RESIDENCIAL)",
        "Estado del Pedido": "Descartado"
    },
    {
        "Número del Pedido": "22222222",
        "Marca temporal": "2026-03-09 12:05:00",
        "Nombre del Técnico": "Yoryi Estiven Sepulveda Castro",
        "Actividad": "ALEGN-(LEGALIZACION NO RESIDENCIAL)",
        "Estado del Pedido": "Ejecutado en Campo"
    }
])

ahora_prueba = pd.Timestamp("2026-03-09 12:00:00")

df_seg = construir_seguimiento_plan(
    df_plan_base=df_plan,
    df_corte_actual=df_corte,
    ahora=ahora_prueba
)

resumen = resumir_seguimiento(df_seg)

render_centro_control_ans(df_seg, resumen)