# src/export.py
from __future__ import annotations
from io import BytesIO
import pandas as pd

from io import BytesIO
import pandas as pd

from .google_maps import url_punto, url_street_view, urls_ruta_google


def _sheet_name(cid: int) -> str:
    name = f"CUADRILLA_{int(cid):02d}"
    return name[:31]  # Excel limit


def _preparar_df_export(df: pd.DataFrame, cid: int) -> pd.DataFrame:
    out = df.copy()

    # Asegurar orden
    if "orden" not in out.columns:
        out.insert(0, "orden", range(1, len(out) + 1))

    # Asegurar cuadrilla
    if "cuadrilla" not in out.columns:
        out.insert(0, "cuadrilla", int(cid))

    # Links por punto
    if "lat" in out.columns and "lng" in out.columns:
        out["link_maps_punto"] = out.apply(lambda r: url_punto(r["lat"], r["lng"]), axis=1)
        out["link_street_view"] = out.apply(lambda r: url_street_view(r["lat"], r["lng"]), axis=1)

    # Orden sugerido de columnas (si existen)
    prefer = [
        "cuadrilla", "orden", "pedido", "concepto", "actividad", "estado", "zona", "subzona",
        "direccion", "municipio", "cliente", "celular", "lat", "lng",
        "link_maps_punto", "link_street_view"
    ]
    cols = [c for c in prefer if c in out.columns] + [c for c in out.columns if c not in prefer]
    out = out[cols]

    return out


def exportar_excel_cuadrilla(
    df_cuadrilla: pd.DataFrame,
    cid: int,
) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_out = _preparar_df_export(df_cuadrilla, cid)
        df_out.to_excel(writer, sheet_name=_sheet_name(cid), index=False)
    return output.getvalue()


def exportar_excel_todas(
    rutas: dict,
) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for cid, df in rutas.items():
            df_out = _preparar_df_export(df, cid)
            df_out.to_excel(writer, sheet_name=_sheet_name(cid), index=False)
    return output.getvalue()

def exportar_rutas_excel_bytes(rutas: dict) -> bytes:
    """
    Retorna un .xlsx en memoria con 1 hoja por cuadrilla.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for cid, df in rutas.items():
            sheet = f"Cuadrilla_{cid}"
            df.to_excel(writer, sheet_name=sheet[:31], index=False)  # Excel limita 31 chars
    output.seek(0)
    return output.getvalue()


def generar_links_ruta_por_cuadrilla(
    df_cuadrilla: pd.DataFrame,
    bodega_lat: float,
    bodega_lng: float,
    max_waypoints: int = 20,
) -> list[str]:
    """
    Crea 1 o varios links para abrir la ruta en Google Maps,
    respetando el orden del DataFrame.
    """
    if len(df_cuadrilla) == 0:
        return []

    pts = list(zip(df_cuadrilla["lat"].astype(float), df_cuadrilla["lng"].astype(float)))
    origin = (float(bodega_lat), float(bodega_lng))
    destination = (float(bodega_lat), float(bodega_lng))  # vuelve a bodega (cierre)
    return urls_ruta_google(origin, destination, pts, max_waypoints=max_waypoints)
