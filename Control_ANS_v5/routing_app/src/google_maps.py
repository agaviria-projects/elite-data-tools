# src/google_maps.py
from __future__ import annotations
from typing import Iterable, List, Tuple
from urllib.parse import quote


def _latlng(lat: float, lng: float) -> str:
    return f"{float(lat):.6f},{float(lng):.6f}"


def url_punto(lat: float, lng: float) -> str:
    # Abre un punto (búsqueda) en Google Maps
    return f"https://www.google.com/maps/search/?api=1&query={_latlng(lat, lng)}"


def url_street_view(lat: float, lng: float) -> str:
    # Abre Street View (si hay cobertura en ese punto)
    return f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={_latlng(lat, lng)}"


def urls_ruta_google(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    waypoints: Iterable[Tuple[float, float]],
    travelmode: str = "driving",
    max_waypoints: int = 20,
) -> List[str]:
    """
    Genera 1 o varias URLs de Google Maps Directions (si hay muchos waypoints).
    Google suele limitar el número de waypoints por URL; por estabilidad partimos en tramos.

    origin/destination: (lat,lng)
    waypoints: lista de puntos intermedios (lat,lng) en el orden de visita
    """

    wps = list(waypoints)

    # Partimos en tramos de max_waypoints
    urls: List[str] = []
    start = origin

    i = 0
    while i < len(wps):
        tramo = wps[i : i + max_waypoints]

        # Si aún quedan puntos después, el final del tramo será el último waypoint del tramo
        # y el siguiente tramo continuará desde allí.
        if i + max_waypoints < len(wps):
            end = tramo[-1]
            tramo_waypoints = tramo[:-1]
        else:
            end = destination
            tramo_waypoints = tramo

        origin_s = _latlng(start[0], start[1])
        dest_s = _latlng(end[0], end[1])

        if tramo_waypoints:
            wp_s = "|".join(_latlng(a, b) for a, b in tramo_waypoints)
            wp_s = quote(wp_s, safe="|,")
            url = (
                "https://www.google.com/maps/dir/?api=1"
                f"&origin={origin_s}"
                f"&destination={dest_s}"
                f"&travelmode={travelmode}"
                f"&waypoints={wp_s}"
            )
        else:
            url = (
                "https://www.google.com/maps/dir/?api=1"
                f"&origin={origin_s}"
                f"&destination={dest_s}"
                f"&travelmode={travelmode}"
            )

        urls.append(url)

        # Siguiente tramo: inicia en el final del tramo
        start = end
        i += max_waypoints

    return urls
