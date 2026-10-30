import ttkbootstrap as ttk

import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

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

        text="🛠️ Validación Mano de Obra Vs Materiales",

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

        cursor="hand2",

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

    boton_validar = ttk.Button(

        acciones,

        text="▶ Validar Materiales",

        width=28,

        bootstyle="success",

        cursor="hand2",

        command=ejecutar_validacion

    )

    boton_validar.pack(pady=(4, 12))

    # ------------------------------------------------------
    # GENERACIÓN DE CORREOS
    # ------------------------------------------------------

    frm_correo = ttk.Frame(acciones)
    frm_correo.pack(fill="x")

    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    fecha_inicial = ttk.StringVar(value=fecha_hoy)
    fecha_final = ttk.StringVar(value=fecha_hoy)
    modo_correo = ttk.StringVar(value="Modo revisión")

    ttk.Label(frm_correo, text="Fecha inicial:").grid(
        row=0, column=0, padx=(0, 6), pady=4, sticky="w"
    )
    ttk.Entry(frm_correo, textvariable=fecha_inicial, width=14).grid(
        row=0, column=1, padx=(0, 18), pady=4
    )
    ttk.Label(frm_correo, text="Fecha final:").grid(
        row=0, column=2, padx=(0, 6), pady=4, sticky="w"
    )
    ttk.Entry(frm_correo, textvariable=fecha_final, width=14).grid(
        row=0, column=3, padx=(0, 18), pady=4
    )
    ttk.Label(frm_correo, text="Modo:").grid(
        row=0, column=4, padx=(0, 6), pady=4, sticky="w"
    )
    ttk.Combobox(
        frm_correo,
        textvariable=modo_correo,
        values=["Modo revisión", "Envío automático"],
        state="readonly",
        width=19,
    ).grid(row=0, column=5, padx=(0, 18), pady=4)
    ttk.Label(frm_correo, text="Adjuntos:").grid(
        row=0, column=6, padx=(0, 6), pady=4, sticky="w"
    )
    ttk.Label(
        frm_correo,
        text="Todos",
        width=10,
        anchor="center",
        bootstyle="inverse-secondary",
    ).grid(row=0, column=7, padx=(0, 18), pady=4)

    boton_correo = ttk.Button(
        frm_correo,
        text="✉ Generar correos",
        width=23,
        bootstyle="info",
        cursor="hand2",
    )
    boton_correo.grid(row=0, column=8, pady=4)

    ttk.Label(
        acciones,
        text=(
            "Modo revisión abre el mensaje en Outlook sin enviarlo. "
            "Las fechas corresponden al rango digitado en la extracción de Fénix."
        ),
        bootstyle="secondary",
    ).pack(anchor="w", pady=(8, 0))

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

    def escribir_correo(mensaje):
        def actualizar():
            txt_consola.insert("end", mensaje + "\n")
            txt_consola.see("end")
        vista.after(0, actualizar)

    def validar_fecha(texto):
        try:
            datetime.strptime(texto.strip(), "%d/%m/%Y")
            return True
        except ValueError:
            return False

    def ejecutar_correo(inicial, final, automatico):
        try:
            import pythoncom
            from modules.correo_validacion_materiales import (
                buscar_informe_mas_reciente,
                crear_correo_outlook,
                generar_adjuntos_por_hoja,
            )

            pythoncom.CoInitialize()
            try:
                escribir_correo("📂 Buscando el informe más reciente...")
                informe = buscar_informe_mas_reciente(proyecto_actual)
                escribir_correo(f"📄 Informe: {informe.name}")
                escribir_correo("📎 Generando libros separados por hoja...")
                adjuntos = generar_adjuntos_por_hoja(informe)
                escribir_correo(f"✅ Adjuntos generados: {len(adjuntos)}")
                crear_correo_outlook(
                    inicial,
                    final,
                    adjuntos,
                    enviar_automaticamente=automatico,
                )
                if automatico:
                    escribir_correo("✅ Correo enviado automáticamente.")
                else:
                    escribir_correo(
                        "✅ Correo abierto en Outlook para revisión."
                    )
            finally:
                pythoncom.CoUninitialize()
        except Exception as error:
            escribir_correo(f"❌ ERROR: {error}")
            vista.after(
                0,
                lambda: messagebox.showerror(
                    "Error al generar correo", str(error)
                ),
            )
        finally:
            vista.after(0, lambda: boton_correo.configure(state="normal"))

    def iniciar_correo():
        inicial = fecha_inicial.get().strip()
        final = fecha_final.get().strip()
        if not validar_fecha(inicial) or not validar_fecha(final):
            messagebox.showerror(
                "Fechas no válidas",
                "Ingrese ambas fechas con el formato DD/MM/AAAA.",
            )
            return

        automatico = modo_correo.get() == "Envío automático"
        if automatico:
            continuar = messagebox.askyesno(
                "Confirmar envío automático",
                (
                    "El correo se enviará directamente y no se abrirá "
                    "para revisión.\n\n"
                    f"Período: {inicial} al {final}\n"
                    "Adjuntos: todas las hojas de resultados\n\n"
                    "¿Desea continuar?"
                ),
                icon="warning",
            )
            if not continuar:
                return

        txt_consola.delete("1.0", "end")
        escribir_correo(
            f"📌 Período del correo: {inicial} al {final}"
        )
        escribir_correo(f"📨 Modo: {modo_correo.get()}")
        boton_correo.configure(state="disabled")
        threading.Thread(
            target=ejecutar_correo,
            args=(inicial, final, automatico),
            daemon=True,
        ).start()

    boton_correo.configure(command=iniciar_correo)
