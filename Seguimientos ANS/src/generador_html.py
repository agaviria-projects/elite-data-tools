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

    return html
# ==========================================================
# RESUMEN EJECUTIVO
# ==========================================================

def generar_resumen_ejecutivo(correo):

    vencidos = 0
    alerta0 = 0
    alerta = 0
    tiempo = 0

    for bloque in correo["bloques"]:

        for actividad in bloque["actividades"]:

            resumen = actividad["resumen"]

            for _, fila in resumen.iterrows():

                estado = str(fila["ESTADO"]).upper()

                total = int(fila["TOTAL"])

                if estado == "VENCIDO":
                    vencidos += total

                elif estado in ("ALERTA_0 DÍAS", "ALERTA_0 DIAS"):
                    alerta0 += total

                elif estado == "ALERTA":
                    alerta += total

                elif estado == "A TIEMPO":
                    tiempo += total

    return f"""
    <div style="
        margin:20px 0;
        display:flex;
        gap:15px;
        font-family:Segoe UI;
    ">

        <div style="
            flex:1;
            background:#fee2e2;
            padding:12px;
            border-radius:8px;
            text-align:center;
        ">
            <div style="font-size:26px;font-weight:bold;color:#991b1b;">
                {vencidos}
            </div>
            <div>🔴 Vencidos</div>
        </div>

        <div style="
            flex:1;
            background:#fed7aa;
            padding:12px;
            border-radius:8px;
            text-align:center;
        ">
            <div style="font-size:26px;font-weight:bold;color:#9a3412;">
                {alerta0}
            </div>
            <div>🟠 Alerta 0 días</div>
        </div>

        <div style="
            flex:1;
            background:#fef3c7;
            padding:12px;
            border-radius:8px;
            text-align:center;
        ">
            <div style="font-size:26px;font-weight:bold;color:#92400e;">
                {alerta}
            </div>
            <div>🟡 Alerta</div>
        </div>

        <div style="
            flex:1;
            background:#d1fae5;
            padding:12px;
            border-radius:8px;
            text-align:center;
        ">
            <div style="font-size:26px;font-weight:bold;color:#166534;">
                {tiempo}
            </div>
            <div>🟢 A Tiempo</div>
        </div>

    </div>
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

            # ------------------------------------------
            # RESUMEN DE LA ACTIVIDAD
            # ------------------------------------------

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
                    margin-bottom:25px;
                ">

                <h3
                    style="
                        color:#1565c0;
                        margin-bottom:5px;
                    ">

                    📋 {actividad['nombre']}

                </h3>

                <p>

                    <b>Total pedidos:</b>

                    {actividad['total']}

                </p>

                {resumen_html}

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
    Genera la tabla resumen por estado.
    """

    colores = {

        "VENCIDO": "#dc2626",

        "ALERTA_0 DÍAS": "#f97316",

        "ALERTA": "#facc15",

        "A TIEMPO": "#16a34a",

    }

    html = """
    <table
        style="
            width:420px;
            border-collapse:collapse;
            margin-top:10px;
            margin-bottom:20px;
            font-size:13px;
        ">
    """

    html += """
        <tr
            style="
                background:#0f766e;
                color:white;
            ">

            <th style="padding:8px;">Estado</th>

            <th style="padding:8px;">Cantidad</th>

            <th style="padding:8px;">%</th>

        </tr>
    """

    for _, fila in resumen.iterrows():

        estado = fila["ESTADO"]

        color = colores.get(
            estado,
            "#6b7280"
        )

        html += f"""

        <tr>

            <td
                style="
                    padding:6px;
                    border:1px solid #ddd;
                ">

                <span style="color:{color};">●</span>

                {estado}

            </td>

            <td
                align="center"
                style="border:1px solid #ddd;">

                {fila['TOTAL']}

            </td>

            <td
                align="center"
                style="border:1px solid #ddd;">

                {fila['PORCENTAJE']}%

            </td>

        </tr>

        """

    html += "</table>"

    return html

# ==========================================================
# BADGE ESTADO
# ==========================================================

def badge_estado(estado: str) -> str:
    """
    Devuelve una etiqueta HTML coloreada según el estado.
    """

    estado = estado.strip().upper()

    texto_mostrar = estado.replace("_", " ")

    colores = {

        "A TIEMPO": (
            "#d1fae5",
            "#166534",
        ),

        "ALERTA": (
            "#fef3c7",
            "#92400e",
        ),

        "ALERTA_0 DÍAS": (
            "#fed7aa",
            "#9a3412",
        ),

        "ALERTA_0 DIAS": (
            "#fed7aa",
            "#9a3412",
        ),

        "VENCIDO": (
            "#fee2e2",
            "#991b1b",
        ),

    }

    fondo, texto = colores.get(
        estado,
        ("#f3f4f6", "#374151")
    )

    return f"""
    <span
        style="
            display:inline-block;
            min-width:95px;
            text-align:center;
            background:{fondo};
            color:{texto};
            padding:4px 8px;
            border-radius:14px;
            font-weight:600;
            font-size:11px;
            white-space:nowrap;
            box-sizing:border-box;
        ">
        {texto_mostrar}
    </span>
    """

# ==========================================================
# GENERAR TABLA
# ==========================================================

def generar_tabla(df) -> str:
    """
    Genera una tabla HTML manteniendo exactamente
    las columnas y el orden del DataFrame.
    """

    html = """
    <table
        style="
            width:100%;
            border-collapse:collapse;
            margin-top:15px;
            margin-bottom:30px;
            font-size:12px;
            font-family:Segoe UI, Arial, sans-serif;
        ">
    """

    # ======================================================
    # ENCABEZADO
    # ======================================================

    html += """
    <tr style="
        background:#0f766e;
        color:white;
    ">
    """

    for columna in df.columns:

        html += f"""
        <th
            style="
                padding:8px;
                border:1px solid #d1d5db;
                text-align:center;
                white-space:nowrap;
            ">

            {columna}

        </th>
        """

    html += "</tr>"
    # ======================================================
    # ORDEN OPERATIVO
    # ======================================================

    orden_estados = {

        "VENCIDO": 1,

        "ALERTA_0 DÍAS": 2,
        "ALERTA_0 DIAS": 2,

        "ALERTA": 3,

        "A TIEMPO": 4,

    }

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

        ]

    )

    df = df.drop(
        columns="ORDEN_ESTADO"
    )
    # ======================================================
    # FILAS
    # ======================================================

    for i, (_, fila) in enumerate(df.iterrows()):

        color_fila = "#ffffff" if i % 2 == 0 else "#f8fafc"

        html += f"""
        <tr style="background:{color_fila};">
        """

        for columna in df.columns:

            valor = fila[columna]

            if valor is None:
                valor = ""

            else:
                valor = str(valor)

            if columna == "ESTADO":

                valor = badge_estado(str(valor))

            html += f"""
            <td
                style="
                    padding:6px;
                    border:1px solid #e5e7eb;
                    vertical-align:top;
                ">

                {valor}

            </td>
            """

        html += "</tr>"

    html += "</table>"

    return html