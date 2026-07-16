
"""
=========================================================
MÓDULO
Informe Actas DRACO
=========================================================
Entrega 1 - Interfaz base
"""


import re
import sys
import os
import subprocess
import threading
import ttkbootstrap as ttk

from pathlib import Path
from tkinter import filedialog

from ui.base_view import crear_vista
from tkinter import filedialog, messagebox

# ==========================================================
# RUTAS
# ==========================================================

BASE = Path(__file__).resolve().parent.parent
PROYECTO = BASE / "actas_draco"
proyecto_actual = PROYECTO

lbl_proyecto = None
lbl_estado = None
txt_consola = None
cmb_acta = None
btn_ejecutar = None

# ==========================================================
# VALIDAR PROYECTO
# ==========================================================

def validar_proyecto():

    return {
        "data/draco": (proyecto_actual / "data" / "draco").exists(),
        "data/salida": (proyecto_actual / "data" / "salida").exists(),
        "data/logs": (proyecto_actual / "data" / "logs").exists(),
        "scripts": (proyecto_actual / "scripts").exists(),
        "main.py": (proyecto_actual / "main.py").exists(),
    }


def actualizar_estado():

    estados = validar_proyecto()

    texto = ""

    for nombre, ok in estados.items():
        icono = "🟢" if ok else "🔴"
        texto += f"{icono} {nombre}\n"

    if lbl_estado is not None:
        lbl_estado.config(text=texto)


# ==========================================================
# DETECTAR ACTAS DISPONIBLES
# ==========================================================

def obtener_actas_disponibles():
    """
    Detecta automáticamente archivos con nombres como:

    ACTA 8.xlsx
    ACTA 9.xlsx
    ACTA 10.xlsx
    ACTA 11.xlsx
    ACTA 12.xlsx

    ubicados dentro de data/draco.
    """

    carpeta_draco = proyecto_actual / "data" / "draco"

    if not carpeta_draco.exists():
        return []

    numeros_actas = []

    for archivo in carpeta_draco.iterdir():

        if not archivo.is_file():
            continue

        # Solo archivos de Excel
        if archivo.suffix.lower() not in {".xlsx", ".xlsm", ".xls"}:
            continue

        nombre = archivo.stem.strip()

        coincidencia = re.fullmatch(
            r"ACTA\s*(\d+)",
            nombre,
            flags=re.IGNORECASE
        )

        if coincidencia:
            numero = int(coincidencia.group(1))
            numeros_actas.append(numero)

    # Eliminar duplicados y ordenar numéricamente
    numeros_actas = sorted(set(numeros_actas))

    return [
        f"ACTA {numero}"
        for numero in numeros_actas
    ]


def actualizar_actas_disponibles():
    """
    Actualiza el Combobox permitiendo:

    - Solo generar DRACO_UNIFICADO.xlsx
    - Generar también un acta específica
    """

    if cmb_acta is None:
        return

    actas = obtener_actas_disponibles()

    opciones = [
        "SOLO UNIFICAR"
    ] + actas

    cmb_acta.configure(
        values=opciones
    )

    # Opción predeterminada más segura
    cmb_acta.set(
        "SOLO UNIFICAR"
    )


# ==========================================================
# CAMBIAR PROYECTO
# ==========================================================

def cambiar_proyecto():

    global proyecto_actual

    carpeta = filedialog.askdirectory(
        title="Seleccione la carpeta actas_draco"
    )

    if not carpeta:
        return

    proyecto_actual = Path(carpeta)

    if lbl_proyecto is not None:
        lbl_proyecto.config(
            text=str(proyecto_actual)
        )

    actualizar_estado()
    actualizar_actas_disponibles()


# ==========================================================
# CONSOLA
# ==========================================================

def escribir_consola(texto):

    if txt_consola is None:
        return

    txt_consola.insert(
        "end",
        texto + "\n"
    )

    txt_consola.see("end")


# ==========================================================
# FINALIZAR EJECUCIÓN
# ==========================================================

def finalizar_ejecucion(exito):

    if btn_ejecutar is not None:
        btn_ejecutar.config(state="normal")

    if exito:
        escribir_consola("")
        escribir_consola("==================================================")
        escribir_consola("✅ PROCESO DRACO FINALIZADO CORRECTAMENTE")
        escribir_consola("==================================================")

        messagebox.showinfo(
            "Informe Actas DRACO",
            "El proceso DRACO finalizó correctamente.\n\n"
            "Revise los archivos generados en data/salida."
        )

    else:
        escribir_consola("")
        escribir_consola("==================================================")
        escribir_consola("❌ EL PROCESO DRACO FINALIZÓ CON ERRORES")
        escribir_consola("==================================================")

        messagebox.showerror(
            "Informe Actas DRACO",
            "El proceso DRACO presentó un error.\n\n"
            "Revise la consola para conocer el detalle."
        )


# ==========================================================
# PROCESO EN SEGUNDO PLANO
# ==========================================================

def ejecutar_proceso_draco(numero_acta=None):

    archivo_main = proyecto_actual / "main.py"

    comando = [
        sys.executable,
        "-u",
        str(archivo_main),
    ]

    if numero_acta is None:
        comando.append("--solo-unificar")
    else:
        comando.extend([
            "--acta",
            str(numero_acta),
        ])

    entorno = dict(os.environ)
    entorno["PYTHONIOENCODING"] = "utf-8"
    entorno["PYTHONUTF8"] = "1"

    try:

        escribir_consola("Comando de ejecución:")
        escribir_consola(" ".join(comando))
        escribir_consola("")

        proceso = subprocess.Popen(
            comando,
            cwd=str(proyecto_actual),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=entorno,
        )

        if proceso.stdout is not None:

            for linea in proceso.stdout:

                linea = linea.rstrip()

                txt_consola.after(
                    0,
                    escribir_consola,
                    linea
                )

        codigo_salida = proceso.wait()

        if codigo_salida == 0:

            txt_consola.after(
                0,
                finalizar_ejecucion,
                True
            )

        else:

            txt_consola.after(
                0,
                escribir_consola,
                f"❌ Código de salida del proceso: {codigo_salida}"
            )

            txt_consola.after(
                0,
                finalizar_ejecucion,
                False
            )

    except Exception as error:

        txt_consola.after(
            0,
            escribir_consola,
            f"❌ Error al ejecutar DRACO: {error}"
        )

        txt_consola.after(
            0,
            finalizar_ejecucion,
            False
        )


# ==========================================================
# EJECUTAR
# ==========================================================

def ejecutar():

    opcion_seleccionada = cmb_acta.get().strip()

    txt_consola.delete(
        "1.0",
        "end"
    )

    escribir_consola(
        "=================================================="
    )
    escribir_consola(
        "🚀 INFORME ACTAS DRACO"
    )
    escribir_consola(
        "=================================================="
    )
    escribir_consola("")

    # ------------------------------------------------------
    # VALIDAR OPCIÓN
    # ------------------------------------------------------

    if not opcion_seleccionada:

        escribir_consola(
            "❌ Seleccione una opción de procesamiento."
        )

        messagebox.showwarning(
            "Informe Actas DRACO",
            "Seleccione una opción de procesamiento."
        )

        return

    # ------------------------------------------------------
    # VALIDAR PROYECTO
    # ------------------------------------------------------

    archivo_main = proyecto_actual / "main.py"
    carpeta_entrada = proyecto_actual / "data" / "draco"
    carpeta_salida = proyecto_actual / "data" / "salida"

    if not archivo_main.exists():

        escribir_consola(
            f"❌ No se encontró main.py en:\n{archivo_main}"
        )

        messagebox.showerror(
            "Informe Actas DRACO",
            "No se encontró el archivo main.py."
        )

        return

    if not carpeta_entrada.exists():

        escribir_consola(
            f"❌ No se encontró la carpeta:\n{carpeta_entrada}"
        )

        messagebox.showerror(
            "Informe Actas DRACO",
            "No se encontró la carpeta data/draco."
        )

        return

    archivos_excel = [
        archivo
        for archivo in carpeta_entrada.iterdir()
        if (
            archivo.is_file()
            and archivo.suffix.lower() in {
                ".xlsx",
                ".xlsm",
                ".xls"
            }
        )
    ]

    if not archivos_excel:

        escribir_consola(
            "❌ La carpeta data/draco no contiene archivos de Excel."
        )

        messagebox.showwarning(
            "Informe Actas DRACO",
            "La carpeta data/draco no contiene archivos para procesar."
        )

        return

    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True
    )

    # ------------------------------------------------------
    # DETERMINAR TIPO DE PROCESO
    # ------------------------------------------------------

    numero_acta = None

    if opcion_seleccionada != "SOLO UNIFICAR":

        coincidencia = re.search(
            r"(\d+)",
            opcion_seleccionada
        )

        if not coincidencia:

            escribir_consola(
                "❌ No fue posible identificar el número del acta."
            )

            return

        numero_acta = int(
            coincidencia.group(1)
        )

    # ------------------------------------------------------
    # INFORMACIÓN
    # ------------------------------------------------------

    escribir_consola(
        f"📁 Proyecto: {proyecto_actual}"
    )
    escribir_consola(
        f"📂 Carpeta de entrada: {carpeta_entrada}"
    )
    escribir_consola(
        f"📂 Carpeta de salida: {carpeta_salida}"
    )
    escribir_consola(
        f"📄 Archivos detectados: {len(archivos_excel)}"
    )

    if numero_acta is None:

        escribir_consola(
            "📌 Proceso seleccionado: SOLO UNIFICAR"
        )
        escribir_consola(
            "📄 Archivo esperado: DRACO_UNIFICADO.xlsx"
        )

    else:

        escribir_consola(
            f"📌 Proceso seleccionado: GENERAR ACTA {numero_acta}"
        )
        escribir_consola(
            "📂 Archivo base: DRACO_UNIFICADO.xlsx"
        )
        escribir_consola(
            f"📄 Archivo esperado: DRACO_ACTA_{numero_acta}.xlsx"
        )

    escribir_consola("")

    escribir_consola(
        "⚠ Regla de negocio:"
    )
    escribir_consola(
        "Los códigos de Mano de Obra que comienzan por "
        "A, B o C no se incluyen en el informe."
    )
    escribir_consola("")

    escribir_consola(
        "⏳ Iniciando proceso DRACO..."
    )
    escribir_consola("")

    # Evitar dobles ejecuciones
    if btn_ejecutar is not None:

        btn_ejecutar.config(
            state="disabled"
        )

    hilo = threading.Thread(
        target=ejecutar_proceso_draco,
        args=(numero_acta,),
        daemon=True
    )

    hilo.start()
# ==========================================================
# INTERFAZ
# ==========================================================

def crear_draco(panel):

    global lbl_proyecto
    global lbl_estado
    global txt_consola
    global cmb_acta
    global btn_ejecutar

    vista = crear_vista(panel)

    # ======================================================
    # TÍTULO
    # ======================================================

    ttk.Label(
        vista,
        text="📄 Informe Actas DRACO",
        font=("Segoe UI", 24, "bold"),
        bootstyle="success"
    ).pack(
        anchor="w"
    )

    ttk.Label(
        vista,
        text="Unificación y generación de archivos DRACO.",
        font=("Segoe UI", 10)
    ).pack(
        anchor="w",
        pady=(0, 15)
    )

    # ======================================================
    # INFORMACIÓN SUPERIOR
    # ======================================================

    superior = ttk.Frame(vista)

    superior.pack(
        fill="x",
        pady=(5, 10)
    )

    superior.columnconfigure(
        0,
        weight=1
    )

    superior.columnconfigure(
        1,
        weight=1
    )

    # ------------------------------------------------------
    # PROYECTO
    # ------------------------------------------------------

    frame_proyecto = ttk.Labelframe(
        superior,
        text="Proyecto",
        padding=10
    )

    frame_proyecto.grid(
        row=0,
        column=0,
        sticky="nsew",
        padx=(0, 10)
    )

    lbl_proyecto = ttk.Label(
        frame_proyecto,
        text=str(proyecto_actual)
    )

    lbl_proyecto.pack(
        anchor="w",
        fill="x"
    )

    ttk.Button(
        frame_proyecto,
        text="Cambiar carpeta",
        bootstyle="secondary",
        cursor="hand2",
        command=cambiar_proyecto
    ).pack(
        anchor="e",
        pady=(10, 0)
    )

    # ------------------------------------------------------
    # ESTADO DEL PROYECTO
    # ------------------------------------------------------

    frame_estado = ttk.Labelframe(
        superior,
        text="Estado del Proyecto",
        padding=10
    )

    frame_estado.grid(
        row=0,
        column=1,
        sticky="nsew"
    )

    lbl_estado = ttk.Label(
        frame_estado,
        justify="left"
    )

    lbl_estado.pack(
        anchor="w"
    )

    actualizar_estado()

    # ======================================================
    # PROCESO
    # ======================================================

    frame_acciones = ttk.Labelframe(
        vista,
        text="Proceso",
        padding=12
    )

    frame_acciones.pack(
        fill="x",
        pady=(0, 10)
    )

    contenido_proceso = ttk.Frame(
        frame_acciones
    )

    contenido_proceso.pack(
        fill="x"
    )

    contenido_proceso.columnconfigure(
        0,
        weight=0
    )

    contenido_proceso.columnconfigure(
        1,
        weight=1
    )

    # ------------------------------------------------------
    # SELECTOR DE ACTA
    # ------------------------------------------------------

    frame_selector = ttk.Frame(
        contenido_proceso
    )

    frame_selector.grid(
        row=0,
        column=0,
        sticky="nw",
        padx=(0, 30)
    )

    ttk.Label(
        frame_selector,
        text="Acta"
    ).pack(
        anchor="w"
    )

    cmb_acta = ttk.Combobox(
        frame_selector,
        state="readonly",
        width=20
    )

    cmb_acta.pack(
        anchor="w",
        pady=(5, 0)
    )

    # Detectar las actas existentes en data/draco
    actualizar_actas_disponibles()

    # ------------------------------------------------------
    # MENSAJE DE REGLA DE NEGOCIO
    # ------------------------------------------------------

    frame_regla = ttk.Labelframe(
        contenido_proceso,
        text="⚠ Regla de negocio",
        padding=10,
        bootstyle="warning"
    )

    frame_regla.grid(
        row=0,
        column=1,
        sticky="ew"
    )

    ttk.Label(
        frame_regla,
        text=(
            "Los códigos correspondientes a Mano de Obra cuyos "
            "valores comiencen por A, B o C se excluyen "
            "automáticamente y no se incluyen en el informe generado."
        ),
        justify="left",
        wraplength=650,
        bootstyle="warning"
    ).pack(
        anchor="w"
    )

    # ------------------------------------------------------
    # BOTÓN EJECUTAR
    # ------------------------------------------------------

    btn_ejecutar = ttk.Button(
        contenido_proceso,
        text="▶ Ejecutar Proceso DRACO",
        bootstyle="success",
        cursor="hand2",
        width=30,
        command=ejecutar
    )

    btn_ejecutar.grid(
        row=1,
        column=0,
        columnspan=2,
        pady=(12, 0)
    )

       # ======================================================
    # CONSOLA
    # ======================================================

    frame_consola = ttk.Labelframe(
        vista,
        text="Consola de ejecución",
        padding=8
    )

    frame_consola.pack(
        fill="both",
        expand=True,
        pady=(0, 5)
    )

    # Contenedor para texto y barras de desplazamiento
    contenido_consola = ttk.Frame(
        frame_consola
    )

    contenido_consola.pack(
        fill="both",
        expand=True
    )

    contenido_consola.rowconfigure(
        0,
        weight=1
    )

    contenido_consola.columnconfigure(
        0,
        weight=1
    )

    # Barra vertical
    scroll_vertical = ttk.Scrollbar(
        contenido_consola,
        orient="vertical"
    )

    scroll_vertical.grid(
        row=0,
        column=1,
        sticky="ns"
    )

    # Barra horizontal
    scroll_horizontal = ttk.Scrollbar(
        contenido_consola,
        orient="horizontal"
    )

    scroll_horizontal.grid(
        row=1,
        column=0,
        sticky="ew"
    )

    txt_consola = ttk.Text(
        contenido_consola,
        height=22,
        wrap="none",
        font=(
            "Consolas",
            10
        ),
        padx=10,
        pady=10,
        yscrollcommand=scroll_vertical.set,
        xscrollcommand=scroll_horizontal.set
    )

    txt_consola.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    scroll_vertical.configure(
        command=txt_consola.yview
    )

    scroll_horizontal.configure(
        command=txt_consola.xview
    )

    txt_consola.insert(
        "end",
        "Esperando ejecución...\n"
    )

    return vista