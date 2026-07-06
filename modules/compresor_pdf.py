import ttkbootstrap as ttk

from pathlib import Path
from tkinter import filedialog

from ui.base_view import crear_vista

from utils.executor import ejecutar_secuencia

# ==========================================================
# RUTAS
# ==========================================================

BASE = Path(__file__).resolve().parent.parent

PROYECTO = BASE / "PDF_ZIP"

proyecto_actual = PROYECTO


# ==========================================================
# VALIDAR PROYECTO
# ==========================================================

def validar_proyecto():

    return {

        "Carpeta PDF": (
            proyecto_actual / "PDF"
        ).exists(),

        "Motor de Compresión": (
            proyecto_actual / "zip.py"
        ).exists(),

        "Carpeta Salida": True,

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

        title="Seleccione PDF_ZIP"

    )

    if not carpeta:
        return

    proyecto_actual = Path(carpeta)

    var.set(str(proyecto_actual))

    actualizar_estado(frame)


# ==========================================================
# EJECUTAR
# ==========================================================

def ejecutar_compresion():

    txt_consola.delete("1.0", "end")

    txt_consola.insert(

        "end",

        "🚀 Iniciando Compresor PDF...\n\n"

    )

    pasos = [

        (

            "Compresión de PDFs",

            "zip.py"

        )

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

        "\n🎉 Compresión finalizada correctamente.\n"

    )


# ==========================================================
# INTERFAZ
# ==========================================================

def crear_compresor_pdf(panel):

    vista = crear_vista(panel)

    ttk.Label(

        vista,

        text="📦 Compresor PDF",

        font=("Segoe UI", 24, "bold"),

        bootstyle="success"

    ).pack(anchor="w")

    ttk.Label(

        vista,

        text="Compresión automática de documentos PDF."

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

    # ------------------------------------------------------

    acciones = ttk.Labelframe(

        vista,

        text="Proceso",

        padding=20

    )

    acciones.pack(fill="x", pady=(20, 15))

    ttk.Button(

        acciones,

        text="▶ Comprimir PDFs",

        width=28,

        bootstyle="success",

        command=ejecutar_compresion

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