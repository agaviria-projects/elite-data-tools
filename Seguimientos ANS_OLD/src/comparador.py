import pandas as pd


# ==========================================================
# OBTENER PEDIDOS NUEVOS
# ==========================================================

def obtener_pedidos_nuevos(
    df_actual: pd.DataFrame,
    df_anterior: pd.DataFrame,
) -> pd.DataFrame:
    """
    Retorna los pedidos que aparecen únicamente
    en el corte actual.
    """

    return df_actual[
        ~df_actual["PEDIDO"].isin(df_anterior["PEDIDO"])
    ].copy()


# ==========================================================
# OBTENER PEDIDOS PERSISTENTES
# ==========================================================

def obtener_pedidos_persistentes(
    df_actual: pd.DataFrame,
    df_anterior: pd.DataFrame,
) -> pd.DataFrame:
    """
    Retorna los pedidos que existen tanto
    en el corte anterior como en el actual.
    """

    return df_actual[
        df_actual["PEDIDO"].isin(df_anterior["PEDIDO"])
    ].copy()


# ==========================================================
# OBTENER PEDIDOS GESTIONADOS
# ==========================================================

def obtener_pedidos_gestionados(
    df_actual: pd.DataFrame,
    df_anterior: pd.DataFrame,
) -> pd.DataFrame:
    """
    Retorna los pedidos que estaban en el corte
    anterior y ya no aparecen en el actual.
    """

    return df_anterior[
        ~df_anterior["PEDIDO"].isin(df_actual["PEDIDO"])
    ].copy()


# ==========================================================
# CAMBIOS DE ESTADO
# ==========================================================

def obtener_cambios_estado(
    df_actual: pd.DataFrame,
    df_anterior: pd.DataFrame,
) -> pd.DataFrame:
    """
    Retorna únicamente los pedidos cuyo
    estado cambió entre cortes.
    """

    anterior = df_anterior[
        ["PEDIDO", "ESTADO"]
    ].rename(
        columns={
            "ESTADO": "ESTADO_ANTERIOR"
        }
    )

    actual = df_actual[
        ["PEDIDO", "ESTADO"]
    ].rename(
        columns={
            "ESTADO": "ESTADO_ACTUAL"
        }
    )

    df = anterior.merge(
        actual,
        on="PEDIDO",
        how="inner",
    )

    return df[
        df["ESTADO_ANTERIOR"] != df["ESTADO_ACTUAL"]
    ].copy()