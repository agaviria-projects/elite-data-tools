from collections.abc import Callable
from pathlib import Path

from modules.informe_ans.models import (
    ConfiguracionEjecucion,
    ResultadoEjecucion,
)
from modules.informe_ans.runner import ejecutar_informe_ans


class InformeAnsController:
    """
    Controlador del módulo Generador Informe ANS.

    Conecta la interfaz de DataSuite con el servicio encargado
    de ejecutar el procesamiento de los informes.
    """

    def ejecutar(
        self,
        archivo_fenix: Path,
        modo_prueba: bool,
        solo_primer_correo: bool,
        abrir_outlook: bool,
        enviar_automaticamente: bool,
        informar: Callable[[str], None],
    ) -> ResultadoEjecucion:
        """
        Construye la configuración y ejecuta el proceso ANS.
        """

        configuracion = ConfiguracionEjecucion(
            archivo_fenix=archivo_fenix,
            modo_prueba=modo_prueba,
            solo_primer_correo=solo_primer_correo,
            abrir_outlook=abrir_outlook,
            enviar_automaticamente=enviar_automaticamente,
        )

        resultado = ejecutar_informe_ans(
            configuracion=configuracion,
            informar=informar,
        )

        return resultado