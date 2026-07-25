from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConfiguracionEjecucion:
    """
    Parámetros utilizados durante la ejecución del informe ANS.
    """

    archivo_fenix: Path
    modo_prueba: bool = True
    solo_primer_correo: bool = False
    abrir_outlook: bool = True
    enviar_automaticamente: bool = False


@dataclass(frozen=True)
class ResultadoEjecucion:
    """
    Resultado final producido por el proceso.
    """

    correos_generados: int
    total_grupos: int
    total_pedidos: int
    tiempo_segundos: float
    ruta_salida: Path