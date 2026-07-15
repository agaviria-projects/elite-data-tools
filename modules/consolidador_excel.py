import ttkbootstrap as ttk

from pathlib import Path
from tkinter import filedialog

from ui.base_view import crear_vista

from utils.executor import ejecutar_python

# ==========================================================
# RUTAS
# ==========================================================

BASE = Path(__file__).resolve().parent.parent

PROYECTO = BASE / "SERVITRAVEL"

proyecto_actual = PROYECTO


# ==========================================================
# VARIABLES GLOBALES
# ==========================================================

lbl_proyecto = None
lbl_estado = None
txt_consola = None


# ==========================================================
# VALIDAR PROYECTO
# ==========================================================

def validar_proyecto():

    return {

        "entrada": (
            proyecto_actual / "entrada"
        ).exists(),

        "salida": (
            proyecto_actual / "salida"
        ).exists(),

        "procesados": (
            proyecto_actual / "procesados"
        ).exists(),

        "backup": (
            proyecto_actual / "backup"
        ).exists(),

        "logs": (
            proyecto_actual / "logs"
        ).exists(),

        "src": (
            proyecto_actual / "src"
        ).exists()

    }


# ==========================================================
# ACTUALIZAR ESTADO
# ==========================================================

def actualizar_estado():

    global lbl_estado

    estados = validar_proyecto()

    texto = ""

    for nombre, ok in estados.items():

        icono = "🟢" if ok else "🔴"

        texto += f"{icono} {nombre}\n"

    lbl_estado.config(text=texto)


# ==========================================================
# CAMBIAR PROYECTO
# ==========================================================

def cambiar_proyecto():

    global proyecto_actual

    carpeta = filedialog.askdirectory(
        title="Seleccione la carpeta del proyecto"
    )

    if not carpeta:
        return

    proyecto_actual = Path(carpeta)

    lbl_proyecto.config(
        text=str(proyecto_actual)
    )

    actualizar_estado()

# ==========================================================
# ESCRIBIR EN CONSOLA
# ==========================================================

def escribir_consola(texto):

    txt_consola.insert("end", texto + "\n")

    txt_consola.see("end")

    txt_consola.update_idletasks()
# ==========================================================
# EJECUTAR
# ==========================================================

def ejecutar():

    txt_consola.delete("1.0", "end")

    script = proyecto_actual / "src" / "main.py"

    if not script.exists():

        escribir_consola("❌ No existe el archivo main.py")

        return

    escribir_consola("🚀 Iniciando Consolidador Excel...\n")

    codigo, _ = ejecutar_python(

        script=script,

        carpeta=script.parent,

        callback=escribir_consola

    )

    if codigo == 0:

        escribir_consola("\n✅ Proceso finalizado correctamente.")

    else:

        escribir_consola(f"\n❌ El proceso terminó con código {codigo}.")
        
# ==========================================================
# INTERFAZ
# ==========================================================

def crear_consolidador_excel(panel):

    global lbl_proyecto
    global lbl_estado
    global txt_consola

    vista = crear_vista(panel)

    # ======================================================
    # TITULO
    # ======================================================

    ttk.Label(
        vista,
        text="📚 Consolidador Excel",
        font=("Segoe UI", 24, "bold"),
        bootstyle="success"
    ).pack(anchor="w")

    # ======================================================
    # PANEL SUPERIOR
    # ======================================================

    superior = ttk.Frame(vista)

    superior.pack(
        fill="x",
        pady=(20, 20)
    )

    superior.columnconfigure(0, weight=1)
    superior.columnconfigure(1, weight=1)

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
    # ESTADO
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

    lbl_estado.pack(anchor="w")

    actualizar_estado()

    # ======================================================
    # EJECUCION
    # ======================================================

    frame_acciones = ttk.Labelframe(
        vista,
        text="Ejecución",
        padding=20
    )

    frame_acciones.pack(
        fill="x",
        pady=(0, 20)
    )

    ttk.Button(
        frame_acciones,
        text="▶ Ejecutar Consolidación",
        bootstyle="success",
        width=28,
        cursor="hand2",
        command=ejecutar
    ).pack(
        pady=10
    )

    # ======================================================
    # CONSOLA
    # ======================================================

    frame_consola = ttk.Labelframe(
        vista,
        text="Consola",
        padding=10
    )

    frame_consola.pack(
        fill="both",
        expand=True
    )

    txt_consola = ttk.Text(
        frame_consola,
        height=12
    )

    txt_consola.pack(
        fill="both",
        expand=True
    )

    txt_consola.insert(
        "end",
        "Esperando ejecución..."
    )

    return vista