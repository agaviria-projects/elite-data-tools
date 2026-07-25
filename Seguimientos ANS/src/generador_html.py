from pathlib import Path


# ==========================================================
# RUTA PLANTILLAS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CARPETA_TEMPLATES = (
    BASE_DIR
    / "templates"
)

PLANTILLA_CORREO = (
    CARPETA_TEMPLATES
    / "correo_ans.html"
)


# ==========================================================
# LEER PLANTILLA
# ==========================================================

def leer_plantilla() -> str:
    """
    Lee la plantilla principal del correo.
    """

    with open(
        PLANTILLA_CORREO,
        "r",
        encoding="utf-8",
    ) as archivo:

        return archivo.read()


# ==========================================================
# GENERAR HTML
# ==========================================================

def generar_html(
    correo: dict,
) -> str:
    """
    Genera el HTML principal del correo.

    En esta primera versión únicamente reemplaza
    la información general del informe.

    Las actividades y tablas se incorporarán
    en las siguientes versiones.
    """

    html = leer_plantilla()

    html = html.replace(
        "{{GRUPO}}",
        correo["grupo"],
    )

    html = html.replace(
        "{{SUBZONA}}",
        correo["subzona"],
    )

    html = html.replace(
        "{{FECHA}}",
        correo["fecha_corte"],
    )

    html = html.replace(
        "{{TOTAL}}",
        str(correo["total_pedidos"]),
    )

    # En la primera versión aún no existen actividades

    html = html.replace(
        "{{ACTIVIDADES}}",
        "<h3>Próximamente...</h3>",
    )

    return html