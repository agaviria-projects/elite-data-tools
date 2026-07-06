# routing_app/src/routing.py
import math
import pandas as pd


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p = math.pi / 180.0
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    a = (math.sin(dlat / 2) ** 2) + math.cos(lat1 * p) * math.cos(lat2 * p) * (math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _ans_priority(row: pd.Series, now: pd.Timestamp) -> int:
    """
    Prioridad:
      0 = VENCIDO
      1 = ALERTA_0 / ALERTA_0 DIAS / ALERTA 0 DIAS
      2 = ALERTA
      3 = A TIEMPO
    Usa 'estado' si existe (más confiable). Si no, usa FECHA_LIMITE_ANS.
    """

    # 1) ✅ PRIORIDAD POR 'estado' (si existe)
    if "estado" in row.index:
        est = str(row.get("estado", "")).strip().upper()

        # normalizaciones comunes
        if est == "VENCIDO":
            return 0
        if est in {"ALERTA_0", "ALERTA_0 DIAS", "ALERTA 0 DIAS", "ALERTA_0 DÍAS", "ALERTA 0 DÍAS"}:
            return 1
        if est == "ALERTA":
            return 2
        if est in {"A TIEMPO", "ATIEMPO"}:
            return 3
        # si viene algo raro, no rompas: mándalo al final

    # 2) Fallback por FECHA_LIMITE_ANS (si 'estado' no existe)
    col_fecha = None
    for c in row.index:
        if str(c).strip().upper() == "FECHA_LIMITE_ANS":
            col_fecha = c
            break
        # soporte por si viene en minúscula o variante
        if str(c).strip().lower() == "fecha_limite_ans":
            col_fecha = c
            break

    if not col_fecha:
        return 3

    dt = pd.to_datetime(row.get(col_fecha, pd.NaT), errors="coerce")
    if pd.isna(dt):
        return 3

    now_day = now.normalize()
    dt_day = dt.normalize()

    if dt < now:
        return 0
    if dt_day == now_day:
        return 1

    # ALERTA cercano: usa DIAS_RESTANTES si existe
    if "DIAS_RESTANTES" in row.index:
        try:
            dr = float(row.get("DIAS_RESTANTES"))
            if dr <= 2:
                return 2
        except Exception:
            pass

    try:
        days = int((dt_day - now_day).days)
        if days <= 2:
            return 2
    except Exception:
        pass

    return 3


# decide el pedido mas cercano partiendo desde el origen (ejemeplo Bodega o cualquier origen)
def greedy_route_order(df_pts: pd.DataFrame, start_lat: float, start_lng: float) -> pd.DataFrame:
    """
    Ordena puntos con greedy nearest-neighbor desde (start_lat,start_lng)
    PERO primero respeta prioridad ANS por FECHA_LIMITE_ANS:
      VENCIDO -> ALERTA 0 -> ALERTA -> A TIEMPO
    Retorna df con columnas: route_order (1..n) y dist_prev_km.
    """
    pts = df_pts.copy().reset_index(drop=True)

    if len(pts) == 0:
        pts["route_order"] = []
        pts["dist_prev_km"] = []
        return pts

    # ✅ NUEVO: pre-calcular prioridad para no recalcular muchas veces
    now = pd.Timestamp.now()
    pts["_ans_prio"] = pts.apply(lambda r: _ans_priority(r, now), axis=1)

    remaining = set(range(len(pts)))
    cur_lat, cur_lng = float(start_lat), float(start_lng)

    ordered_rows = []
    step = 1
    prev_dist = 0.0

    while remaining:
        best_i = None
        best_key = None  # (prio, dist)

        for i in remaining:
            # distancia desde punto actual
            d = haversine_km(cur_lat, cur_lng, float(pts.loc[i, "lat"]), float(pts.loc[i, "lng"]))

            # ✅ clave compuesta: primero prioridad ANS, luego nearest neighbor
            prio = int(pts.loc[i, "_ans_prio"]) if "_ans_prio" in pts.columns else 3
            key = (prio, float(d))

            if best_key is None or key < best_key:
                best_key = key
                best_i = i

        row = pts.loc[best_i].copy()
        row["route_order"] = step
        row["dist_prev_km"] = float(best_key[1]) if best_key is not None else float(prev_dist)

        ordered_rows.append(row)

        cur_lat = float(pts.loc[best_i, "lat"])
        cur_lng = float(pts.loc[best_i, "lng"])
        remaining.remove(best_i)
        prev_dist = best_key[1] if best_key is not None else prev_dist
        step += 1

    out = pd.DataFrame(ordered_rows).reset_index(drop=True)

    # ✅ Limpieza: no exportar columna interna
    if "_ans_prio" in out.columns:
        out = out.drop(columns=["_ans_prio"])

    return out


def generar_rutas_por_cuadrilla(df: pd.DataFrame, start_lat: float, start_lng: float) -> dict:
    """
    Retorna dict {cuadrilla_id: df_ordenado}
    """
    rutas = {}
    if "cuadrilla_id" not in df.columns:
        # fallback: todo a cuadrilla 1
        tmp = df.copy()
        tmp["cuadrilla_id"] = 1
        df = tmp

    for cid, g in df.groupby("cuadrilla_id"):
        rutas[int(cid)] = greedy_route_order(g, start_lat, start_lng)

    return rutas


# -----------------------------
# Google Maps URL (API style) - ÚNICA FUNCIÓN
# (mínimo cambio: asegurar ORIGEN bodega + DESTINO último punto + WAYPOINTS intermedios)
# -----------------------------
from urllib.parse import urlencode


def url_google_maps_cuadrilla(
    df_ruta,
    start_lat: float,
    start_lng: float,
    return_to_bodega: bool = False,
    max_waypoints: int = 23,
    travelmode: str = "driving",
) -> str | None:
    """
    Genera URL Google Maps (api=1) más estable/compatible.

    - origin: bodega
    - destination: último punto (o bodega si return_to_bodega=True)
    - waypoints: puntos intermedios separados por "|"
    - Orden: respeta ORDEN_VISITA o route_order si existen
    - max_waypoints: límite práctico (Google suele limitar ~23 waypoints)
    """
    if df_ruta is None or len(df_ruta) == 0:
        return None

    if "lat" not in df_ruta.columns or "lng" not in df_ruta.columns:
        return None

    df = df_ruta.copy()

    # ✅ MÍNIMO: ordenar si viene el orden del plan/ruta
    if "ORDEN_VISITA" in df.columns:
        df = df.sort_values("ORDEN_VISITA", ascending=True)
    elif "route_order" in df.columns:
        df = df.sort_values("route_order", ascending=True)

    # ✅ MÍNIMO: asegurar numéricos (evita strings raros)
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")

    pts = df[["lat", "lng"]].dropna()
    if len(pts) == 0:
        return None

    origin = f"{float(start_lat)},{float(start_lng)}"

    # ✅ BLINDAJE: si algún punto coincide (o está muy cerca) del origen, lo quitamos
    # Esto evita que Maps "funda" la bodega con el primer pedido.
    try:
        o_lat, o_lng = float(start_lat), float(start_lng)

        def _dist_km(row):
            return haversine_km(o_lat, o_lng, float(row["lat"]), float(row["lng"]))

        dists = pts.apply(_dist_km, axis=1)
        pts = pts.loc[dists > 0.05]  # 50 metros (ajústalo si quieres)
    except Exception:
        pass

    if len(pts) == 0:
        return None


    if return_to_bodega:
        # destino vuelve a bodega, waypoints = primeros N puntos
        destination = origin
        wp_pts = pts.head(max_waypoints)
    else:
        # destino = último punto; waypoints = todos menos el último (recortado)
        pts2 = pts.head(max_waypoints + 1)  # +1 para poder tener destino + waypoints
        last = pts2.iloc[-1]
        destination = f"{last['lat']},{last['lng']}"
        wp_pts = pts2.iloc[:-1]  # intermedios

    waypoints = "|".join([f"{r.lat},{r.lng}" for r in wp_pts.itertuples(index=False)]) if len(wp_pts) else ""

    params = {
        "api": "1",
        "origin": origin,
        "destination": destination,
        "travelmode": travelmode,
    }
    if waypoints:
        params["waypoints"] = waypoints

    return "https://www.google.com/maps/dir/?" + urlencode(params, safe="|,")


# =========================================================
# Wrapper requerido por plan_diario_8x15 (NO rompe flujo)
# =========================================================
def ordenar_nearest_neighbor_por_bloques(
    df_pts: pd.DataFrame,
    origen_lat: float = 0.0,
    origen_lng: float = 0.0,
    col_lat: str = "lat",
    col_lng: str = "lng",
) -> pd.DataFrame:
    """
    Compatibilidad con plan_diario_8x15():
    - Usa greedy_route_order() (ya existente) para secuenciar por cercanía.
    - greedy_route_order() ya respeta prioridad ANS por estado/FECHA_LIMITE_ANS.
    - Retorna columna ORDEN_VISITA (1..N) sin tocar tu lógica actual.
    """
    if df_pts is None or len(df_pts) == 0:
        return df_pts

    # Copia y asegura nombres esperados por greedy_route_order (lat/lng)
    tmp = df_pts.copy()

    # Si vienen con otro nombre, las duplicamos (no reemplazamos)
    if col_lat != "lat":
        tmp["lat"] = pd.to_numeric(tmp[col_lat], errors="coerce")
    else:
        tmp["lat"] = pd.to_numeric(tmp["lat"], errors="coerce")

    if col_lng != "lng":
        tmp["lng"] = pd.to_numeric(tmp[col_lng], errors="coerce")
    else:
        tmp["lng"] = pd.to_numeric(tmp["lng"], errors="coerce")

    tmp = tmp.dropna(subset=["lat", "lng"]).copy()
    if tmp.empty:
        return tmp

    out = greedy_route_order(tmp, float(origen_lat), float(origen_lng))

    # Normaliza el nombre de la columna de orden para tu flujo
    if "route_order" in out.columns and "ORDEN_VISITA" not in out.columns:
        out = out.rename(columns={"route_order": "ORDEN_VISITA"})

    return out

# =========================================================
# ✅ NUEVO: Google Maps en TRAMOS (evita recorte en móvil)
# - Reutiliza url_google_maps_cuadrilla() sin tocar tu lógica actual
# - Devuelve lista de URLs: ["tramo1", "tramo2", ...]
# =========================================================
def urls_google_maps_cuadrilla_tramos(
    df_ruta,
    start_lat: float,
    start_lng: float,
    return_to_bodega: bool = False,
    max_paradas_por_tramo: int = 9,
    travelmode: str = "driving",
) -> list[str]:
    """
    Google Maps móvil suele recortar si mandas muchas paradas.
    Este helper parte la ruta en tramos y devuelve VARIAS URLs.

    max_paradas_por_tramo:
      - número de PARADAS por tramo (sin contar la bodega).
      - recomendado 8 o 9 para móvil.

    Nota: usa el mismo orden (ORDEN_VISITA / route_order) que ya manejas.
    """
    import pandas as pd  # blindaje local

    if df_ruta is None or len(df_ruta) == 0:
        return []

    # requiere estas columnas (tu flujo ya las maneja)
    if "lat" not in df_ruta.columns or "lng" not in df_ruta.columns:
        return []

    df = df_ruta.copy()

    # Respeta orden
    if "ORDEN_VISITA" in df.columns:
        df = df.sort_values("ORDEN_VISITA", ascending=True)
    elif "route_order" in df.columns:
        df = df.sort_values("route_order", ascending=True)

    # Asegura numéricos
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    df = df.dropna(subset=["lat", "lng"]).copy()
    if df.empty:
        return []

    n = int(max_paradas_por_tramo) if max_paradas_por_tramo else 9
    chunks = [df.iloc[i:i+n].copy() for i in range(0, len(df), n)]

    urls: list[str] = []
    for ch in chunks:
        u = url_google_maps_cuadrilla(
            ch,
            start_lat=float(start_lat),
            start_lng=float(start_lng),
            return_to_bodega=bool(return_to_bodega),
            max_waypoints=max(0, len(ch) - 1),
            travelmode=travelmode,
        )
        if u:
            urls.append(u)

    return urls