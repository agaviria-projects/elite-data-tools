import subprocess
import sys
from pathlib import Path
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk

from ui.base_view import crear_vista

from utils.executor import ejecutar_secuencia

# ==========================================================
# RUTAS
# ==========================================================

BASE = Path(__file__).resolve().parent.parent

PROYECTO = BASE / "Control_ANS_v5"

proyecto_actual = PROYECTO


# ==========================================================
# VALIDAR PROYECTO
# ==========================================================

def validar_proyecto():

    return {

        "Datos de Entrada": (
            proyecto_actual / "data_raw"
        ).exists(),

        "Datos Procesados": (
            proyecto_actual / "data_clean"
        ).exists(),

        "Motor ANS Operativo": (
            proyecto_actual / "calculos_ans.py"
        ).exists(),

        "Motor ANS Contractual": (
            proyecto_actual / "calculos_ans_epm.py"
        ).exists(),

        "Limpieza de Información": (
            proyecto_actual / "limpieza_fenix.py"
        ).exists(),

    }

# ==========================================================
# ACTUALIZAR ESTADO
# ==========================================================

def actualizar_estado(frame):

    for w in frame.winfo_children():
        w.destroy()

    for nombre, existe in validar_proyecto().items():

        ttk.Label(

            frame,

            text=f'{"🟢" if existe else "🔴"} {nombre}'

        ).pack(anchor="w", pady=2)


# ==========================================================
# CAMBIAR PROYECTO
# ==========================================================

def cambiar_proyecto(var, frame):

    global proyecto_actual

    carpeta = filedialog.askdirectory(

        title="Seleccione Control_ANS_v5"

    )

    if not carpeta:
        return

    proyecto_actual = Path(carpeta)

    var.set(str(proyecto_actual))

    actualizar_estado(frame)


# ==========================================================
# EJECUTAR INFORME
# ==========================================================

def ejecutar_informe(tipo):

    txt_consola.delete("1.0", "end")

    txt_consola.insert(
        "end",
        "🚀 Iniciando Generador Informe ANS...\n"
    )

    txt_consola.insert(
        "end",
        f"📌 Tipo de cálculo: {'Operativo' if tipo == 'OPERATIVO' else 'Contractual EPM'}\n\n"
    )
    if tipo == "OPERATIVO":

        pasos = [

            (
                "Limpieza de Información",
                "limpieza_fenix.py"
            ),

            (
                "Motor de Cálculo ANS",
                "calculos_ans.py"
            ),
        ]

    else:

        pasos = [

            (
                "Limpieza de Información",
                "limpieza_fenix.py"
            ),

            (
                "Motor de Cálculo ANS EPM",
                "calculos_ans_epm.py"
            ),

        ]

    def escribir(linea):

        txt_consola.insert(
            "end",
            linea + "\n"
        )

        txt_consola.see("end")

        txt_consola.update_idletasks()

    ok = ejecutar_secuencia(

        proyecto_actual,

        pasos,

        callback=escribir

    )

    if ok:

        txt_consola.insert(

            "end",

            "\n🎉 Informe ANS finalizado correctamente.\n"

        )

    else:

        txt_consola.insert(

            "end",

            "\n❌ El proceso terminó con errores.\n"

        )

# ==========================================================
# INTERFAZ
# ==========================================================

def crear_generador_ans(panel):

    vista = crear_vista(panel)

    ttk.Label(

        vista,

        text="📈 Generador Informe ANS",

        font=("Segoe UI", 24, "bold"),

        bootstyle="success"

    ).pack(anchor="w")

    ttk.Label(

        vista,

        text="Automatización completa del proceso ANS."

    ).pack(anchor="w", pady=(0, 15))

    # ------------------------------------------------------

    cuerpo = ttk.Frame(vista)

    cuerpo.pack(fill="both", expand=True)

    cuerpo.columnconfigure((0, 1), weight=1)

    izquierda = ttk.Frame(cuerpo)

    izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

    derecha = ttk.Frame(cuerpo)

    derecha.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    # ------------------------------------------------------

    ruta = ttk.StringVar(value=str(proyecto_actual))

    tipo_calculo = ttk.StringVar(value="ANS Operativo")

    frm_proyecto = ttk.Labelframe(

        izquierda,

        text="Proyecto",

        padding=10

    )

    frm_proyecto.pack(fill="x")

    ttk.Entry(

        frm_proyecto,

        textvariable=ruta,

        state="readonly"

    ).pack(fill="x", pady=(0, 8))

    ttk.Button(

        frm_proyecto,

        text="Cambiar carpeta",

        bootstyle="secondary",

        command=lambda: cambiar_proyecto(

            ruta,

            frm_proyecto_estado

        )

    ).pack(anchor="e")

    # ------------------------------------------------------

    frm_proyecto_estado = ttk.Labelframe(

        derecha,

        text="Estado del Proyecto",

        padding=10

    )

    frm_proyecto_estado.pack(

        fill="both",

        expand=True

    )

    actualizar_estado(frm_proyecto_estado)

    
    acciones = ttk.Labelframe(
        vista,
        text="Proceso",
        padding=12
    )

    acciones.pack(fill="x", pady=(20, 15))

    # ============================================
    # PROCESO
    # ============================================

    fila = ttk.Frame(acciones)
    fila.pack(fill="x")

    ttk.Label(
        fila,
        text="Tipo de cálculo ANS:"
    ).pack(side="left", padx=(0,10))

    cmb_tipo = ttk.Combobox(
        fila,
        textvariable=tipo_calculo,
        values=[
            "ANS Operativo",
            "ANS Contractual EPM"
        ],
        state="readonly",
        width=22
    )

    cmb_tipo.pack(side="left")

    ttk.Button(
        fila,
        text="▶ Generar Informe ANS",
        width=25,
        bootstyle="success",
        cursor="hand2",
        command=lambda: ejecutar_informe(
            "OPERATIVO"
            if tipo_calculo.get() == "ANS Operativo"
            else "EPM"
        )
    ).pack(side="right")
    # ------------------------------------------------------

    consola = ttk.Labelframe(

        vista,

        text="Consola",

        padding=8

    )

    consola.pack(

        fill="both",

        expand=True

    )
    global txt_consola

    txt_consola = ttk.Text(

        consola,

        height=10

    )

    txt_consola.pack(

        fill="both",

        expand=True

    )

    txt_consola.insert(

        "end",

        "Esperando ejecución...\n"

    )