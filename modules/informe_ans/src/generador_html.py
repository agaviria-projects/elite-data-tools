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

    resumen = generar_resumen_ejecutivo(correo)

    html = html.replace(
        "{{RESUMEN_EJECUTIVO}}",
        resumen,
    )

    # En la primera versión aún no existen actividades

    actividades = generar_actividades(correo)

    html = html.replace(
        "{{ACTIVIDADES}}",
        actividades,
    )
    footer = generar_footer(correo)

    html = html.replace(
        "{{FOOTER}}",
        footer,
    )
    return html
# ==========================================================
# RESUMEN EJECUTIVO
# ==========================================================

def generar_resumen_ejecutivo(correo):
    """
    Genera cuatro KPIs ejecutivos compactos y compatibles
    con Outlook Desktop.

    La lógica de conteo se conserva.
    Únicamente cambia la presentación visual.
    """

    vencidos = 0
    alerta0 = 0
    alerta = 0
    tiempo = 0

    for bloque in correo["bloques"]:

        for actividad in bloque["actividades"]:

            resumen = actividad["resumen"]

            for _, fila in resumen.iterrows():

                estado = (
                    str(fila["ESTADO"])
                    .strip()
                    .upper()
                    .replace("_", " ")
                )

                total = int(fila["TOTAL"])

                if estado == "VENCIDO":

                    vencidos += total

                elif estado in (
                    "ALERTA 0 DÍAS",
                    "ALERTA 0 DIAS",
                ):

                    alerta0 += total

                elif estado == "ALERTA":

                    alerta += total

                elif estado == "A TIEMPO":

                    tiempo += total

    return f"""
    <table
        role="presentation"
        width="100%"
        cellpadding="0"
        cellspacing="0"
        border="0"
        style="
            width:100%;
            margin:10px 0 16px 0;
            border-collapse:collapse;
            font-family:Segoe UI, Arial, sans-serif;
        "
    >
        <tr>

            <!-- KPI VENCIDOS -->

            <td
                width="25%"
                valign="top"
                style="
                    width:25%;
                    padding:0 5px 0 0;
                "
            >
                <table
                    role="presentation"
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    border="0"
                    bgcolor="#fff7f7"
                    style="
                        width:100%;
                        background-color:#fff7f7;
                        border:1px solid #f2c9cd;
                        border-left:4px solid #dc2626;
                        border-collapse:separate;
                        border-radius:8px;
                    "
                >
                    <tr>
                        <td
                            valign="middle"
                            style="
                                padding:10px 11px;
                            "
                        >
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                                style="
                                    width:100%;
                                    border-collapse:collapse;
                                "
                            >
                                <tr>
                                    <td
                                        width="48"
                                        valign="middle"
                                        style="
                                            width:48px;
                                            color:#991b1b;
                                            font-family:Segoe UI, Arial, sans-serif;
                                            font-size:23px;
                                            font-weight:700;
                                            line-height:27px;
                                        "
                                    >
                                        {vencidos}
                                    </td>

                                    <td
                                        valign="middle"
                                        style="
                                            padding-left:8px;
                                        "
                                    >
                                        <div
                                            style="
                                                color:#991b1b;
                                                font-family:Segoe UI, Arial, sans-serif;
                                                font-size:11px;
                                                font-weight:700;
                                                line-height:15px;
                                            "
                                        >
                                            VENCIDOS
                                        </div>

                                        <div
                                            style="
                                                margin-top:2px;
                                                color:#7f1d1d;
                                                font-family:Segoe UI, Arial, sans-serif;
                                                font-size:9px;
                                                line-height:13px;
                                            "
                                        >
                                            Prioridad máxima
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>

            <!-- KPI ALERTA 0 DÍAS -->

            <td
                width="25%"
                valign="top"
                style="
                    width:25%;
                    padding:0 5px;
                "
            >
                <table
                    role="presentation"
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    border="0"
                    bgcolor="#fff8f1"
                    style="
                        width:100%;
                        background-color:#fff8f1;
                        border:1px solid #f5d0ae;
                        border-left:4px solid #f97316;
                        border-collapse:separate;
                        border-radius:8px;
                    "
                >
                    <tr>
                        <td
                            valign="middle"
                            style="
                                padding:10px 11px;
                            "
                        >
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                                style="
                                    width:100%;
                                    border-collapse:collapse;
                                "
                            >
                                <tr>
                                    <td
                                        width="48"
                                        valign="middle"
                                        style="
                                            width:48px;
                                            color:#9a3412;
                                            font-family:Segoe UI, Arial, sans-serif;
                                            font-size:23px;
                                            font-weight:700;
                                            line-height:27px;
                                        "
                                    >
                                        {alerta0}
                                    </td>

                                    <td
                                        valign="middle"
                                        style="
                                            padding-left:8px;
                                        "
                                    >
                                        <div
                                            style="
                                                color:#9a3412;
                                                font-family:Segoe UI, Arial, sans-serif;
                                                font-size:11px;
                                                font-weight:700;
                                                line-height:15px;
                                            "
                                        >
                                            ALERTA 0 DÍAS
                                        </div>

                                        <div
                                            style="
                                                margin-top:2px;
                                                color:#9a3412;
                                                font-family:Segoe UI, Arial, sans-serif;
                                                font-size:9px;
                                                line-height:13px;
                                            "
                                        >
                                            Gestionar hoy
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>

            <!-- KPI ALERTA -->

            <td
                width="25%"
                valign="top"
                style="
                    width:25%;
                    padding:0 5px;
                "
            >
                <table
                    role="presentation"
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    border="0"
                    bgcolor="#fffdf3"
                    style="
                        width:100%;
                        background-color:#fffdf3;
                        border:1px solid #f1df9d;
                        border-left:4px solid #eab308;
                        border-collapse:separate;
                        border-radius:8px;
                    "
                >
                    <tr>
                        <td
                            valign="middle"
                            style="
                                padding:10px 11px;
                            "
                        >
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                                style="
                                    width:100%;
                                    border-collapse:collapse;
                                "
                            >
                                <tr>
                                    <td
                                        width="48"
                                        valign="middle"
                                        style="
                                            width:48px;
                                            color:#92400e;
                                            font-family:Segoe UI, Arial, sans-serif;
                                            font-size:23px;
                                            font-weight:700;
                                            line-height:27px;
                                        "
                                    >
                                        {alerta}
                                    </td>

                                    <td
                                        valign="middle"
                                        style="
                                            padding-left:8px;
                                        "
                                    >
                                        <div
                                            style="
                                                color:#92400e;
                                                font-family:Segoe UI, Arial, sans-serif;
                                                font-size:11px;
                                                font-weight:700;
                                                line-height:15px;
                                            "
                                        >
                                            ALERTA
                                        </div>

                                        <div
                                            style="
                                                margin-top:2px;
                                                color:#92400e;
                                                font-family:Segoe UI, Arial, sans-serif;
                                                font-size:9px;
                                                line-height:13px;
                                            "
                                        >
                                            Revisar y acelerar
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>

            <!-- KPI A TIEMPO -->

            <td
                width="25%"
                valign="top"
                style="
                    width:25%;
                    padding:0 0 0 5px;
                "
            >
                <table
                    role="presentation"
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    border="0"
                    bgcolor="#f4fcf7"
                    style="
                        width:100%;
                        background-color:#f4fcf7;
                        border:1px solid #bfe7cd;
                        border-left:4px solid #22c55e;
                        border-collapse:separate;
                        border-radius:8px;
                    "
                >
                    <tr>
                        <td
                            valign="middle"
                            style="
                                padding:10px 11px;
                            "
                        >
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                                style="
                                    width:100%;
                                    border-collapse:collapse;
                                "
                            >
                                <tr>
                                    <td
                                        width="48"
                                        valign="middle"
                                        style="
                                            width:48px;
                                            color:#166534;
                                            font-family:Segoe UI, Arial, sans-serif;
                                            font-size:23px;
                                            font-weight:700;
                                            line-height:27px;
                                        "
                                    >
                                        {tiempo}
                                    </td>

                                    <td
                                        valign="middle"
                                        style="
                                            padding-left:8px;
                                        "
                                    >
                                        <div
                                            style="
                                                color:#166534;
                                                font-family:Segoe UI, Arial, sans-serif;
                                                font-size:11px;
                                                font-weight:700;
                                                line-height:15px;
                                            "
                                        >
                                            A TIEMPO
                                        </div>

                                        <div
                                            style="
                                                margin-top:2px;
                                                color:#166534;
                                                font-family:Segoe UI, Arial, sans-serif;
                                                font-size:9px;
                                                line-height:13px;
                                            "
                                        >
                                            Dentro del ANS
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>

        </tr>
    </table>
    """



# ==========================================================
# GENERAR ACTIVIDADES
# ==========================================================

def generar_actividades(
    correo: dict,
) -> str:
    """
    Construye el bloque de actividades del correo.
    """

    html = ""

    for bloque in correo["bloques"]:

        productos = ", ".join(
            bloque["productos"]
        )

        html += f"""
        <hr>

        <h2 style="color:#0f766e;">
            📦 Producto: {productos}
        </h2>

        <p>
            <b>Total pedidos:</b>
            {bloque['total_pedidos']}
        </p>
        """

        for actividad in bloque["actividades"]:

            resumen_html = generar_resumen(
                actividad["resumen"]
            )

            tabla_html = generar_tabla(
                actividad["tabla"]
            )

            html += f"""
            <div
                style="
                    margin-left:25px;
                    margin-bottom:35px;
                ">

                <h3
                    style="
                        color:#1565c0;
                        margin-bottom:8px;
                    ">

                    📋 Actividad: {actividad['nombre']}

                </h3>

                <p style="margin:4px 0;">

                    <b>Total pedidos:</b>

                    {actividad['total']}

                </p>

                {resumen_html}

                <hr style="
                    border:none;
                    border-top:1px solid #d1d5db;
                    margin:18px 0;
                ">

                <h3 style="
                    color:#0f766e;
                    margin:0 0 12px 0;
                    font-size:16px;
                ">

                    📋 Detalle de pedidos

                </h3>

                {tabla_html}

            </div>
            """

    return html

# ==========================================================
# GENERAR RESUMEN
# ==========================================================

def generar_resumen(
    resumen,
) -> str:
    """
    Genera una tabla resumen ejecutiva por estado.

    Mejoras visuales:
    - Mayor ancho.
    - Tipografía más clara.
    - Filas proporcionadas.
    - Cantidades y porcentajes con mayor jerarquía.
    - Compatible con Outlook Desktop.
    """

    html = """
    <table
        role="presentation"
        width="420"
        cellpadding="0"
        cellspacing="0"
        border="0"
        style="
            width:420px;
            max-width:420px;
            margin:12px 0 20px 0;
            border-collapse:collapse;
            font-family:Segoe UI, Arial, sans-serif;
            font-size:12px;
            color:#1f2937;
        "
    >
        <tr
            bgcolor="#0f766e"
            style="
                background-color:#0f766e;
                color:#ffffff;
            "
        >
            <th
                width="50%"
                height="36"
                style="
                    width:50%;
                    height:36px;
                    padding:0 12px;
                    border:1px solid #0b625c;
                    text-align:center;
                    vertical-align:middle;
                    color:#ffffff;
                    font-family:Segoe UI, Arial, sans-serif;
                    font-size:11px;
                    font-weight:700;
                    line-height:16px;
                    mso-line-height-rule:exactly;
                "
            >
                Estado
            </th>

            <th
                width="25%"
                height="36"
                style="
                    width:25%;
                    height:36px;
                    padding:0 10px;
                    border:1px solid #0b625c;
                    text-align:center;
                    vertical-align:middle;
                    color:#ffffff;
                    font-family:Segoe UI, Arial, sans-serif;
                    font-size:11px;
                    font-weight:700;
                    line-height:16px;
                    mso-line-height-rule:exactly;
                "
            >
                Cantidad
            </th>

            <th
                width="25%"
                height="36"
                style="
                    width:25%;
                    height:36px;
                    padding:0 10px;
                    border:1px solid #0b625c;
                    text-align:center;
                    vertical-align:middle;
                    color:#ffffff;
                    font-family:Segoe UI, Arial, sans-serif;
                    font-size:11px;
                    font-weight:700;
                    line-height:16px;
                    mso-line-height-rule:exactly;
                "
            >
                Porcentaje
            </th>
        </tr>
    """
    # ======================================================
    # ORDEN OPERATIVO DE LOS ESTADOS
    # ======================================================

    resumen = resumen.copy()

    resumen["ORDEN_ESTADO"] = (
        resumen["ESTADO"]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace("_", " ", regex=False)
        .map({
            "VENCIDO": 1,
            "ALERTA 0 DÍAS": 2,
            "ALERTA 0 DIAS": 2,
            "ALERTA": 3,
            "A TIEMPO": 4,
        })
        .fillna(99)
    )

    resumen = (
        resumen
        .sort_values("ORDEN_ESTADO")
        .drop(columns="ORDEN_ESTADO")
    )
    
    for indice, (_, fila) in enumerate(
        resumen.iterrows()
    ):

        estado = (
            str(fila["ESTADO"])
            .strip()
            .upper()
            .replace("_", " ")
        )

        color_fila = (
            "#ffffff"
            if indice % 2 == 0
            else "#f8fafc"
        )

        html += f"""
        <tr
            bgcolor="{color_fila}"
            style="
                background-color:{color_fila};
            "
        >
            <td
                height="38"
                align="center"
                valign="middle"
                style="
                    height:38px;
                    padding:0 10px;
                    border:1px solid #d9dee5;
                    text-align:center;
                    vertical-align:middle;
                    font-family:Segoe UI, Arial, sans-serif;
                    font-size:11px;
                    line-height:15px;
                    mso-line-height-rule:exactly;
                "
            >
                {badge_estado(estado)}
            </td>

            <td
                height="38"
                align="center"
                valign="middle"
                style="
                    height:38px;
                    padding:0 10px;
                    border:1px solid #d9dee5;
                    text-align:center;
                    vertical-align:middle;
                    color:#111827;
                    font-family:Segoe UI, Arial, sans-serif;
                    font-size:13px;
                    font-weight:700;
                    line-height:16px;
                    mso-line-height-rule:exactly;
                "
            >
                {fila['TOTAL']}
            </td>

            <td
                height="38"
                align="center"
                valign="middle"
                style="
                    height:38px;
                    padding:0 10px;
                    border:1px solid #d9dee5;
                    text-align:center;
                    vertical-align:middle;
                    color:#334155;
                    font-family:Segoe UI, Arial, sans-serif;
                    font-size:12px;
                    font-weight:600;
                    line-height:16px;
                    mso-line-height-rule:exactly;
                "
            >
                {fila['PORCENTAJE']}%
            </td>
        </tr>
        """

    html += """
    </table>
    """

    return html



# ==========================================================
# FORMATO ESTADO
# ==========================================================

def badge_estado(estado: str):

    estado = (
        estado
        .strip()
        .upper()
        .replace("_", " ")
    )

    estilos = {

        "VENCIDO": {
            "fondo": "#DC2626",
            "borde": "#991B1B",
            "texto": "#FFFFFF",
        },

        "ALERTA 0 DÍAS": {
            "fondo": "#F97316",
            "borde": "#C2410C",
            "texto": "#FFFFFF",
        },

        "ALERTA 0 DIAS": {
            "fondo": "#F97316",
            "borde": "#C2410C",
            "texto": "#FFFFFF",
        },

        "ALERTA": {
            "fondo": "#FACC15",
            "borde": "#CA8A04",
            "texto": "#3F2B00",
        },

        "A TIEMPO": {
            "fondo": "#22C55E",
            "borde": "#15803D",
            "texto": "#FFFFFF",
        },

    }

    estilo = estilos.get(
        estado,
        {
            "fondo": "#64748B",
            "borde": "#475569",
            "texto": "#FFFFFF",
        },
    )

    return f"""
<table
    role="presentation"
    cellpadding="0"
    cellspacing="0"
    border="0"
    align="center"
    style="
        margin:auto;
        border-collapse:separate;
    "
>
    <tr>

        <td
            bgcolor="{estilo['fondo']}"
            align="center"
            valign="middle"
            style="
                background-color:{estilo['fondo']};

                border-top:1px solid {estilo['borde']};
                border-left:1px solid {estilo['borde']};
                border-right:1px solid {estilo['borde']};
                border-bottom:none;

                padding:5px 12px;

                min-width:88px;

                color:{estilo['texto']};

                font-family:'Segoe UI', Arial, sans-serif;

                font-size:10px;

                font-weight:700;

                text-align:center;

                white-space:nowrap;

                line-height:12px;

                mso-line-height-rule:exactly;
            "
        >
            {estado}
        </td>

    </tr>
</table>
"""

# ==========================================================
# GENERAR TABLA
# ==========================================================

def generar_tabla(df) -> str:
    """
    Genera la tabla HTML manteniendo exactamente
    las columnas y el orden del DataFrame.

    Mejoras visuales:
    - Filas más compactas.
    - Altura controlada para Outlook.
    - Tipografía más clara.
    - Encabezado corporativo.
    - Estados en badges compactos.
    """

    html = """
    <table
        role="presentation"
        width="100%"
        cellpadding="0"
        cellspacing="0"
        border="0"
        style="
            width:100%;
            border-collapse:collapse;
            margin-top:10px;
            margin-bottom:24px;
            table-layout:auto;
            color:#1f2937;
            font-family:Segoe UI, Arial, sans-serif;
            font-size:10px;
        "
    >
    """

    # ======================================================
    # ENCABEZADO
    # ======================================================

    html += """
    <tr
        bgcolor="#0f766e"
        style="
            background-color:#0f766e;
            color:#ffffff;
        "
    >
    """

    for columna in df.columns:

        html += f"""
        <th
            height="34"
            valign="middle"
            style="
                height:34px;
                padding:0 6px;
                border:1px solid #d5dde5;
                background-color:#0f766e;
                color:#ffffff;
                text-align:center;
                vertical-align:middle;
                white-space:nowrap;
                font-family:Segoe UI, Arial, sans-serif;
                font-size:9px;
                font-weight:700;
                line-height:13px;
                mso-line-height-rule:exactly;
            "
        >
            {columna}
        </th>
        """

    html += "</tr>"

    # ======================================================
    # ORDEN OPERATIVO
    # ======================================================

    df = df.copy()

    df["ORDEN_ESTADO"] = (
        df["ESTADO"]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace("_", " ", regex=False)
        .map({
            "VENCIDO": 1,
            "ALERTA 0 DÍAS": 2,
            "ALERTA 0 DIAS": 2,
            "ALERTA": 3,
            "A TIEMPO": 4,
        })
        .fillna(99)
    )

    df = df.sort_values(
        by=[
            "ORDEN_ESTADO",
            "DIAS_RESTANTES",
        ],
        ascending=[
            True,
            True,
        ],
    )

    df = df.drop(
        columns="ORDEN_ESTADO"
    )

    # ======================================================
    # FILAS
    # ======================================================

    for indice, (_, fila) in enumerate(
        df.iterrows()
    ):

        color_fila = (
            "#ffffff"
            if indice % 2 == 0
            else "#f8fafc"
        )

        html += f"""
        <tr
            bgcolor="{color_fila}"
            style="
                background-color:{color_fila};
            "
        >
        """

        for columna in df.columns:

            valor = fila[columna]

            if valor is None:

                valor = ""

            else:

                valor = str(valor)

            # ----------------------------------------------
            # ESTADO
            # ----------------------------------------------

            if columna == "ESTADO":

                valor = badge_estado(valor)

            # ----------------------------------------------
            # ALINEACIÓN
            # ----------------------------------------------

            alineacion = "left"

            if columna in [
                "PEDIDO",
                "MUNICIPIO",
                "TIPO_DIRECCION",
                "CONCEPTO",
                "ACTIVIDAD",
                "PRODUCTO_ID",
                "DIAS_PACTADOS",
                "DIAS_RESTANTES",
                "ESTADO",
            ]:

                alineacion = "center"

            # ----------------------------------------------
            # ESTILO POR COLUMNA
            # ----------------------------------------------

            if columna == "DIRECCION":

                estilo_extra = """
                    white-space:normal;
                    word-break:break-word;
                    max-width:230px;
                """

            elif columna in [
                "FECHA_INICIO_ANS",
                "FECHA_LIMITE_ANS",
            ]:

                estilo_extra = """
                    white-space:nowrap;
                    min-width:112px;
                """

            else:

                estilo_extra = """
                    white-space:nowrap;
                """

            # ----------------------------------------------
            # CELDA
            # ----------------------------------------------

            html += f"""
            <td
                height="30"
                valign="middle"
                style="
                    height:30px;
                    padding:3px 6px;
                    border:1px solid #e2e8f0;
                    vertical-align:middle;
                    text-align:{alineacion};
                    color:#1f2937;
                    font-family:Segoe UI, Arial, sans-serif;
                    font-size:10px;
                    font-weight:400;
                    line-height:14px;
                    mso-line-height-rule:exactly;
                    {estilo_extra}
                "
            >
                {valor}
            </td>
            """

        html += "</tr>"

    html += """
    </table>
    """

    return html



# ==========================================================
# LEER FOOTER
# ==========================================================

PLANTILLA_FOOTER = (
    CARPETA_TEMPLATES
    / "footer.html"
)


def leer_footer():

    with open(
        PLANTILLA_FOOTER,
        "r",
        encoding="utf-8",
    ) as archivo:

        return archivo.read()


# ==========================================================
# GENERAR FOOTER
# ==========================================================

def generar_footer(correo):

    html = leer_footer()

    vencidos = 0
    alerta0 = 0

    for bloque in correo["bloques"]:

        for actividad in bloque["actividades"]:

            resumen = actividad["resumen"]

            for _, fila in resumen.iterrows():

                estado = (
                    str(fila["ESTADO"])
                    .strip()
                    .upper()
                    .replace("_", " ")
                )

                total = int(fila["TOTAL"])

                if estado == "VENCIDO":

                    vencidos += total

                elif estado in (

                    "ALERTA 0 DÍAS",
                    "ALERTA 0 DIAS",

                ):

                    alerta0 += total

    # ------------------------------------------------------
    # MENSAJE DINÁMICO
    # ------------------------------------------------------

    mensaje = ""

    if vencidos > 0:

        mensaje += (
            f"Favor gestionar con prioridad los "
            f"<b>{vencidos}</b> pedidos que actualmente "
            f"se encuentran en estado <b>VENCIDO</b>."
        )

    if alerta0 > 0:

        if mensaje:

            mensaje += "<br><br>"

            texto_inicio = "Así mismo, dar celeridad a los"

        else:

            texto_inicio = "Favor gestionar con prioridad los"

        mensaje += (
            f"{texto_inicio} "
            f"<b>{alerta0}</b> pedidos que se encuentran en "
            f"<b>ALERTA 0 DÍAS</b>, con el fin de evitar su "
            f"vencimiento."
        )

    if mensaje == "":

        mensaje = (
            "Actualmente no existen pedidos vencidos "
            "ni pedidos en ALERTA 0 DÍAS. "
            "Continuar con el seguimiento preventivo."
        )

    html = html.replace(
        "{{MENSAJE}}",
        mensaje,
    )

    return html
        