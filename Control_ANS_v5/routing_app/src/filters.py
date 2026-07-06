# src/filters.py
import pandas as pd
from .constants import CONCEPTOS_RUTEO

def aplicar_filtros(
    df: pd.DataFrame,
    conceptos: list[str] | None = None,
    estados: list[str] | None = None,
    actividades: list[str] | None = None,
    zonas: list[str] | None = None,
) -> pd.DataFrame:
    out = df.copy()

    if not conceptos:
        conceptos = sorted(list(CONCEPTOS_RUTEO))
    out = out[out["concepto"].isin(conceptos)]

    if estados:
        out = out[out["estado"].isin(estados)]
    if actividades:
        out = out[out["actividad"].isin(actividades)]
    if zonas:
        out = out[out["zona"].isin(zonas)]

    return out
