# src/cc_ans_repository.py

from __future__ import annotations

from typing import Optional
import pandas as pd

from src.cc_ans_db import conectar_db


def _normalizar_texto(valor) -> str:
    """
    Convierte nulos a cadena vacía y limpia espacios.
    """
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def _pick_col(df: pd.DataFrame, candidatos: list[str]) -> Optional[str]:
    """
    Busca una columna por nombre, ignorando mayúsculas/minúsculas.
    """
    if df is None or df.empty:
        return None

    mapa = {str(c).strip().upper(): c for c in df.columns}
    for cand in candidatos:
        key = str(cand).strip().upper()
        if key in mapa:
            return mapa[key]
    return None


def registrar_plan_base(
    df_plan: pd.DataFrame,
    fecha_operacion: str,
    marca_plan: str
) -> int:
    """
    Guarda el plan base del día en SQLite.
    Retorna la cantidad de registros insertados.
    """
    if df_plan is None or df_plan.empty:
        return 0

    col_pedido = _pick_col(df_plan, ["PEDIDO", "id_pedido", "pedido"])
    col_zona = _pick_col(df_plan, ["zona", "ZONA", "zona_geo", "ZONA_GEO"])
    col_cuadrilla = _pick_col(df_plan, ["cuadrilla_id", "CUADRILLA_ID", "cuadrilla", "CUADRILLA"])
    col_ans = _pick_col(df_plan, ["FECHA_LIMITE_ANS", "fecha_limite_ans", "ANS_Limite", "ans_limite"])
    col_estado = _pick_col(df_plan, ["estado", "ESTADO", "estado_inicial"])

    if not col_pedido:
        raise ValueError("No se encontró la columna PEDIDO en el plan base.")

    conn = conectar_db()
    cur = conn.cursor()

    rows_insertadas = 0

    for _, row in df_plan.iterrows():
        id_pedido = _normalizar_texto(row.get(col_pedido))
        if not id_pedido:
            continue

        zona = _normalizar_texto(row.get(col_zona)) if col_zona else ""
        cuadrilla = _normalizar_texto(row.get(col_cuadrilla)) if col_cuadrilla else ""
        ans_limite = _normalizar_texto(row.get(col_ans)) if col_ans else ""
        estado_inicial = _normalizar_texto(row.get(col_estado)) if col_estado else ""

        cur.execute("""
            INSERT OR REPLACE INTO plan_base_diario (
                fecha_operacion,
                id_pedido,
                zona,
                cuadrilla,
                ans_limite,
                estado_inicial,
                marca_plan
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fecha_operacion,
            id_pedido,
            zona,
            cuadrilla,
            ans_limite,
            estado_inicial,
            marca_plan
        ))
        rows_insertadas += 1

    conn.commit()
    conn.close()
    return rows_insertadas


def registrar_corte(
    fecha_operacion: str,
    tipo_corte: str,
    marca_corte: str,
    archivo_nombre: str,
    total_registros: int
) -> int:
    """
    Registra el corte cargado y devuelve su id_corte.
    """
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO cortes_operacion (
            fecha_operacion,
            tipo_corte,
            marca_corte,
            archivo_nombre,
            total_registros
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        fecha_operacion,
        tipo_corte,
        marca_corte,
        archivo_nombre,
        int(total_registros)
    ))

    id_corte = cur.lastrowid
    conn.commit()
    conn.close()

    return int(id_corte)


def leer_plan_base(fecha_operacion: str) -> pd.DataFrame:
    """
    Lee el plan base guardado para una fecha.
    """
    conn = conectar_db()

    df = pd.read_sql_query("""
        SELECT
            fecha_operacion,
            id_pedido,
            zona,
            cuadrilla,
            ans_limite,
            estado_inicial,
            marca_plan
        FROM plan_base_diario
        WHERE fecha_operacion = ?
        ORDER BY cuadrilla, id_pedido
    """, conn, params=(fecha_operacion,))

    conn.close()
    return df


def guardar_seguimiento(
    df_seguimiento: pd.DataFrame,
    id_corte: int,
    fecha_operacion: str
) -> int:
    """
    Guarda el seguimiento calculado del plan frente a un corte.
    Retorna la cantidad de filas insertadas.
    """
    if df_seguimiento is None or df_seguimiento.empty:
        return 0

    conn = conectar_db()
    cur = conn.cursor()

    filas = 0

    for _, row in df_seguimiento.iterrows():
        cur.execute("""
            INSERT INTO seguimiento_plan (
                id_corte,
                fecha_operacion,
                id_pedido,
                zona_actual,
                estado_actual,
                marca_temporal,
                reporte_tecnico,
                cumple_visita,
                fuente_visita,
                nivel_riesgo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(id_corte),
            fecha_operacion,
            _normalizar_texto(row.get("id_pedido")),
            _normalizar_texto(row.get("zona_actual")),
            _normalizar_texto(row.get("estado_actual")),
            _normalizar_texto(row.get("marca_temporal")),
            _normalizar_texto(row.get("reporte_tecnico")),
            int(row.get("cumple_visita", 0) or 0),
            _normalizar_texto(row.get("fuente_visita")),
            _normalizar_texto(row.get("nivel_riesgo"))
        ))
        filas += 1

    conn.commit()
    conn.close()
    return filas


def leer_ultimo_seguimiento(fecha_operacion: str) -> pd.DataFrame:
    """
    Devuelve el seguimiento más reciente de la fecha consultada.
    """
    conn = conectar_db()

    df = pd.read_sql_query("""
        SELECT sp.*
        FROM seguimiento_plan sp
        INNER JOIN (
            SELECT MAX(id_corte) AS id_corte_max
            FROM cortes_operacion
            WHERE fecha_operacion = ?
        ) u
        ON sp.id_corte = u.id_corte_max
        WHERE sp.fecha_operacion = ?
        ORDER BY sp.id_pedido
    """, conn, params=(fecha_operacion, fecha_operacion))

    conn.close()
    return df