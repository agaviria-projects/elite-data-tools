import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def asignar_cuadrillas_kmeans(df: pd.DataFrame, n_cuadrillas: int, seed: int = 42) -> pd.DataFrame:
    """
    Asigna cada pedido a una cuadrilla usando KMeans sobre (lat,lng).
    Retorna df con columna 'cuadrilla_id' (1..K).
    """
    out = df.copy()

    coords = out[["lat", "lng"]].dropna()
    if len(coords) == 0:
        out["cuadrilla_id"] = 1
        return out

    k = int(min(max(1, n_cuadrillas), len(coords)))

    model = KMeans(n_clusters=k, random_state=seed, n_init="auto")
    labels = model.fit_predict(coords.to_numpy())

    out.loc[coords.index, "cuadrilla_id"] = (labels + 1)  # 1..k
    out["cuadrilla_id"] = out["cuadrilla_id"].fillna(1).astype(int)

    return out
