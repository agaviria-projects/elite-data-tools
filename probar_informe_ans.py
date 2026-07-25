from modules.informe_ans.config.parametros import ARCHIVO_FENIX
from modules.informe_ans.models import ConfiguracionEjecucion
from modules.informe_ans.runner import ejecutar_informe_ans


def mostrar_mensaje(mensaje: str) -> None:
    """
    Muestra en la terminal los mensajes producidos por el runner.
    """

    print(mensaje)


def main() -> None:
    """
    Prueba controlada del módulo Informe ANS.

    En esta prueba:
    - Se procesa únicamente el primer correo.
    - Se genera el archivo HTML.
    - No se abre Outlook.
    - No se envía ningún correo.
    """

    configuracion = ConfiguracionEjecucion(
        archivo_fenix=ARCHIVO_FENIX,
        modo_prueba=True,
        solo_primer_correo=True,
        abrir_outlook=True,
        enviar_automaticamente=False,
    )

    resultado = ejecutar_informe_ans(
        configuracion=configuracion,
        informar=mostrar_mensaje,
    )

    print()
    print("=" * 68)
    print("RESULTADO DEVUELTO POR EL MÓDULO")
    print("=" * 68)
    print(
        f"Correos generados : "
        f"{resultado.correos_generados}"
    )
    print(
        f"Total grupos      : "
        f"{resultado.total_grupos}"
    )
    print(
        f"Total pedidos     : "
        f"{resultado.total_pedidos:,}"
    )
    print(
        f"Tiempo segundos   : "
        f"{resultado.tiempo_segundos:.2f}"
    )
    print(
        f"Ruta de salida    : "
        f"{resultado.ruta_salida}"
    )


if __name__ == "__main__":
    main()