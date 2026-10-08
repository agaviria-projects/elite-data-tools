from pathlib import Path
import pandas as pd
from html import escape

def normalizar_estado(serie):
    return serie.astype(str).str.strip().str.upper().str.replace("_", " ", regex=False)


def obtener_vencidos_epm(df):
    """Usa el cálculo del archivo de entrada; no recalcula plazos."""
    if df.empty:
        return pd.Series(False, index=df.index, dtype=bool)
    if "ESTADO_EPM" in df.columns:
        estados = normalizar_estado(df["ESTADO_EPM"])
        validos = {"VENCIDO", "DENTRO DEL PLAZO", "SIN FECHA", "SIN REGLA EPM"}
        if not estados.isin(validos).all():
            raise ValueError("ESTADO_EPM contiene valores vacíos o desconocidos. Revisar FENIX_ANS y el lector.")
        vencidos = estados.eq("VENCIDO")
        if "VENCIDO_EPM" in df.columns:
            indicador = pd.to_numeric(df["VENCIDO_EPM"], errors="coerce")
            if not indicador.isin([0, 1]).all() or not indicador.eq(1).equals(vencidos):
                raise ValueError("VENCIDO_EPM y ESTADO_EPM no coinciden. Revisar el archivo de entrada.")
        return vencidos
    raise ValueError(
        "Falta ESTADO_EPM en los pedidos del correo. El lector/agrupador debe conservar "
        "ESTADO_EPM, FECHA_LIMITE_EPM y DIAS_RESTANTES_EPM de FENIX_ANS. "
        "No se puede interpretar la ausencia de datos EPM como cero vencidos."
    )


def contar_epm_correo(correo):
    return sum(int(obtener_vencidos_epm(a["tabla"]).sum())
               for b in correo["bloques"] for a in b["actividades"])


def nota_epm(df):
    if df.empty:
        return "EPM incluidos en ELITE · No sumar"
    epm = obtener_vencidos_epm(df)
    elite = normalizar_estado(df["ESTADO"]).eq("VENCIDO")
    if (epm & ~elite).any():
        return "ELITE y EPM se evalúan por separado · No sumar"
    return "EPM incluidos en ELITE · No sumar"


def badge_epm(estado):
    estado = str(estado).strip().upper()
    fondo, texto = {"VENCIDO": ("#991b1b", "#ffffff"),
                    "DENTRO DEL PLAZO": ("#e0f2fe", "#075985")}.get(
                        estado, ("#f1f5f9", "#475569"))
    return (f'<span style="display:inline-block;padding:5px 9px;'
            f'background-color:{fondo};color:{texto};font-size:10px;'
            f'font-weight:700;white-space:nowrap;">{escape(estado)}</span>')


def resumen_epm_html(df):
    cantidad = int(obtener_vencidos_epm(df).sum())
    porcentaje = round(cantidad / len(df) * 100, 1) if len(df) else 0.0
    return f"""<table role="presentation" width="420" cellpadding="0" cellspacing="0"
        style="width:420px;border-collapse:collapse;margin:-8px 0 20px 0;font-family:Segoe UI,Arial,sans-serif;">
        <tr><td style="padding:10px 12px;background:#fff1f2;border:1px solid #fecdd3;">
        <b style="color:#991b1b;font-size:11px;">VENCIDOS EPM</b>
        <span style="color:#991b1b;font-size:15px;font-weight:700;">&nbsp; {cantidad}</span>
        <span style="color:#64748b;font-size:11px;">&nbsp; ({porcentaje:.1f}% del total de esta actividad/zona)</span>
        <div style="font-size:10px;color:#64748b;padding-top:4px;">{nota_epm(df)}</div>
        </td></tr></table>"""

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
    Genera el correo completo reutilizando la misma plantilla.
    Para METROPOLITANA conserva la separación actual por
    producto y actividad.
    Para SUROESTE y OCCIDENTE genera un único resumen y un
    único detalle con todos los pedidos de la zona.
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
    fecha_corte = correo.get(
        "fecha_corte",
        "",
    )
    html = html.replace(
        "{{FECHA}}",
        fecha_corte,
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
    # ======================================================
    # CONTENIDO SEGÚN TIPO DE CORREO
    # ======================================================
    if correo.get("tipo_correo") == "ZONA":
        contenido = generar_contenido_zona(
            correo
        )
    else:
        contenido = generar_actividades(
            correo
        )
    html = html.replace(
        "{{ACTIVIDADES}}",
        contenido,
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
    """Cuatro tarjetas; la primera distingue plazo operativo y contractual."""
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
    epm = contar_epm_correo(correo)
    tablas = [a["tabla"] for b in correo["bloques"] for a in b["actividades"]]
    nota = nota_epm(pd.concat(tablas, ignore_index=True)) if tablas else "EPM incluidos en ELITE · No sumar"
    doble = f"""<td width="25%" valign="top" style="width:25%;padding-right:5px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="width:100%;border-collapse:collapse;border:1px solid #fecdd3;border-left:4px solid #dc2626;background:#fff7f7;">
       <tr><td width="50%" valign="top" style="padding:8px 9px;border-right:1px solid #fecdd3;">
        <div style="font-size:22px;line-height:26px;font-weight:700;color:#b91c1c;">{vencidos}</div>
        <div style="font-size:10px;font-weight:700;color:#b91c1c;">VENCIDOS ELITE</div>
        <div style="font-size:9px;line-height:13px;color:#7f1d1d;">Plazo operativo</div>
       </td><td width="50%" valign="top" style="padding:8px 9px;background:#ffe4e6;">
        <div style="font-size:22px;line-height:26px;font-weight:700;color:#881337;">{epm}</div>
        <div style="font-size:10px;font-weight:700;color:#881337;">VENCIDOS EPM</div>
        <div style="font-size:9px;line-height:13px;color:#881337;">Plazo contractual</div>
       </td></tr><tr><td colspan="2" style="padding:4px 8px;border-top:1px solid #fecdd3;font-size:9px;line-height:12px;color:#7f1d1d;">{nota}</td></tr>
      </table></td>"""
    tarjetas = [doble]
    for cantidad, titulo, detalle, fondo, color, borde in [
        (alerta0, "ALERTA 0 DÍAS", "Gestionar hoy", "#fff8f1", "#9a3412", "#f97316"),
        (alerta, "ALERTA", "Revisar y acelerar", "#fffdf3", "#92400e", "#eab308"),
        (tiempo, "A TIEMPO", "Dentro del ANS ELITE", "#f4fcf7", "#166534", "#22c55e"),
    ]:
        tarjetas.append(f"""<td width="25%" valign="top" style="width:25%;padding:0 5px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="width:100%;border-collapse:collapse;background:{fondo};border:1px solid {borde};border-left:4px solid {borde};">
         <tr><td height="82" valign="middle" style="height:82px;padding:0 11px;">
          <table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr>
           <td style="font-size:23px;font-weight:700;color:{color};padding-right:8px;">{cantidad}</td>
           <td><div style="font-size:11px;font-weight:700;color:{color};">{titulo}</div>
            <div style="font-size:9px;line-height:13px;padding-top:3px;color:{color};">{detalle}</div></td>
          </tr></table></td></tr></table></td>""")
    return ('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            'style="width:100%;border-collapse:collapse;margin:10px 0 16px;font-family:Segoe UI,Arial,sans-serif;">'
            '<tr>' + ''.join(tarjetas) + '</tr></table>')
# ==========================================================
# GENERAR CONTENIDO PARA CORREOS POR ZONA
# ==========================================================
def generar_contenido_zona(
    correo: dict,
) -> str:
    """
    Genera un único bloque para SUROESTE u OCCIDENTE.
    A diferencia de METROPOLITANA:
    - No separa por producto.
    - No separa por actividad.
    - Presenta un único resumen por estado.
    - Presenta un único detalle con todos los pedidos de la zona.
    El diseño visual reutiliza los mismos componentes del
    correo metropolitano para mantener uniformidad.
    """
    bloques = correo.get(
        "bloques",
        [],
    )
    if not bloques:
        return ""
    bloque = bloques[0]
    actividades = bloque.get(
        "actividades",
        [],
    )
    if not actividades:
        return ""
    actividad = actividades[0]
    resumen_html = generar_resumen(
        actividad["resumen"]
    ) + resumen_epm_html(actividad["tabla"])
    tabla_html = generar_tabla(
        actividad["tabla"],
        correo["grupo"],
    )
    total_pedidos = correo.get(
        "total_pedidos",
        actividad.get(
            "total",
            0,
        ),
    )
    zona = correo.get(
        "zona",
        correo.get(
            "subzona",
            correo.get(
                "grupo",
                "",
            ),
        ),
    )
    return f"""
    <div
        style="
            margin-bottom:35px;
        "
    >
        <h2
            style="
                color:#0f766e;
                margin:0 0 8px 0;
                font-size:18px;
            "
        >
            📍 Zona: {zona}
        </h2>
        <p
            style="
                margin:4px 0 12px 0;
            "
        >
            <b>Total pedidos:</b>
            {total_pedidos}
        </p>
        <h3
            style="
                color:#1565c0;
                margin:12px 0 8px 0;
                font-size:16px;
            "
        >
            📊 Resumen general
        </h3>
        {resumen_html}
        <hr
            style="
                border:none;
                border-top:1px solid #d1d5db;
                margin:18px 0;
            "
        >
        <h3
            style="
                color:#0f766e;
                margin:0 0 12px 0;
                font-size:16px;
            "
        >
            📋 Detalle de pedidos
        </h3>
        {tabla_html}
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
            resumen_html = generar_resumen(
                actividad["resumen"]
            ) + resumen_epm_html(actividad["tabla"])
            tabla_html = generar_tabla(
                actividad["tabla"],
                correo["grupo"],
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
                {badge_estado("VENCIDO ELITE" if estado == "VENCIDO" else estado)}
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
        "VENCIDO ELITE": {"fondo": "#DC2626", "borde": "#991B1B", "texto": "#FFFFFF"},
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
def generar_tabla(
    df,
    grupo,
) -> str:
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
    df = df.copy(deep=True)
    df = df.drop(columns=["SUBZONA"], errors="ignore")
    obtener_vencidos_epm(df)
    columnas_epm = ["ESTADO_EPM", "FECHA_LIMITE_EPM", "DIAS_RESTANTES_EPM"]
    faltantes = [c for c in columnas_epm if c not in df.columns]
    if faltantes:
        raise ValueError("El lector/agrupador eliminó columnas EPM del detalle: " + ", ".join(faltantes))
    # Indicadores y días pactados EPM son de cálculo; el correo muestra estado y plazo.
    originales = [c for c in df.columns if c not in columnas_epm +
                  ["VENCIDO_ELITE", "VENCIDO_EPM", "DIAS_PACTADOS_EPM"]]
    df = df[originales + columnas_epm]
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
    # OBSERVACIÓN SOLO PARA PUNTOS DE CONEXIÓN
    # ======================================================
    if (
        grupo == "PUNTOS DE CONEXIÓN"
        and "ACTIVIDAD" in df.columns
        and "SUBPED" in df.columns
    ):
        if "OBSERVACION" in df.columns:
            df = df.drop(columns="OBSERVACION")
        df.insert(loc=1, column="OBSERVACION", value="")
        # ======================================================
        # PEDIDOS SISTEMA PARRILLA
        # ======================================================
        ruta_parrilla = (
            BASE_DIR
            / "config"
            / "SISTEMA_PARRILLA.xlsx"
        )
        if ruta_parrilla.exists():
            df_parrilla = pd.read_excel(
                ruta_parrilla,
                dtype=str,
            )
            pedidos_parrilla = (
                df_parrilla["PEDIDO"]
                .astype(str)
                .str.strip()
            )
            mask_parrilla = (
                df["PEDIDO"]
                .astype(str)
                .str.strip()
                .isin(pedidos_parrilla)
            )
            df.loc[
                mask_parrilla,
                "OBSERVACION"
            ] = "SISTEMA PARRILLA"
        mask = (
            df["OBSERVACION"].eq("")
            &
            df["ACTIVIDAD"]
            .astype(str)
            .str.strip()
            .str.upper()
            .eq("ACREV")
            &
            (
                df["SUBPED"]
                .astype(str)
                .str.strip()
                != "1"
            )
        )
        df.loc[
            mask,
            "OBSERVACION"
        ] = "RECONSIDERACION"
    # ======================================================
    # OCULTAR COLUMNAS EN LOS DEMÁS CORREOS
    # ======================================================
    else:
        df = df.drop(
            columns=[
                c for c in (
                    "OBSERVACION",
                    "SUBPED",
                )
                if c in df.columns
            ]
        )
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
        titulo = {"ESTADO": "ESTADO ELITE", "ESTADO_EPM": "ESTADO EPM",
                  "FECHA_LIMITE_EPM": "FECHA LÍMITE EPM",
                  "DIAS_RESTANTES_EPM": "DÍAS RESTANTES EPM"}.get(columna, columna)
        color_encabezado = "#881337" if columna in columnas_epm else "#0f766e"
        if columna == "OBSERVACION":
            titulo = "OBSERVACIÓN"
        ancho_extra = ""
        if columna == "SUBPED":
            ancho_extra = """
                min-width:65px;
                width:65px;
            """
        html += f"""
        <th
            height="34"
            valign="middle"
            style="
                height:34px;
                padding:0 6px;
                border:1px solid #d5dde5;
                background-color:{color_encabezado};
                color:#ffffff;
                text-align:center;
                vertical-align:middle;
                white-space:nowrap;
                font-family:Segoe UI, Arial, sans-serif;
                font-size:9px;
                font-weight:700;
                line-height:13px;
                mso-line-height-rule:exactly;
                {ancho_extra}
            "
        >
            {titulo}
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
            if columna == "OBSERVACION":
                if valor == "RECONSIDERACION":
                    valor = """
                    <span
                        style="
                            display:inline-block;
                            padding:3px 8px;
                            background:#DBEAFE;
                            color:#1D4ED8;
                            border:1px solid #93C5FD;
                            border-radius:12px;
                            font-family:'Segoe UI', Arial, sans-serif;
                            font-size:10px;
                            font-weight:700;
                            white-space:nowrap;
                        "
                    >
                        RECONSIDERACIÓN
                    </span>
                    """
                elif valor == "SISTEMA PARRILLA":
                    valor = """
                    <span
                        style="
                            display:inline-block;
                            padding:3px 10px;
                            background:#F3E8FF;
                            color:#7E22CE;
                            border:1px solid #D8B4FE;
                            border-radius:12px;
                            font-family:'Segoe UI', Arial, sans-serif;
                            font-size:10px;
                            font-weight:700;
                            white-space:nowrap;
                        "
                    >
                        SISTEMA PARRILLA
                    </span>
                    """
            elif columna == "ESTADO":
                valor = badge_estado(valor)
            elif columna == "ESTADO_EPM":
                valor = badge_epm(valor)
            elif columna == "DIAS_RESTANTES_EPM":
                valor = "—" if pd.isna(fila[columna]) else escape(valor)
            elif columna == "FECHA_LIMITE_EPM":
                valor = "—" if pd.isna(fila[columna]) else escape(valor)
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
                "ESTADO_EPM",
                "DIAS_RESTANTES_EPM",
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
                "FECHA_LIMITE_EPM",
            ]:
                estilo_extra = """
                    white-space:nowrap;
                    min-width:112px;
                """
            elif columna == "SUBPED":
                estilo_extra = """
                    white-space:nowrap;
                    text-align:center;
                    min-width:65px;
                    width:65px;
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
    tablas = [a["tabla"] for b in correo["bloques"] for a in b["actividades"]]
    df = pd.concat(tablas, ignore_index=True) if tablas else pd.DataFrame(columns=["ESTADO", "ESTADO_EPM"])
    elite = normalizar_estado(df["ESTADO"])
    epm = obtener_vencidos_epm(df)
    vencidos_elite = int(elite.eq("VENCIDO").sum())
    vencidos_epm = int(epm.sum())
    preventivos = int((elite.eq("VENCIDO") & normalizar_estado(df["ESTADO_EPM"]).eq("DENTRO DEL PLAZO")).sum())
    alerta0 = int(elite.isin(["ALERTA 0 DÍAS", "ALERTA 0 DIAS"]).sum())
    partes = []
    if vencidos_elite:
        partes.append(f"Se registran <b>{vencidos_elite} vencidos ELITE</b> según el plazo operativo.")
    if preventivos:
        partes.append(f"Priorizar visita y cierre de los <b>{preventivos} vencidos ELITE que aún están dentro del plazo EPM</b>, para evitar el incumplimiento contractual.")
    if vencidos_epm:
        partes.append(f"Los <b>{vencidos_epm} vencidos EPM</b> ya superaron el plazo contractual: gestionar su cierre y seguimiento. {nota_epm(df)}.")
    if alerta0:
        partes.append(f"Dar celeridad a los <b>{alerta0} pedidos en ALERTA 0 DÍAS ELITE</b>.")
    if not partes:
        partes.append("No existen vencidos ELITE, vencidos EPM ni pedidos en ALERTA 0 DÍAS. Continuar el seguimiento preventivo.")
    sin_evaluar = int(normalizar_estado(df["ESTADO_EPM"]).isin(["SIN FECHA", "SIN REGLA EPM"]).sum())
    if sin_evaluar:
        partes.append(f"<b>{sin_evaluar} pedidos sin evaluación EPM</b> por falta de fecha o regla. No se interpretan como dentro del plazo.")
    return html.replace("{{MENSAJE}}", "<br><br>".join(partes))
