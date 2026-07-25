import pandas as pd

from ..config.grupos import GRUPOS


# ==========================================================
# RESUMEN POR ESTADO
# ==========================================================

def resumen_estado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera el resumen por estado de un DataFrame.
    """

    if df.empty:

        return pd.DataFrame(
            columns=[
                "ESTADO",
                "TOTAL",
                "PORCENTAJE",
            ]
        )

    resumen = (

        df.groupby("ESTADO")

        .size()

        .reset_index(name="TOTAL")

    )

    resumen["PORCENTAJE"] = (

        resumen["TOTAL"]

        / resumen["TOTAL"].sum()

        * 100

    ).round(1)

    return resumen


# ==========================================================
# CONSTRUIR INFORMES
# ==========================================================

def construir_informes(
    df: pd.DataFrame,
) -> dict:
    """
    Construye todos los informes definidos en
    config/grupos.py.

    Retorna un diccionario con la siguiente estructura:

    {
        "PUNTOS DE CONEXIÓN": [

            {

                "productos": [...],

                "actividades": {

                    "ACREV": DataFrame

                }

            }

        ],

        ...

    }
    """

    informes = {}

    # ------------------------------------------------------
    # RECORRER CADA GRUPO
    # ------------------------------------------------------

    for nombre_grupo, configuracion in GRUPOS.items():

        bloques = []

        # --------------------------------------------------
        # RECORRER BLOQUES DEL GRUPO
        # --------------------------------------------------

        for bloque in configuracion["bloques"]:

            productos = bloque["producto"]

            actividades = bloque["actividades"]

            actividades_dict = {}

            # ----------------------------------------------
            # RECORRER ACTIVIDADES
            # ----------------------------------------------

            for actividad in actividades:

                df_filtrado = df[

                    (df["PRODUCTO_ID"].isin(productos))

                    &

                    (df["ACTIVIDAD"] == actividad)

                ].copy()

                actividades_dict[actividad] = df_filtrado

            bloques.append(

                {

                    "productos": productos,

                    "actividades": actividades_dict,

                    "total_pedidos": sum(
                        len(x)
                        for x in actividades_dict.values()
                    ),

                    "resumen": {

                        actividad: resumen_estado(df_actividad)

                        for actividad, df_actividad

                        in actividades_dict.items()

                    }

                }

            )

        informes[nombre_grupo] = bloques

    return informes