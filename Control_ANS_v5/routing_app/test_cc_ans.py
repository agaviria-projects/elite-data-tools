import pandas as pd

from src.cc_ans_metrics import construir_seguimiento_plan, resumir_seguimiento


# =========================
# PLAN BASE SIMULADO
# =========================
df_plan = pd.DataFrame([
    {
        "id_pedido": "12345678",
        "zona": "NORTE",
        "ans_limite": "2026-03-09 14:00:00",
        "estado_inicial": "PENDIENTE"
    },
    {
        "id_pedido": "22222222",
        "zona": "SUR",
        "ans_limite": "2026-03-09 18:00:00",
        "estado_inicial": "PENDIENTE"
    },
    {
        "id_pedido": "33333333",
        "zona": "CENTRO",
        "ans_limite": "2026-03-09 10:00:00",
        "estado_inicial": "PENDIENTE"
    },
    {
        "id_pedido": "44444444",
        "zona": "OCCIDENTE",
        "ans_limite": "",
        "estado_inicial": "PENDIENTE"
    }
])


# =========================
# CORTE ACTUAL SIMULADO
# =========================
df_corte = pd.DataFrame([
    {
        "PEDIDO": "12345678",
        "zona": "NORTE",
        "estado": "PENDIENTE",
        "MARCA_TEMPORAL": "2026-03-09 11:42:00",
        "REPORTE_TECNICO": "SIN DATO",
        "FECHA_LIMITE_ANS": "2026-03-09 14:00:00"
    },
    {
        "PEDIDO": "22222222",
        "zona": "SUR",
        "estado": "PENDIENTE",
        "MARCA_TEMPORAL": "SIN DATO",
        "REPORTE_TECNICO": "EFECTIVO PARA HV",
        "FECHA_LIMITE_ANS": "2026-03-09 18:00:00"
    },
    {
        "PEDIDO": "33333333",
        "zona": "CENTRO",
        "estado": "PENDIENTE",
        "MARCA_TEMPORAL": "SIN DATO",
        "REPORTE_TECNICO": "SIN DATO",
        "FECHA_LIMITE_ANS": "2026-03-09 10:00:00"
    }
])


# =========================
# EJECUCIÓN DE PRUEBA
# =========================
ahora_prueba = pd.Timestamp("2026-03-09 12:00:00")

df_seg = construir_seguimiento_plan(
    df_plan_base=df_plan,
    df_corte_actual=df_corte,
    ahora=ahora_prueba
)

resumen = resumir_seguimiento(df_seg)

print("\n=== SEGUIMIENTO DETALLADO ===")
print(df_seg)

print("\n=== RESUMEN ===")
print(resumen)