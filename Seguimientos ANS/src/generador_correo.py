from datetime import datetime

from config.parametros import SUBZONA_PROCESAR


# ==========================================================
# CONSTRUIR MODELO DE CORREO
# ==========================================================

def construir_correos(informes: dict) -> list[dict]:
    """
    Convierte la salida del agrupador en una estructura
    preparada para generar el HTML de los correos.
    """

    correos = []

    fecha_corte = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )

    for nombre_grupo, bloques in informes.items():

        correo = {

            "grupo": nombre_grupo,

            "asunto": (
                f"🚨 Seguimiento ANS | "
                f"{nombre_grupo}"
            ),

            "subzona": SUBZONA_PROCESAR,

            "fecha_corte": fecha_corte,

            "total_pedidos": sum(
                bloque["total_pedidos"]
                for bloque in bloques
            ),

            "bloques": []

        }

        # ----------------------------------------------
        # BLOQUES
        # ----------------------------------------------

        for bloque in bloques:

            bloque_correo = {

                "productos": bloque["productos"],

                "total_pedidos": bloque["total_pedidos"],

                "actividades": []

            }

            # ------------------------------------------
            # ACTIVIDADES
            # ------------------------------------------

            for actividad, df in bloque["actividades"].items():

                actividad_correo = {

                    "nombre": actividad,

                    "total": len(df),

                    "resumen": bloque["resumen"][actividad],

                    "tabla": df

                }

                bloque_correo["actividades"].append(
                    actividad_correo
                )

            correo["bloques"].append(
                bloque_correo
            )

        correos.append(
            correo
        )

    return correos