from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from inspect import getsourcefile
from time import perf_counter

import pandas as pd

from modules.informe_ans.config.parametros import (
    CARPETA_HTML,
    SUBZONA_PROCESAR,
)
from modules.informe_ans.config.zonas import (
    ZONAS,
    zona_habilitada_revision,
    zona_habilitada_envio,
)

from modules.informe_ans.models import (
    ConfiguracionEjecucion,
    ResultadoEjecucion,
)
from modules.informe_ans.src.agrupador import construir_informes
from modules.informe_ans.src.generador_correo import construir_correos
from modules.informe_ans.src.generador_html import generar_html
from modules.informe_ans.src.lector_excel import leer_excel
from modules.informe_ans.src.outlook import abrir_correo_outlook
from modules.informe_ans.src.validador import validar_archivo_fenix


CallbackMensaje = Callable[[str], None]



# Diagnóstico temporal: no altera datos, estados ni cálculos.
def registrar_origen_ans(informar, df, etapa):
    campos = [
        "PEDIDO", "FECHA_INICIO_ANS", "FECHA_LIMITE_ANS",
        "FECHA_LIMITE_EPM", "ESTADO", "ESTADO_EPM", "SUBZONA",
    ]
    if etapa == "LECTURA":
        ruta = leer_excel.__globals__.get("ARCHIVO_FENIX")
        informar("🔎 DIAGNÓSTICO ANS — origen real de esta ejecución")
        if ruta is not None:
            ruta = Path(ruta).resolve()
            informar(f"   Excel leído: {ruta}")
            if ruta.is_file():
                fecha = datetime.fromtimestamp(ruta.stat().st_mtime)
                informar(f"   Última modificación del Excel: {fecha:%d/%m/%Y %H:%M:%S}")
        else:
            informar("   El lector no expone ARCHIVO_FENIX en sus variables globales.")
        informar(f"   Lector ejecutado: {getsourcefile(leer_excel)}")
        informar(f"   Generador HTML ejecutado: {getsourcefile(generar_html)}")
    if "PEDIDO" not in df.columns:
        informar(f"   {etapa}: falta la columna PEDIDO.")
        return
    pedidos = df["PEDIDO"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    encontrados = df.loc[pedidos.eq("23601040")]
    if encontrados.empty:
        informar(f"   {etapa}: el pedido 23601040 no está en este bloque.")
        return
    for indice, fila in encontrados.iterrows():
        informar(f"   {etapa} — pedido 23601040, índice {indice}:")
        for campo in campos:
            if campo in df.columns:
                informar(f"      {campo}: {fila[campo]}")


def ejecutar_informe_ans(
    configuracion: ConfiguracionEjecucion,
    informar: CallbackMensaje,
) -> ResultadoEjecucion:
    """
    Ejecuta el proceso completo de Seguimiento ANS.

    Modos disponibles:
    - METROPOLITANA: conserva el flujo actual de 4 correos.
    - SUROESTE: genera 1 correo con todos los pedidos de la zona.
    - OCCIDENTE: genera 1 correo con todos los pedidos de la zona.
    - TODAS: genera los 4 correos metropolitanos + SUROESTE + OCCIDENTE.

    El runner coordina el proceso y no modifica el archivo FENIX_ANS.xlsx.
    """

    inicio = perf_counter()

    zonas = normalizar_zonas(
        configuracion.zonas
    )

    if not zonas:
        raise ValueError(
            "Debe seleccionar al menos una zona."
        )

    zonas_desconocidas = [
        zona
        for zona in zonas
        if zona not in ZONAS
    ]

    if zonas_desconocidas:
        raise ValueError(
            "Zona(s) no válida(s): "
            + ", ".join(zonas_desconocidas)
        )

    if configuracion.enviar_automaticamente:

        zonas_no_autorizadas = [
            zona
            for zona in zonas
            if not zona_habilitada_envio(zona)
        ]

        if zonas_no_autorizadas:
            raise ValueError(
                "No está autorizado el envío automático para: "
                + ", ".join(zonas_no_autorizadas)
            )

    else:

        zonas_no_disponibles = [
            zona
            for zona in zonas
            if not zona_habilitada_revision(zona)
        ]

        if zonas_no_disponibles:
            raise ValueError(
                "Zona(s) no disponible(s) para revisión: "
                + ", ".join(zonas_no_disponibles)
            )

    informar("=" * 68)
    informar("SEGUIMIENTO INTELIGENTE ANS")
    informar("=" * 68)

    informar(
        "📍 Zonas seleccionadas: "
        + ", ".join(zonas)
    )

    informar("📄 Validando archivo FENIX...")

    validar_archivo_fenix()

    informar("✅ Archivo válido.")

    informar("📖 Leyendo información...")

    df = leer_excel()
    registrar_origen_ans(informar, df, "LECTURA")

    informar(
        f"✅ Registros cargados: {len(df):,}"
    )

    # ======================================================
    # CONSTRUIR CORREOS SEGÚN ZONA
    # ======================================================

    correos = []

    for zona in zonas:

        if zona == "METROPOLITANA":

            informar(
                "📊 Construyendo correos de METROPOLITANA..."
            )

            df_metro = df[
                df["SUBZONA"]
                .astype(str)
                .str.strip()
                .str.upper()
                .eq(
                    str(SUBZONA_PROCESAR)
                    .strip()
                    .upper()
                )
            ].copy()

            informar(
                f"   Registros METROPOLITANA: "
                f"{len(df_metro):,}"
            )

            informes_metro = construir_informes(
                df_metro
            )

            correos_metro = construir_correos(
                informes_metro
            )

            correos.extend(
                correos_metro
            )

            informar(
                f"✅ Correos metropolitanos preparados: "
                f"{len(correos_metro)}"
            )

            continue

        informar(
            f"📊 Filtrando pedidos de {zona}..."
        )

        correo_zona = construir_correo_zona(
            df=df,
            zona=zona,
        )

        if correo_zona is not None:

            correos.append(
                correo_zona
            )

            informar(
                f"✅ Correo {zona} preparado: "
                f"{correo_zona['total_pedidos']:,} pedidos."
            )

        else:

            informar(
                f"⚠ {zona} no tiene pedidos para procesar."
            )

    if not correos:
        raise ValueError(
            f"No se encontraron correos para procesar "
            "en las zonas seleccionadas."
        )

    # ======================================================
    # SOLO PRIMER CORREO
    # ======================================================

    if configuracion.solo_primer_correo:
        correos = correos[:1]

        informar(
            "🧪 Modo de prueba: "
            "se procesará únicamente el primer correo."
        )

    # ======================================================
    # CARPETA DE SALIDA
    # ======================================================

    CARPETA_HTML.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_pedidos = 0
    correos_generados = 0

    # ======================================================
    # GENERAR / ABRIR / ENVIAR
    # ======================================================

    for numero, correo in enumerate(
        correos,
        start=1,
    ):
        grupo = correo["grupo"]

        pedidos_grupo = correo.get(
            "total_pedidos",
            0,
        )

        informar("-" * 68)

        informar(
            f"📨 Procesando correo "
            f"{numero}/{len(correos)}: {grupo}"
        )

        informar(
            f"   Asunto: {correo['asunto']}"
        )

        informar(
            f"   Pedidos: {pedidos_grupo:,}"
        )

        informar("🧱 Construyendo HTML...")

        for bloque in correo["bloques"]:
            for actividad in bloque["actividades"]:
                registrar_origen_ans(
                    informar, actividad["tabla"], f"ANTES DEL HTML / {grupo}"
                )

        html = generar_html(
            correo
        )

        archivo_html = guardar_html(
            correo=correo,
            html=html,
            carpeta_salida=CARPETA_HTML,
        )

        informar(
            f"✅ HTML generado: {archivo_html.name}"
        )

        if configuracion.abrir_outlook:

            if configuracion.enviar_automaticamente:

                informar(
                    "📤 Enviando correo automáticamente "
                    "desde Outlook..."
                )

            else:

                informar(
                    "📬 Creando correo para revisión "
                    "en Outlook..."
                )

            abrir_correo_outlook(
                correo,
                html,
                enviar_automaticamente=(
                    configuracion.enviar_automaticamente
                ),
            )

            if configuracion.enviar_automaticamente:

                informar(
                    "✅ Correo enviado automáticamente."
                )

            else:

                informar(
                    "✅ Correo abierto en Outlook para revisión."
                )

        total_pedidos += pedidos_grupo
        correos_generados += 1

    # ======================================================
    # RESULTADO
    # ======================================================

    tiempo_segundos = (
        perf_counter()
        - inicio
    )

    informar("=" * 68)
    informar("✅ PROCESO FINALIZADO")

    informar(
        f"✔ Correos generados : {correos_generados}"
    )

    informar(
        f"✔ Total grupos      : {len(correos)}"
    )

    informar(
        f"✔ Total pedidos     : {total_pedidos:,}"
    )

    informar(
        f"✔ Tiempo ejecución  : "
        f"{formatear_tiempo(tiempo_segundos)}"
    )

    informar(
        f"✔ Ruta de salida    : {CARPETA_HTML}"
    )

    informar("=" * 68)

    return ResultadoEjecucion(
        correos_generados=correos_generados,
        total_grupos=len(correos),
        total_pedidos=total_pedidos,
        tiempo_segundos=tiempo_segundos,
        ruta_salida=CARPETA_HTML,
    )


# ==========================================================
# CONSTRUIR CORREO COMPLETO POR ZONA
# ==========================================================

def construir_correo_zona(
    df: pd.DataFrame,
    zona: str,
) -> dict | None:
    """
    Construye un único correo consolidado para una zona.

    No separa por producto. Todos los pedidos de la zona
    se envían dentro de un único paquete.

    El correo mantiene una estructura compatible con
    generador_html.py para reutilizar el diseño existente.
    """

    zona = normalizar_zona(
        zona
    )

    if "SUBZONA" not in df.columns:
        raise ValueError(
            "El archivo FENIX no contiene la columna SUBZONA."
        )

    df_zona = df[
        df["SUBZONA"]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq(zona)
    ].copy()

    if df_zona.empty:
        return None

    resumen = resumen_estado(
        df_zona
    )

    actividad_general = {
        "nombre": "TODOS LOS PEDIDOS",
        "total": len(df_zona),
        "resumen": resumen,
        "tabla": df_zona,
    }

    bloque_general = {
        "productos": [],
        "total_pedidos": len(df_zona),
        "actividades": [
            actividad_general
        ],
    }

    fecha_corte = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )

    return {
        "grupo": zona,
        "tipo_correo": "ZONA",
        "zona": zona,
        "subzona": zona,
        "asunto": (
            f"🚨 Seguimiento ANS | {zona}"
        ),
        "fecha_corte": fecha_corte,
        "total_pedidos": len(df_zona),
        "bloques": [
            bloque_general
        ],
    }


# ==========================================================
# RESUMEN DE ESTADOS PARA CORREOS POR ZONA
# ==========================================================

def resumen_estado(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Genera el resumen Estado / Total / Porcentaje
    para el correo completo de una zona.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                "ESTADO",
                "TOTAL",
                "PORCENTAJE",
            ]
        )

    if "ESTADO" not in df.columns:
        raise ValueError(
            "El archivo FENIX no contiene la columna ESTADO."
        )

    resumen = (
        df.groupby(
            "ESTADO",
            dropna=False,
        )
        .size()
        .reset_index(
            name="TOTAL"
        )
    )

    total = resumen[
        "TOTAL"
    ].sum()

    resumen[
        "PORCENTAJE"
    ] = (
        resumen["TOTAL"]
        / total
        * 100
    ).round(1)

    return resumen


# ==========================================================
# NORMALIZAR ZONA
# ==========================================================

def normalizar_zona(
    zona: str,
) -> str:
    return (
        str(zona)
        .strip()
        .upper()
    )


def normalizar_zonas(
    zonas,
) -> tuple[str, ...]:

    resultado = []

    for zona in zonas:

        zona_normalizada = normalizar_zona(
            zona
        )

        if (
            zona_normalizada
            and zona_normalizada not in resultado
        ):
            resultado.append(
                zona_normalizada
            )

    return tuple(
        resultado
    )



# ==========================================================
# GUARDAR HTML
# ==========================================================

def guardar_html(
    correo: dict,
    html: str,
    carpeta_salida: Path,
) -> Path:
    """
    Guarda en disco el HTML generado para un grupo o zona.
    """

    nombre_grupo = normalizar_nombre_archivo(
        correo["grupo"]
    )

    archivo_html = (
        carpeta_salida
        / f"{nombre_grupo}.html"
    )

    archivo_html.write_text(
        html,
        encoding="utf-8",
    )

    return archivo_html


# ==========================================================
# NORMALIZAR NOMBRE DE ARCHIVO
# ==========================================================

def normalizar_nombre_archivo(
    nombre: str,
) -> str:
    """
    Convierte un nombre de grupo en un nombre válido de archivo.
    """

    return (
        nombre.strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


# ==========================================================
# FORMATEAR TIEMPO
# ==========================================================

def formatear_tiempo(
    segundos: float,
) -> str:
    """
    Convierte segundos en formato HH:MM:SS.
    """

    total_segundos = int(
        segundos
    )

    horas, restante = divmod(
        total_segundos,
        3600,
    )

    minutos, segundos_restantes = divmod(
        restante,
        60,
    )

    return (
        f"{horas:02d}:"
        f"{minutos:02d}:"
        f"{segundos_restantes:02d}"
    )
