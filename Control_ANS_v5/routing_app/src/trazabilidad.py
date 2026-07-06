import pandas as pd

# ---------------------------------------------------------
# Helpers: normalización de estados y prioridad ANS
# ---------------------------------------------------------
def _canon_estado_ans(x: str) -> str:
    s = str(x or "").strip().upper()

    if s in ("VENCIDO",):
        return "VENCIDO"

    if s in ("ALERTA_0", "ALERTA_0 DIAS", "ALERTA 0 DIAS", "ALERTA_0 DÍAS", "ALERTA 0 DÍAS"):
        return "ALERTA_0"

    if s in ("ALERTA",):
        return "ALERTA"

    if s in ("A TIEMPO", "ATIEMPO"):
        return "A TIEMPO"

    return "SIN FECHA"  # fallback (o desconocido)


def _prio_estado_ans(canon: str) -> int:
    # Menor = más urgente
    orden = {
        "VENCIDO": 1,
        "ALERTA_0": 2,
        "ALERTA": 3,
        "A TIEMPO": 4,
        "SIN FECHA": 99
    }
    return orden.get(canon, 99)


# ---------------------------------------------------------
# Priorización ANS (TOP por zona) - sin depender de otros módulos
# ---------------------------------------------------------
_PRIORIDAD_ANS = {
    "VENCIDO": 1,
    "ALERTA_0": 2,
    "ALERTA_0 DÍAS": 2,
    "ALERTA_0 DIAS": 2,
    "ALERTA": 3,
    "A TIEMPO": 4,
    "SIN FECHA": 99,
}


def top_urgentes_por_zona(
    df: pd.DataFrame,
    n_por_zona: int = 15,
    col_pedido: str = "PEDIDO",
    col_estado: str = "ESTADO_ANS",
    col_fecha_limite: str = "FECHA_LIMITE_ANS",
    col_zona: str = "ZONA_GEO",
) -> pd.DataFrame:
    """
    Selecciona TOP N por zona respetando:
    1) Estado (VENCIDO, ALERTA_0, ALERTA, A TIEMPO)
    2) FECHA_LIMITE_ANS asc (NaT al final)
    3) PEDIDO como clave única
    """
    if df is None or df.empty:
        return df

    d = df.copy()

    # columnas mínimas
    for c in [col_pedido, col_estado]:
        if c not in d.columns:
            return df

    d[col_pedido] = d[col_pedido].astype(str).str.strip()
    d[col_estado] = d[col_estado].astype(str).str.strip().str.upper()

    # fecha
    if col_fecha_limite in d.columns:
        d[col_fecha_limite] = pd.to_datetime(d[col_fecha_limite], errors="coerce")
    else:
        d[col_fecha_limite] = pd.NaT

    # prioridad
    d["_prio_ans"] = d[col_estado].map(_PRIORIDAD_ANS).fillna(999).astype(int)

    # clave única
    d = d.drop_duplicates(subset=[col_pedido], keep="first")

    # si no hay zona, top global
    if col_zona not in d.columns:
        out = (
            d.sort_values(by=["_prio_ans", col_fecha_limite], ascending=[True, True], na_position="last")
             .head(n_por_zona)
             .drop(columns=["_prio_ans"], errors="ignore")
        )
        return out

    d[col_zona] = d[col_zona].fillna("").astype(str).str.strip()

    partes = []
    for _, g in d.groupby(col_zona, dropna=False):
        g2 = (
            g.sort_values(by=["_prio_ans", col_fecha_limite], ascending=[True, True], na_position="last")
             .head(n_por_zona)
        )
        partes.append(g2)

    out = pd.concat(partes, ignore_index=True) if partes else d.head(n_por_zona)
    out = out.drop(columns=["_prio_ans"], errors="ignore")
    return out


# ---------------------------------------------------------
# FUNCIÓN PRINCIPAL: Plan Diario 8×15 (o N×cap)
# ---------------------------------------------------------
def plan_diario_8x15(
    df_in: pd.DataFrame,
    n_cuadrillas: int = 8,
    cap_por_cuadrilla: int = 15,
    origen_lat: float = 0.0,
    origen_lng: float = 0.0,
    col_pedido: str = "PEDIDO",
    col_estado: str = "estado",
    col_fecha_limite: str = "FECHA_LIMITE_ANS",
    col_zona_geo: str = "zona_geo",
    col_lat: str = "lat",
    col_lng: str = "lng",
    respetar_zona_geo: bool = True,
):
    """
    Retorna dict: {cuadrilla_id: df_plan_cuadrilla}
    df_plan_cuadrilla incluye:
      - cuadrilla_id
      - estado_ans (canon)
      - prioridad_ans (int)
      - ORDEN_VISITA (1..N)
    """

    if df_in is None or df_in.empty:
        return {}

    df = df_in.copy()

    # ---------------------------------------------------------
    # BLINDAJE: alias de columnas (no rompe flujo)
    # ---------------------------------------------------------
    # Normaliza nombres (trim) para evitar "PEDIDO " con espacios
    df.columns = [str(c).strip() for c in df.columns]

    # Alias comunes -> nombre estándar
    alias_pedido = ["PEDIDO", "Pedido", "pedido", "No_Pedido", "NRO_PEDIDO", "NUM_PEDIDO", "OT", "Orden", "ORDEN"]
    alias_lat = ["lat", "LAT", "Lat", "COORDENADAY", "LATITUD", "Latitud"]
    alias_lng = ["lng", "LNG", "Lng", "COORDENADAX", "LONGITUD", "Longitud"]

    def _first_present(cands):
        for c in cands:
            if c in df.columns:
                return c
        return None

    c_pedido = _first_present(alias_pedido)
    c_lat = _first_present(alias_lat)
    c_lng = _first_present(alias_lng)

    # Si tu función está esperando col_pedido/col_lat/col_lng pero el df trae otro nombre,
    # reasignamos SOLO las variables (no renombramos el df completo)
    if c_pedido is not None and col_pedido not in df.columns:
        col_pedido = c_pedido
    if c_lat is not None and col_lat not in df.columns:
        col_lat = c_lat
    if c_lng is not None and col_lng not in df.columns:
        col_lng = c_lng

    # --- Validaciones mínimas
    for c in (col_pedido, col_lat, col_lng):
        if c not in df.columns:
            raise ValueError(f"Falta columna requerida: {c}")

    # estado y fecha pueden venir con otro casing
    if col_estado not in df.columns:
        df[col_estado] = ""

    if col_fecha_limite not in df.columns:
        df[col_fecha_limite] = None

    # --- lat/lng válidos
    df[col_lat] = pd.to_numeric(df[col_lat], errors="coerce")
    df[col_lng] = pd.to_numeric(df[col_lng], errors="coerce")
    df = df.dropna(subset=[col_lat, col_lng]).copy()
    if df.empty:
        return {}

    # --- Canon + prioridad
    df["estado_ans"] = df[col_estado].apply(_canon_estado_ans)
    df["prioridad_ans"] = df["estado_ans"].apply(_prio_estado_ans)

    # --- fecha límite a datetime (NaT al final)
    df["_fecha_limite_dt"] = pd.to_datetime(df[col_fecha_limite], errors="coerce")

    # --- total requerido
    total_req = int(n_cuadrillas) * int(cap_por_cuadrilla)

    # --- orden base: prioridad + fecha límite asc
    df = df.sort_values(
        by=["prioridad_ans", "_fecha_limite_dt"],
        ascending=[True, True],
        na_position="last"
    ).copy()

    plan = {}

    # IMPORTANTE:
    # Para evitar imports circulares, NO importamos desde src.trazabilidad dentro de este archivo.
    # Asumimos que estas funciones existen en otros módulos:
    # - asignar_cuadrillas_kmeans en src.clustering
    # - ordenar_nearest_neighbor_por_bloques en src.routing
    from src.clustering import asignar_cuadrillas_kmeans
    from src.routing import ordenar_nearest_neighbor_por_bloques

    # ==========================================================
    # CONSTRUCCIÓN BASE DEL PLAN
    # ==========================================================

    # ---------------------------------------------------------
    # Caso 1: Respetar zona_geo (no mezclar)
    # ---------------------------------------------------------
    if respetar_zona_geo and (col_zona_geo in df.columns):
        df[col_zona_geo] = df[col_zona_geo].fillna("").astype(str).str.strip()
        zonas_uni = [z for z in sorted(df[col_zona_geo].unique().tolist()) if z != ""]

        if zonas_uni:
            counts = df[col_zona_geo].value_counts().to_dict()
            total_disp = sum(counts.values()) or 1

            # asignar cuadrillas por zona (mínimo 1)
            k_total = int(n_cuadrillas)
            k_por_zona = {}
            for z in zonas_uni:
                frac = counts.get(z, 0) / total_disp
                k_por_zona[z] = max(1, int(round(frac * k_total)))

            def _sumk(d): return sum(d.values())

            while _sumk(k_por_zona) > k_total:
                cand = [z for z in zonas_uni if k_por_zona[z] > 1]
                if not cand:
                    break
                zmax = max(cand, key=lambda z: k_por_zona[z])
                k_por_zona[zmax] -= 1

            while _sumk(k_por_zona) < k_total:
                zmax = max(zonas_uni, key=lambda z: counts.get(z, 0))
                k_por_zona[zmax] += 1

            next_cid = 1
            for z in zonas_uni:
                df_zone = df[df[col_zona_geo] == z]
                if df_zone.empty:
                    continue

                k_z = min(k_por_zona.get(z, 1), len(df_zone))
                if k_z <= 0:
                    continue

                # ✅ NOTA: mantenemos tu lógica de "head", pero el post-fill completará con A TIEMPO si hace falta.
                # top de esa zona: hasta k_z * cap
                df_z = df_zone.head(k_z * cap_por_cuadrilla).copy()
                if df_z.empty:
                    continue

                # clustering dentro de la zona
                df_z_asig = asignar_cuadrillas_kmeans(df_z, n_cuadrillas=int(k_z))

                # renumerar cuadrillas globalmente
                old_ids = sorted(df_z_asig["cuadrilla_id"].unique().tolist())
                mapa = {old: next_cid + i for i, old in enumerate(old_ids)}
                df_z_asig["cuadrilla_id"] = df_z_asig["cuadrilla_id"].map(mapa)

                # construir cada cuadrilla con cap y secuenciar por bloques
                for cid in sorted(df_z_asig["cuadrilla_id"].unique().tolist()):
                    df_c = df_z_asig[df_z_asig["cuadrilla_id"] == cid].copy()

                    df_c = df_c.sort_values(
                        by=["prioridad_ans", "_fecha_limite_dt"],
                        ascending=[True, True],
                        na_position="last"
                    ).head(cap_por_cuadrilla)

                    df_seq = ordenar_nearest_neighbor_por_bloques(
                        df_c,
                        origen_lat=origen_lat,
                        origen_lng=origen_lng,
                        col_lat=col_lat,
                        col_lng=col_lng,
                    )

                    if "cuadrilla_id" not in df_seq.columns:
                        df_seq = df_seq.copy()
                        df_seq["cuadrilla_id"] = cid

                    plan[int(cid)] = df_seq

                next_cid += len(old_ids)

    # ---------------------------------------------------------
    # Caso 2: Modo libre (mezcla) => top total_req + KMeans global
    # ---------------------------------------------------------
    if not plan:
        df_top = df.head(total_req).copy()
        if df_top.empty:
            return {}

        df_asig = asignar_cuadrillas_kmeans(df_top, n_cuadrillas=int(n_cuadrillas))

        for cid in sorted(df_asig["cuadrilla_id"].unique().tolist()):
            df_c = df_asig[df_asig["cuadrilla_id"] == cid].copy()

            df_c = df_c.sort_values(
                by=["prioridad_ans", "_fecha_limite_dt"],
                ascending=[True, True],
                na_position="last"
            ).head(cap_por_cuadrilla)

            df_seq = ordenar_nearest_neighbor_por_bloques(
                df_c,
                origen_lat=origen_lat,
                origen_lng=origen_lng,
                col_lat=col_lat,
                col_lng=col_lng,
            )

            if "cuadrilla_id" not in df_seq.columns:
                df_seq = df_seq.copy()
                df_seq["cuadrilla_id"] = int(cid)

            plan[int(cid)] = df_seq

    # ORDEN_VISITA si faltara (ANTES del post-fill)
    for cid, dfp in list(plan.items()):
        if "ORDEN_VISITA" not in dfp.columns:
            dfp = dfp.copy()
            dfp["ORDEN_VISITA"] = range(1, len(dfp) + 1)
            plan[cid] = dfp

    # ==========================================================
    # POST-FILL: Completar cupos por cuadrilla con A TIEMPO
    # (los más próximos a FECHA_LIMITE_ANS => próximos a ALERTA)
    # ==========================================================
    # Regla:
    # 1) No duplicar pedidos
    # 2) Rellenar con A TIEMPO por fecha límite más próxima (riesgo)
    # 3) Si respetar_zona_geo=True: primero intenta rellenar desde la MISMA zona_geo
    #    y si no alcanza, rellena del resto (para garantizar 15 si hay inventario).
    # ==========================================================

    # 1) set de pedidos ya asignados (evita duplicados)
    assigned = set()
    for _, dfc in plan.items():
        if col_pedido in dfc.columns:
            assigned.update(dfc[col_pedido].astype(str).tolist())

    # 2) pool restante (NO asignado) -> usa df (ya canonizado y con lat/lng válidos)
    df_rest = df.copy()
    df_rest[col_pedido] = df_rest[col_pedido].astype(str)
    df_rest = df_rest[~df_rest[col_pedido].isin(assigned)].copy()

    # 3) filtrar SOLO A TIEMPO para rellenar (mejor por estado_ans ya canonizado)
    if "estado_ans" not in df_rest.columns:
        df_rest["estado_ans"] = df_rest[col_estado].apply(_canon_estado_ans)
    if "prioridad_ans" not in df_rest.columns:
        df_rest["prioridad_ans"] = df_rest["estado_ans"].apply(_prio_estado_ans)
    if "_fecha_limite_dt" not in df_rest.columns:
        df_rest["_fecha_limite_dt"] = pd.to_datetime(df_rest[col_fecha_limite], errors="coerce")

    df_fill_all = df_rest[df_rest["estado_ans"] == "A TIEMPO"].copy()

    # 4) ordenar por FECHA_LIMITE_ANS (más próximo primero)
    df_fill_all = df_fill_all.sort_values(["_fecha_limite_dt"], ascending=[True], na_position="last")

    # 5) completar cada cuadrilla hasta cap_por_cuadrilla
    for cid in sorted(plan.keys()):
        dfc = plan[cid].copy()
        faltan = int(cap_por_cuadrilla) - len(dfc)
        if faltan <= 0:
            plan[cid] = dfc
            continue

        if len(df_fill_all) == 0:
            plan[cid] = dfc
            continue

        # --- prioridad de relleno por zona si aplica
        zona_c = None
        if respetar_zona_geo and (col_zona_geo in dfc.columns) and (col_zona_geo in df_fill_all.columns):
            # zona "dominante" de la cuadrilla (la más frecuente)
            try:
                zona_c = (
                    dfc[col_zona_geo].fillna("").astype(str).str.strip()
                    .value_counts().index[0]
                )
                zona_c = zona_c if zona_c != "" else None
            except Exception:
                zona_c = None

        take_parts = []

        # 5.A) Primero: A TIEMPO de la MISMA zona
        if zona_c is not None:
            same = df_fill_all[df_fill_all[col_zona_geo].fillna("").astype(str).str.strip() == zona_c].copy()
            if len(same) > 0:
                take_same = same.head(faltan).copy()
                if len(take_same) > 0:
                    take_parts.append(take_same)
                    # remover del pool global los pedidos tomados
                    df_fill_all = df_fill_all[~df_fill_all[col_pedido].astype(str).isin(take_same[col_pedido].astype(str))].copy()
                    faltan -= len(take_same)

        # 5.B) Si aún falta: completar con A TIEMPO del RESTO (para garantizar 15 si hay inventario)
        if faltan > 0 and len(df_fill_all) > 0:
            take_more = df_fill_all.head(faltan).copy()
            if len(take_more) > 0:
                take_parts.append(take_more)
                df_fill_all = df_fill_all.iloc[len(take_more):].copy()
                faltan -= len(take_more)

        if not take_parts:
            plan[cid] = dfc
            continue

        take = pd.concat(take_parts, ignore_index=True)

        # asegurar cuadrilla_id para el plan
        take["cuadrilla_id"] = cid

        # unir
        merged = pd.concat([dfc, take], ignore_index=True)

        # ✅ RECALCULAR RUTA/DISTANCIAS PARA TODA LA CUADRILLA (con el relleno)
        df_all = ordenar_nearest_neighbor_por_bloques(
            merged,
            origen_lat=origen_lat,
            origen_lng=origen_lng,
            col_lat=col_lat,
            col_lng=col_lng,
        )

        # asegurar cuadrilla_id y ORDEN_VISITA consistentes
        df_all["cuadrilla_id"] = cid
        df_all["ORDEN_VISITA"] = range(1, len(df_all) + 1)

        # blindaje si la función no devolvió dist_prev_km
        if "dist_prev_km" not in df_all.columns:
            df_all["dist_prev_km"] = None

        plan[cid] = df_all

    # ✅ Limpieza final: no mostrar columnas técnicas
    for cid in list(plan.keys()):
        plan[cid] = plan[cid].drop(columns=["_fecha_lim"], errors="ignore")

    return plan