"""
=========================================================
Executor
Motor genérico para ejecutar scripts Python
ELITE Data Tools
=========================================================
"""

import subprocess
import sys
from pathlib import Path

print("=" * 60)
print("EXECUTOR V2 CARGADO")
print("=" * 60)


# =========================================================
# EJECUTAR SCRIPT PYTHON
# =========================================================

def ejecutar_python(
    script,
    carpeta=None,
    callback=None,
    argumentos=None
):
    """
    Ejecuta un script Python.

    Parameters
    ----------
    script : str | Path
        Ruta del script.

    carpeta : Path | str
        Directorio de trabajo.

    callback : function
        Función que recibe cada línea del proceso.
    """

    script = Path(script)

    if carpeta is None:
        carpeta = script.parent

    comando = [
        sys.executable,
        "-u",
        "-X",
        "utf8",
        str(script)
    ]

    if argumentos:
        comando.extend(argumentos)

    proceso = subprocess.Popen(
        comando,

        cwd=carpeta,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8"
    )

    salida = []

    for linea in iter(proceso.stdout.readline, ""):

        linea = linea.rstrip()

        salida.append(linea)

        if callback:
            callback(linea)

    proceso.wait()

    return proceso.returncode, salida
# =========================================================
# EJECUTAR SECUENCIA DE SCRIPTS
# =========================================================

from pathlib import Path

def ejecutar_secuencia(
    carpeta,
    pasos,
    callback=None,
    argumentos=None
):
    """
    Ejecuta varios scripts en orden.

    carpeta : Path
        Carpeta donde están los scripts.

    pasos : list[tuple]
        [
            ("Título", "script.py"),
            ...
        ]
    """

    carpeta = Path(carpeta)

    for titulo, script in pasos:

        if callback:
            callback(f"\n▶ {titulo}")

        ruta = carpeta / script

        codigo, salida = ejecutar_python(

            ruta,

            carpeta,

            callback,

            argumentos

        )

        if codigo != 0:

            if callback:
                callback(
                    f"\n❌ Error ejecutando {script}"
                )

            return False

        if callback:
            callback(
                f"✅ Finalizó {titulo}"
            )

    return True