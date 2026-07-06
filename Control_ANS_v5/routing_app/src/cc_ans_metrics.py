# src/cc_ans_metrics.py

from __future__ import annotations

from typing import Optional
import pandas as pd


def _normalizar_texto(valor) -> str:
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def _pick_col(df: pd.DataFrame, candidatos: list[str]) -> Optional[str]:
    if df is None or df.empty:
        return None

    mapa = {str(c).strip().upper(): c for c in df.columns}
    for cand in candidatos:
        key = str(cand).strip().upper()
        if key in mapa:
            return mapa[key]
    return None


def _tiene_dato_real(valor) -> bool:
    txt = _normalizar_texto(valor).upper()
    return txt not in {"", "SIN DATO", "NAN", "NONE", "NULL", "N/A", "NA"}


def _calcular_nivel_riesgo(ans_limite, ahora: Optional[pd.Timestamp] = None) -> str:
    """
    Clasificación simple del riesgo ANS según cercanía al vencimiento.
    """
    if ahora is None:
        ahora = pd.Timestamp.now()

    fecha_ans = pd.to_datetime(ans_limite, errors="coerce")
    if pd.isna(fecha_ans):
        return "SIN_FECHA"

    horas_restantes = (fecha_ans - ahora).total_seconds() / 3600

    if horas_restantes <= 0:
        return "CRITICO"
    if horas_restantes <= 2:
        return "ALTO"
    if horas_restantes <= 6:
        return "MEDIO"
    return "BAJO"


def construir_seguimiento_plan(
    df_plan_base: pd.DataFrame,
    df_corte_actual: pd.DataFrame,
    ahora: Optional[pd.Timestamp] = None
) -> pd.DataFrame:
    """
    Cruza el plan base con el corte actual (Google Sheets / formulario técnico)
    y construye el seguimiento operativo.
    """
    if df_plan_base is None or df_plan_base.empty:
        return pd.DataFrame()

    if df_corte_actual is None:
        df_corte_actual = pd.DataFrame()

    # -------------------------
    # Columnas del plan base
    # -------------------------
    col_plan_pedido = _pick_col(df_plan_base, ["id_pedido", "PEDIDO", "pedido"])
    col_plan_zona = _pick_col(df_plan_base, ["zona", "ZONA", "zona_geo", "ZONA_GEO"])
    col_plan_ans = _pick_col(df_plan_base, ["ans_limite", "FECHA_LIMITE_ANS", "fecha_limite_ans"])
    col_plan_estado = _pick_col(df_plan_base, ["estado_inicial", "estado", "ESTADO"])

    if not col_plan_pedido:
        raise ValueError("El plan base no tiene columna id_pedido / PEDIDO.")

    # -------------------------
    # Columnas del corte actual (Google Sheets)
    # -------------------------
    col_corte_pedido = _pick_col(df_corte_actual, ["Número del Pedido", "NUMERO DEL PEDIDO", "PEDIDO", "pedido", "id_pedido"])
    col_corte_marca = _pick_col(df_corte_actual, ["Marca temporal", "MARCA_TEMPORAL", "marca_temporal"])
    col_corte_tecnico = _pick_col(df_corte_actual, ["Nombre del Técnico", "NOMBRE DEL TECNICO", "nombre_tecnico"])
    col_corte_estado_campo = _pick_col(df_corte_actual, ["Estado del Pedido", "ESTADO DEL PEDIDO", "estado_pedido", "estado_actual_campo"])
    col_corte_actividad = _pick_col(df_corte_actual, ["Actividad", "ACTIVIDAD", "actividad"])

    # -------------------------
    # Preparar plan base
    # -------------------------
    plan = df_plan_base.copy()
    plan["id_pedido"] = plan[col_plan_pedido].astype(str).str.strip()

    plan_view = pd.DataFrame({
        "id_pedido": plan["id_pedido"],
        "zona_plan": plan[col_plan_zona] if col_plan_zona else "",
        "ans_limite_plan": plan[col_plan_ans] if col_plan_ans else "",
        "estado_inicial": plan[col_plan_estado] if col_plan_estado else "",
    })

    # -------------------------
    # Si no hay corte o no hay columna pedido en corte
    # -------------------------
    if df_corte_actual.empty or not col_corte_pedido:
        out = plan_view.copy()
        out["zona_actual"] = out["zona_plan"]
        out["reportado_tecnico"] = 0
        out["estado_actual_campo"] = "SIN_REPORTE"
        out["nombre_tecnico"] = ""
        out["marca_temporal"] = ""
        out["actividad_campo"] = ""
        out["nivel_riesgo"] = out["ans_limite_plan"].apply(lambda x: _calcular_nivel_riesgo(x, ahora=ahora))
        return out

    # -------------------------
    # Preparar corte actual
    # -------------------------
    corte = df_corte_actual.copy()
    corte["id_pedido"] = corte[col_corte_pedido].astype(str).str.strip()

    # Dejar una fila por pedido; si hay varios reportes, toma el último
    corte = corte.drop_duplicates(subset=["id_pedido"], keep="last")

    corte_view = pd.DataFrame({
        "id_pedido": corte["id_pedido"],
        "nombre_tecnico": corte[col_corte_tecnico] if col_corte_tecnico else "",
        "marca_temporal": corte[col_corte_marca] if col_corte_marca else "",
        "estado_actual_campo": corte[col_corte_estado_campo] if col_corte_estado_campo else "",
        "actividad_campo": corte[col_corte_actividad] if col_corte_actividad else "",
    })

    # -------------------------
    # Cruce plan vs corte
    # -------------------------
    df_merge = plan_view.merge(corte_view, on="id_pedido", how="left")

    df_merge["zona_actual"] = df_merge["zona_plan"]

    # Si no aparece en el formulario, no ha sido reportado
    df_merge["reportado_tecnico"] = df_merge["marca_temporal"].apply(lambda x: 1 if _tiene_dato_real(x) else 0)

    # Ajuste más robusto:
    # si no tiene marca temporal pero sí nombre técnico o estado de campo, también cuenta como reportado
    mask_reportado = (
        df_merge["marca_temporal"].apply(_tiene_dato_real) |
        df_merge["nombre_tecnico"].apply(_tiene_dato_real) |
        df_merge["estado_actual_campo"].apply(_tiene_dato_real)
    )
    df_merge["reportado_tecnico"] = mask_reportado.astype(int)

    # Estado de campo
    df_merge["estado_actual_campo"] = df_merge["estado_actual_campo"].fillna("").astype(str).str.strip()
    df_merge.loc[df_merge["reportado_tecnico"] == 0, "estado_actual_campo"] = "SIN_REPORTE"

    # Completar vacíos
    df_merge["nombre_tecnico"] = df_merge["nombre_tecnico"].fillna("").astype(str).str.strip()
    df_merge["marca_temporal"] = df_merge["marca_temporal"].fillna("").astype(str).str.strip()
    df_merge["actividad_campo"] = df_merge["actividad_campo"].fillna("").astype(str).str.strip()

    # Riesgo
    df_merge["nivel_riesgo"] = df_merge["ans_limite_plan"].apply(lambda x: _calcular_nivel_riesgo(x, ahora=ahora))

    salida = df_merge[[
        "id_pedido",
        "zona_actual",
        "reportado_tecnico",
        "estado_actual_campo",
        "nombre_tecnico",
        "marca_temporal",
        "actividad_campo",
        "nivel_riesgo"
    ]].copy()

    return salida


def resumir_seguimiento(df_seguimiento: pd.DataFrame) -> dict:
    """
    Resume métricas clave del seguimiento.
    """
    if df_seguimiento is None or df_seguimiento.empty:
        return {
            "total_plan": 0,
            "reportados": 0,
            "sin_reporte": 0,
            "pct_reporte": 0.0,
            "criticos": 0,
        }

    total_plan = len(df_seguimiento)
    reportados = int(df_seguimiento["reportado_tecnico"].sum())
    sin_reporte = total_plan - reportados
    pct_reporte = round((reportados / total_plan) * 100, 1) if total_plan > 0 else 0.0
    criticos = int((df_seguimiento["nivel_riesgo"] == "CRITICO").sum())

    return {
        "total_plan": total_plan,
        "reportados": reportados,
        "sin_reporte": sin_reporte,
        "pct_reporte": pct_reporte,
        "criticos": criticos,
    }