from collections.abc import Callable
from pathlib import Path
from time import perf_counter

from modules.informe_ans.config.parametros import CARPETA_HTML
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


def ejecutar_informe_ans(
    configuracion: ConfiguracionEjecucion,
    informar: CallbackMensaje,
) -> ResultadoEjecucion:
    """
    Ejecuta el proceso completo de Seguimiento ANS.

    No contiene reglas de negocio. Únicamente coordina los servicios
    existentes y reporta el avance a la interfaz.
    """

    inicio = perf_counter()

    informar("=" * 68)
    informar("SEGUIMIENTO INTELIGENTE ANS")
    informar("=" * 68)

    informar("📄 Validando archivo FENIX...")

    validar_archivo_fenix()

    informar("✅ Archivo válido.")

    informar("📖 Leyendo información...")

    df = leer_excel()

    informar(
        f"✅ Registros cargados: {len(df):,}"
    )

    informar("📊 Calculando y agrupando información...")

    informes = construir_informes(df)

    informar("📧 Construyendo modelo de correos...")

    correos = construir_correos(informes)

    if configuracion.solo_primer_correo:
        correos = correos[:1]

        informar(
            "🧪 Modo de prueba: "
            "se procesará únicamente el primer correo."
        )

    CARPETA_HTML.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_pedidos = 0
    correos_generados = 0

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

        html = generar_html(correo)

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
                    "📤 Enviando correo automáticamente desde Outlook..."
                )

            else:

                informar(
                    "📬 Creando correo para revisión en Outlook..."
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

    tiempo_segundos = perf_counter() - inicio

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


def guardar_html(
    correo: dict,
    html: str,
    carpeta_salida: Path,
) -> Path:
    """
    Guarda en disco el HTML generado para un grupo.
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


def formatear_tiempo(
    segundos: float,
) -> str:
    """
    Convierte segundos en formato HH:MM:SS.
    """

    total_segundos = int(segundos)

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