# src/io_excel.py
import pandas as pd
import numpy as np
from . import constants as C


def _colapsar_columnas_duplicadas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Si hay columnas duplicadas (mismo nombre), las colapsa en una sola tomando
    el primer valor no nulo por fila (de izquierda a derecha).
    """
    if not df.columns.duplicated().any():
        return df

    out = df.copy()
    series_list = []
    new_cols = []

    for col in pd.unique(out.columns):
        if (out.columns == col).sum() == 1:
            series_list.append(out[col])
        else:
            block = out.loc[:, col]
            merged = block.bfill(axis=1).iloc[:, 0]
            series_list.append(merged)

        new_cols.append(col)

    out = pd.concat(series_list, axis=1)
    out.columns = new_cols
    return out


import re

def _normalizar_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def _norm_col(c) -> str:
        s = str(c).strip().lower()
        s = s.replace("\u00a0", " ")          # ✅ NBSP -> espacio normal
        s = re.sub(r"\s+", "_", s)            # ✅ cualquier whitespace -> _
        s = s.replace("-", "_")
        s = re.sub(r"_+", "_", s)             # ✅ colapsa ___
        return s

    df.columns = [_norm_col(c) for c in df.columns]

    ren = {c: C.ALIASES[c] for c in df.columns if c in C.ALIASES}
    if ren:
        df = df.rename(columns=ren)

    df = _colapsar_columnas_duplicadas(df)
    return df

def validar_columnas(df: pd.DataFrame) -> tuple[bool, list]:
    faltantes = [c for c in C.COLS_MIN if c not in df.columns]
    return (len(faltantes) == 0, faltantes)


def cargar_excel(uploaded_file) -> pd.DataFrame:
    df = pd.read_excel(uploaded_file)
    df = _normalizar_cols(df)
    
    # ============================
    # ✅ CELULAR: regla dura
    # - Mantener celular_contacto y telefono_contacto si existen
    # - Construir columna 'celular' (COLS_MIN) priorizando celular_contacto
    # ============================
    if "celular_contacto" in df.columns:
        base = df["celular_contacto"].astype(str).str.strip()
        base = base.replace({"": np.nan, "nan": np.nan, "none": np.nan, "None": np.nan})
        df["celular_contacto"] = base

    if "telefono_contacto" in df.columns:
        tel = df["telefono_contacto"].astype(str).str.strip()
        tel = tel.replace({"": np.nan, "nan": np.nan, "none": np.nan, "None": np.nan})
        df["telefono_contacto"] = tel

    # construir 'celular' requerido
    if "celular_contacto" in df.columns and "telefono_contacto" in df.columns:
        df["celular"] = df["celular_contacto"].fillna(df["telefono_contacto"])
    elif "celular_contacto" in df.columns:
        df["celular"] = df["celular_contacto"]
    elif "telefono_contacto" in df.columns:
        df["celular"] = df["telefono_contacto"]
    # else: si ya existe 'celular' por otra fuente, se respeta


    # ✅ Preferir SUBZONA para el filtro de zona (si existe y trae valores)
    if "subzona" in df.columns:
        sub = df["subzona"].astype(str).str.strip()
        sub = sub.replace({"": np.nan, "nan": np.nan, "none": np.nan, "None": np.nan})
        if sub.notna().any():
            df["zona"] = sub.fillna(df.get("zona"))

    # =========================================================
    # ✅ BLINDAJE CELULAR:
    # - df["celular"] siempre sale de CELULAR_CONTACTO si existe
    # - si no existe / viene vacío, cae a TELEFONO_CONTACTO/TELEFONO/TEL
    # =========================================================


    def _clean_phone_series(s: pd.Series) -> pd.Series:
        s = s.astype(str).str.strip()

        # normaliza textos basura
        s = s.replace({
            "": np.nan, "0": np.nan,
            "nan": np.nan, "NaN": np.nan,
            "none": np.nan, "None": np.nan,
            "null": np.nan, "NULL": np.nan,
            "SIN DATOS": np.nan, "sin datos": np.nan, "Sin datos": np.nan,
            "N/A": np.nan, "NA": np.nan
        })

        # deja solo dígitos
        s = s.astype(str).str.replace(r"\D+", "", regex=True)

        # vacíos -> NaN
        s = s.replace({"": np.nan})
        return s


    def _validar_celular_co(s: pd.Series) -> pd.Series:
        """
        ✅ Celular CO típico: 10 dígitos y empieza por 3.
        Si no cumple, se vuelve NaN (para que NO gane sobre telefono).
        """
        s = s.copy()
        ok = s.notna() & (s.str.len() == 10) & (s.str.startswith("3"))
        return s.where(ok, np.nan)


    # =========================
    # ✅ BLINDAJE CELULAR REAL
    # =========================

    cel_src = None
    if "celular_contacto" in df.columns:
        cel_src = _validar_celular_co(_clean_phone_series(df["celular_contacto"]))

    # teléfonos (pueden ser 7/10 dígitos, pero NO deben reemplazar celular real)
    tel_merge = None
    for c in ["telefono_contacto", "telefono", "tel"]:
        if c in df.columns:
            t = _clean_phone_series(df[c])
            tel_merge = t if tel_merge is None else tel_merge.fillna(t)

    # construir df["celular"] (la que usa el plan/export)
    if cel_src is not None and cel_src.notna().any():
        # ✅ SI hay celular real, manda
        df["celular"] = cel_src
    else:
        # ✅ si NO hay celular real, cae al teléfono si existe
        if tel_merge is not None and tel_merge.notna().any():
            df["celular"] = tel_merge
        else:
            df["celular"] = df.get("celular", "")


    # =========================================================

    ok, faltantes = validar_columnas(df)
    if not ok:
        raise ValueError(f"Faltan columnas obligatorias: {faltantes}")

    # lat/lng numéricos (robusto ante coma decimal)
    df["lat"] = pd.to_numeric(
        df["lat"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    df["lng"] = pd.to_numeric(
        df["lng"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )

    # Limpieza texto básica (nota: ahora celular ya viene blindado)
    for c in ["pedido", "concepto", "actividad", "zona", "estado", "direccion", "cliente", "celular"]:
        df[c] = df[c].astype(str).str.strip()

    return df


def separar_invalidos_latlng(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    mask = df["lat"].notna() & df["lng"].notna()
    return df[mask].copy(), df[~mask].copy()

