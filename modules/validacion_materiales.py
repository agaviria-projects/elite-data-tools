import ttkbootstrap as ttk

from pathlib import Path
from tkinter import filedialog

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

        "FENIX ANS": (
            proyecto_actual / "data_clean" / "FENIX_ANS.xlsx"
        ).exists(),

        "Almacén Export": (
            proyecto_actual / "data_raw" / "ALMACEN_EXPORT.xlsx"
        ).exists(),

        "Relación MO - Material": (
            proyecto_actual / "data_raw" / "RELACION_MO_MAT.xlsx"
        ).exists(),

        "Motor de Validación": (
            proyecto_actual / "validar_export_almacen.py"
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
# EJECUTAR VALIDACIÓN
# ==========================================================

def ejecutar_validacion():

    txt_consola.delete("1.0", "end")

    txt_consola.insert(
        "end",
        "🚀 Iniciando Validación Mano de Obra Vs Materiales...\n\n"
    )

    pasos = [

        (
            "Validación Mano de Obra Vs Materiales",
            "validar_export_almacen.py"
        ),

    ]

    def escribir(linea):

        txt_consola.insert(
            "end",
            linea + "\n"
        )

        txt_consola.see("end")

        txt_consola.update_idletasks()

    ejecutar_secuencia(

        proyecto_actual,

        pasos,

        callback=escribir

    )

    txt_consola.insert(

        "end",

        "\n🎉 Validación finalizada correctamente.\n"

    )


# ==========================================================
# INTERFAZ
# ==========================================================

def crear_validacion_materiales(panel):

    vista = crear_vista(panel)

    ttk.Label(

        vista,

        text="📦 Validación Mano de Obra Vs Materiales",

        font=("Segoe UI", 24, "bold"),

        bootstyle="success"

    ).pack(anchor="w")

    ttk.Label(

        vista,

        text="Valida automáticamente los materiales obligatorios por mano de obra."

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

            frm_estado

        )

    ).pack(anchor="e")

    # ------------------------------------------------------

    frm_estado = ttk.Labelframe(

        derecha,

        text="Estado del Proyecto",

        padding=10

    )

    frm_estado.pack(

        fill="both",

        expand=True

    )

    actualizar_estado(frm_estado)

    # ------------------------------------------------------

    acciones = ttk.Labelframe(

        vista,

        text="Proceso",

        padding=20

    )

    acciones.pack(fill="x", pady=(20, 15))

    ttk.Button(

        acciones,

        text="▶ Validar Materiales",

        width=28,

        bootstyle="success",

        command=ejecutar_validacion

    ).pack(pady=10)

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