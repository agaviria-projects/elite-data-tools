# --- NUEVO: sugerir origen (centroide) a partir del DF filtrado ---
import numpy as np
import pandas as pd
import requests

def sugerir_origen_por_df(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lng_col: str = "lng",
    metodo: str = "median",   # "median" (más robusto) o "mean"
    min_puntos: int = 3
):
    """
    Devuelve (lat, lng) sugerido como centro del conjunto de pedidos filtrados.
    - Usa lat/lng del DF (ya deberían venir numéricos desde io_excel.py)
    - Ignora NaN
    - Si hay muy pocos puntos, retorna None
    """
    if df is None or len(df) == 0:
        return None

    if lat_col not in df.columns or lng_col not in df.columns:
        return None

    lat = pd.to_numeric(df[lat_col], errors="coerce")
    lng = pd.to_numeric(df[lng_col], errors="coerce")

    mask = lat.notna() & lng.notna()
    if mask.sum() < min_puntos:
        return None

    if str(metodo).lower() == "mean":
        return (float(lat[mask].mean()), float(lng[mask].mean()))
    else:
        # median por defecto (más estable si hay outliers)
        return (float(np.nanmedian(lat[mask].values)), float(np.nanmedian(lng[mask].values)))

# --- NUEVO: obtener dirección (reverse geocoding) desde lat/lng ---
def obtener_direccion_por_latlng(
    lat: float,
    lng: float,
    zoom: int = 18
) -> str | None:
    """
    Devuelve una dirección aproximada usando Nominatim (OpenStreetMap).
    - NO afecta el ruteo (solo es informativo para mostrar la dirección de la bodega).
    - Puede retornar None si no hay coincidencia exacta.
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "jsonv2",
            "lat": float(lat),
            "lon": float(lng),
            "zoom": int(zoom),
            "addressdetails": 1
        }
        headers = {"User-Agent": "Control_ANS_Enrutamiento/1.0"}

        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        return data.get("display_name")

    except Exception:
        return None
    
def clasificar_zona_geo(
    lat: float,
    lng: float,
    *,
    lat_norte: float = 6.30,
    lat_sur: float = 6.20,
    lng_occidente: float = -75.61,
    lng_oriente: float = -75.54
) -> str:
    """
    Clasificación geográfica simple por coordenadas.
    Ajusta umbrales según tu operación.
    Retorna: NORTE, SUR, OCCIDENTE, ORIENTE, CENTRO, SIN_COORD
    """
    if lat is None or lng is None:
        return "SIN_COORD"

    try:
        lat = float(lat)
        lng = float(lng)
    except Exception:
        return "SIN_COORD"

    # Norte / Sur primero
    if lat >= lat_norte:
        return "NORTE"
    if lat <= lat_sur:
        return "SUR"

    # Oriente / Occidente por longitud
    if lng <= lng_occidente:
        return "OCCIDENTE"
    if lng >= lng_oriente:
        return "ORIENTE"

    return "CENTRO"