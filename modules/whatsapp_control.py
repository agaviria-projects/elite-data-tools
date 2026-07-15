import ttkbootstrap as ttk

from datetime import datetime
from pathlib import Path
from tkinter import filedialog

from ui.base_view import crear_vista
from ui.widgets.date_picker import DatePicker
from utils.executor import ejecutar_secuencia


# ==========================================================
# RUTAS
# ==========================================================

BASE = Path(__file__).resolve().parent.parent

PROYECTO = BASE / "grupo_whatsapp"

proyecto_actual = PROYECTO


# ==========================================================
# VARIABLES GLOBALES
# ==========================================================

txt_consola = None
fecha_desde = None
fecha_hasta = None


# ==========================================================
# VALIDAR PROYECTO
# ==========================================================

def validar_proyecto():

    entrada = proyecto_actual / "entrada"
    salida = proyecto_actual / "salida"

    return {

        "Carpeta entrada": entrada.exists(),

        "Carpeta salida": salida.exists(),

        "Archivo TXT": any(
            entrada.glob("*.txt")
        ),

        "Conexión Clientes": (
            entrada / "CONEXION CLIENTES.xlsx"
        ).exists(),

        "Informe ANS": any(
            entrada.glob("INFORME ANS-CORTE*.xlsm")
        )
    }


# ==========================================================
# ACTUALIZAR ESTADO
# ==========================================================

def actualizar_estado(frame):

    for widget in frame.winfo_children():
        widget.destroy()

    for nombre, existe in validar_proyecto().items():

        fila = ttk.Frame(frame)

        fila.pack(
            fill="x",
            pady=2
        )

        ttk.Label(
            fila,
            text="🟢" if existe else "🔴",
            width=2
        ).pack(side="left")

        ttk.Label(
            fila,
            text=nombre,
            anchor="w"
        ).pack(
            side="left",
            fill="x",
            expand=True
        )


# ==========================================================
# CAMBIAR CARPETA
# ==========================================================

def cambiar_proyecto(var_ruta, frame_estado):

    global proyecto_actual

    carpeta = filedialog.askdirectory(
        title="Seleccione la carpeta grupo_whatsapp"
    )

    if not carpeta:
        return

    proyecto_actual = Path(carpeta)

    var_ruta.set(
        str(proyecto_actual)
    )

    actualizar_estado(frame_estado)

    if txt_consola:

        txt_consola.insert(
            "end",
            f"📁 Proyecto seleccionado:\n{proyecto_actual}\n\n"
        )

        txt_consola.see("end")


# ==========================================================
# VALIDAR FECHAS
# ==========================================================

def validar_rango_fechas(desde, hasta):

    inicio = datetime.strptime(
        desde,
        "%Y-%m-%d"
    )

    fin = datetime.strptime(
        hasta,
        "%Y-%m-%d"
    )

    if inicio > fin:

        ttk.dialogs.Messagebox.show_error(

            title="Rango de fechas",

            message=(
                "La fecha inicial no puede "
                "ser mayor que la fecha final."
            )
        )

        return False

    return True


# ==========================================================
# VALIDAR PROYECTO COMPLETO
# ==========================================================

def validar_proyecto_completo():

    estado = validar_proyecto()

    if all(estado.values()):
        return True

    ttk.dialogs.Messagebox.show_error(

        title="Proyecto incompleto",

        message=(
            "El proyecto no está completo.\n\n"
            "Revise el panel Estado del Proyecto."
        )
    )

    return False


# ==========================================================
# EJECUTAR
# ==========================================================

def ejecutar_whatsapp():
    print("ENTRÓ A EJECUTAR_WHATSAPP")
    desde = fecha_desde.get()
    hasta = fecha_hasta.get()

    if not validar_rango_fechas(
        desde,
        hasta
    ):
        return

    if not validar_proyecto_completo():
        return

    txt_consola.delete(
        "1.0",
        "end"
    )

    txt_consola.insert(
        "end",
        "🚀 Iniciando WhatsApp + Control ANS...\n\n"
    )

    pasos = [

        (
            "Cruce WhatsApp + Formulario + ANS",
            "procesar_whatsapp.py"
        )

    ]

    def escribir(texto):

        txt_consola.insert(
            "end",
            texto + "\n"
        )

        txt_consola.see("end")
        txt_consola.update_idletasks()

    ejecutar_secuencia(

        proyecto_actual,

        pasos,

        callback=escribir,

        argumentos=[
            desde,
            hasta
        ]
    )

    txt_consola.insert(

        "end",

        "\n🎉 Proceso finalizado correctamente.\n"

    )

    txt_consola.see("end")

# ==========================================================
# INTERFAZ
# ==========================================================

def crear_whatsapp(panel):

    global txt_consola

    vista = crear_vista(panel)

    crear_encabezado(vista)

    crear_panel_superior(vista)

    crear_panel_parametros(vista)

    crear_panel_proceso(vista)

    txt_consola = crear_panel_consola(vista)


# ==========================================================
# ENCABEZADO
# ==========================================================

def crear_encabezado(parent):

    ttk.Label(
        parent,
        text="💬 WhatsApp + Control ANS",
        font=("Segoe UI", 24, "bold"),
        bootstyle="success"
    ).pack(
        anchor="w"
    )

    ttk.Label(
        parent,
        text="Cruce automático entre WhatsApp, Conexión Clientes e Informe ANS."
    ).pack(
        anchor="w",
        pady=(0, 15)
    )


# ==========================================================
# PANEL SUPERIOR
# ==========================================================

def crear_panel_superior(parent):

    contenedor = ttk.Frame(parent)

    contenedor.pack(
        fill="x",
        pady=(0, 12)
    )

    contenedor.columnconfigure(
        0,
        weight=1
    )

    contenedor.columnconfigure(
        1,
        weight=1
    )

    frm_estado = crear_panel_proyecto(
        contenedor
    )

    crear_panel_estado(
        contenedor,
        frm_estado
    )


# ==========================================================
# PANEL PROYECTO
# ==========================================================

def crear_panel_proyecto(parent):

    izquierda = ttk.Labelframe(
        parent,
        text="Proyecto",
        padding=10
    )

    izquierda.grid(
        row=0,
        column=0,
        sticky="nsew",
        padx=(0, 8)
    )

    ruta = ttk.StringVar(
        value=str(proyecto_actual)
    )

    ttk.Entry(
        izquierda,
        textvariable=ruta,
        state="readonly"
    ).pack(
        fill="x"
    )

    frm_estado = ttk.Labelframe(
        parent,
        text="Estado del Proyecto",
        padding=10
    )

    ttk.Button(
        izquierda,
        text="Cambiar carpeta",
        bootstyle="secondary",
        cursor="hand2",
        command=lambda: cambiar_proyecto(
            ruta,
            frm_estado
        )
    ).pack(
        anchor="e",
        pady=(8, 0)
    )

    return frm_estado


# ==========================================================
# PANEL ESTADO
# ==========================================================

def crear_panel_estado(parent, frame_estado):

    frame_estado.grid(
        row=0,
        column=1,
        sticky="nsew",
        padx=(8, 0)
    )

    actualizar_estado(
        frame_estado
    )

# ==========================================================
# PANEL PARÁMETROS
# ==========================================================

def crear_panel_parametros(parent):

    frm = ttk.Labelframe(
        parent,
        text="Parámetros",
        padding=10
    )

    frm.pack(
        fill="x",
        pady=(0, 12)
    )

    crear_parametros_fechas(frm)


# ==========================================================
# FECHAS
# ==========================================================

def crear_parametros_fechas(parent):

    global fecha_desde
    global fecha_hasta

    contenedor = ttk.Frame(parent)

    contenedor.pack(
        fill="x"
    )

    contenedor.columnconfigure(0, weight=1)
    contenedor.columnconfigure(1, weight=1)

    fecha_desde = DatePicker(
        contenedor,
        label="Fecha desde"
    )

    fecha_desde.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=(0, 8)
    )

    fecha_hasta = DatePicker(
        contenedor,
        label="Fecha hasta"
    )

    fecha_hasta.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(8, 0)
    )


# ==========================================================
# PANEL PROCESO
# ==========================================================

def crear_panel_proceso(parent):

    frm = ttk.Labelframe(
        parent,
        text="Proceso",
        padding=10
    )

    frm.pack(
        fill="x",
        pady=(0, 12)
    )

    btn = ttk.Button(
        frm,
        text="🚀 Ejecutar Cruce WhatsApp + ANS",
        bootstyle="success",
        width=35,
        cursor="hand2",
        command=ejecutar_whatsapp
    )

    print("Cursor del botón:", btn.cget("cursor"))

    btn.pack()

# ==========================================================
# PANEL CONSOLA
# ==========================================================

def crear_panel_consola(parent):

    frm = ttk.Labelframe(
        parent,
        text="Consola",
        padding=8
    )

    frm.pack(
        fill="both",
        expand=True
    )

    contenedor = ttk.Frame(frm)

    contenedor.pack(
        fill="both",
        expand=True
    )

    scrollbar = ttk.Scrollbar(
        contenedor,
        orient="vertical"
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    consola = ttk.Text(
        contenedor,
        height=14,
        wrap="word",
        yscrollcommand=scrollbar.set
    )

    consola.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar.config(
        command=consola.yview
    )

    consola.insert(
        "end",
        "============================================================\n"
    )

    consola.insert(
        "end",
        "        WhatsApp + Control ANS\n"
    )

    consola.insert(
        "end",
        "============================================================\n\n"
    )

    consola.insert(
        "end",
        "Esperando ejecución...\n"
    )

    return consola