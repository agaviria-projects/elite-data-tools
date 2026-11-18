import threading
from tkinter import messagebox

import pythoncom
import ttkbootstrap as ttk

from ui.base_view import crear_vista

from modules.informe_ans.config.correos import MODO_PRUEBA
from modules.informe_ans.config.zonas import ZONAS
from modules.informe_ans.config.parametros import (
    ARCHIVO_FENIX,
    CARPETA_HTML,
)
from modules.informe_ans.controller import InformeAnsController
from modules.informe_ans.src.generador_html import (
    PLANTILLA_CORREO,
    PLANTILLA_FOOTER,
)


# ==========================================================
# VALIDAR MÓDULO
# ==========================================================

def validar_modulo() -> dict[str, bool]:
    """
    Comprueba que los recursos principales del módulo
    estén disponibles.
    """

    return {
        "Archivo FENIX": ARCHIVO_FENIX.exists(),
        "Plantilla principal": PLANTILLA_CORREO.exists(),
        "Plantilla footer": PLANTILLA_FOOTER.exists(),
        "Carpeta de salida": CARPETA_HTML.exists(),
        "Motor Seguimiento ANS": True,
    }


# ==========================================================
# ACTUALIZAR ESTADO
# ==========================================================

def actualizar_estado(frame) -> None:
    """
    Actualiza visualmente el estado de los componentes
    del módulo.
    """

    for widget in frame.winfo_children():
        widget.destroy()

    for nombre, disponible in validar_modulo().items():

        ttk.Label(
            frame,
            text=(
                f"{'🟢' if disponible else '🔴'} "
                f"{nombre}"
            ),
        ).pack(
            anchor="w",
            pady=2,
        )


# ==========================================================
# INTERFAZ
# ==========================================================

def crear_seguimiento_ans(panel) -> None:
    """
    Crea la interfaz integrada del módulo Seguimiento ANS.
    """

    vista = crear_vista(panel)

    controller = InformeAnsController()

    # ======================================================
    # ENCABEZADO
    # ======================================================

    ttk.Label(
        vista,
        text="📨 Seguimiento ANS",
        font=("Segoe UI", 24, "bold"),
        bootstyle="success",
    ).pack(
        anchor="w",
    )

    ttk.Label(
        vista,
        text=(
            "Generación, revisión y envío controlado "
            "de correos de seguimiento ANS."
        ),
    ).pack(
        anchor="w",
        pady=(0, 15),
    )

    # ======================================================
    # PANELES SUPERIORES
    # ======================================================

    cuerpo = ttk.Frame(vista)

    cuerpo.pack(
        fill="both",
        expand=False,
    )

    cuerpo.columnconfigure(
        (0, 1),
        weight=1,
    )

    izquierda = ttk.Frame(cuerpo)

    izquierda.grid(
        row=0,
        column=0,
        sticky="nsew",
        padx=(0, 8),
    )

    derecha = ttk.Frame(cuerpo)

    derecha.grid(
        row=0,
        column=1,
        sticky="nsew",
        padx=(8, 0),
    )

    # ======================================================
    # ARCHIVO DE ENTRADA
    # ======================================================

    frm_archivo = ttk.Labelframe(
        izquierda,
        text="Archivo de entrada",
        padding=10,
    )

    frm_archivo.pack(
        fill="both",
        expand=True,
    )

    ruta_archivo = ttk.StringVar(
        value=str(ARCHIVO_FENIX),
    )

    # Mantener la referencia de la variable
    vista.ruta_archivo = ruta_archivo

    ttk.Entry(
        frm_archivo,
        textvariable=ruta_archivo,
        state="readonly",
    ).pack(
        fill="x",
        pady=(0, 8),
    )

    ttk.Label(
        frm_archivo,
        text=(
            "El módulo utilizará el archivo FENIX_ANS.xlsx "
            "ubicado en la carpeta de entrada."
        ),
        bootstyle="secondary",
        wraplength=450,
        justify="left",
    ).pack(
        anchor="w",
    )

    # ======================================================
    # ESTADO DEL MÓDULO
    # ======================================================

    frm_estado = ttk.Labelframe(
        derecha,
        text="Estado del módulo",
        padding=10,
    )

    frm_estado.pack(
        fill="both",
        expand=True,
    )

    actualizar_estado(frm_estado)

    # ======================================================
    # PROCESO
    # ======================================================

    modo_ejecucion = ttk.StringVar(
        value="Modo revisión",
    )

    solo_primer_correo = ttk.BooleanVar(
        value=False,
    )

    # Mantener referencias
    vista.modo_ejecucion = modo_ejecucion
    vista.solo_primer_correo = solo_primer_correo

    acciones = ttk.Labelframe(
        vista,
        text="Proceso",
        padding=12,
    )

    acciones.pack(
        fill="x",
        pady=(20, 15),
    )

    fila_superior = ttk.Frame(acciones)

    fila_superior.pack(
        fill="x",
    )

    ttk.Label(
        fila_superior,
        text="Modo de ejecución:",
    ).pack(
        side="left",
        padx=(0, 10),
    )

    cmb_modo = ttk.Combobox(
        fila_superior,
        textvariable=modo_ejecucion,
        values=[
            "Modo revisión",
            "Envío automático",
        ],
        state="readonly",
        width=22,
    )

    cmb_modo.pack(
        side="left",
    )

    boton_generar = ttk.Button(
        fila_superior,
        text="▶ Generar correos",
        width=25,
        bootstyle="success",
        cursor="hand2",
    )

    boton_generar.pack(
        side="right",
    )

    fila_zonas = ttk.Frame(
        acciones
    )

    fila_zonas.pack(
        fill="x",
        pady=(12, 0),
    )

    ttk.Label(
        fila_zonas,
        text="Zonas:",
    ).pack(
        side="left",
        padx=(0, 10),
    )

    variables_zona = {}
    controles_zona = {}

    seleccionar_todas = ttk.BooleanVar(
        value=False
    )

    for nombre_zona, configuracion_zona in ZONAS.items():

        variable_zona = ttk.BooleanVar(
            value=(
                nombre_zona == "METROPOLITANA"
            )
        )

        variables_zona[nombre_zona] = variable_zona

        texto_zona = nombre_zona

        # if not configuracion_zona.get(
        #     "envio",
        #     False,
        # ):
        #     texto_zona += " (solo revisión)"

        def sincronizar_todas_autorizadas():
            """
            Mantiene el interruptor 'Todas las autorizadas'
            sincronizado con las selecciones individuales.
            """

            clave_modo = (
                "envio"
                if modo_ejecucion.get() == "Envío automático"
                else "revision"
            )

            zonas_activas = [
                nombre
                for nombre, cfg in ZONAS.items()
                if cfg.get(
                    clave_modo,
                    False,
                )
            ]

            seleccionar_todas.set(
                all(
                    variables_zona[nombre].get()
                    for nombre in zonas_activas
                )
            )

        chk_zona = ttk.Checkbutton(
            fila_zonas,
            text=texto_zona,
            variable=variable_zona,
            command=sincronizar_todas_autorizadas,
            bootstyle="success-round-toggle",
        )

        chk_zona.pack(
            side="left",
            padx=(0, 10),
        )

        controles_zona[
            nombre_zona
        ] = chk_zona

    vista.variables_zona = variables_zona
    vista.seleccionar_todas = seleccionar_todas

    def actualizar_todas_zonas():
        """
        Marca o desmarca únicamente las zonas autorizadas.
        """

        nuevo_estado = seleccionar_todas.get()

        for nombre_zona, configuracion_zona in ZONAS.items():

            clave_modo = (
                "envio"
                if modo_ejecucion.get() == "Envío automático"
                else "revision"
            )

            if configuracion_zona.get(
                clave_modo,
                False,
            ):
                variables_zona[
                    nombre_zona
                ].set(
                    nuevo_estado
                )

    ttk.Checkbutton(
        fila_zonas,
        text="Todas disponibles",
        variable=seleccionar_todas,
        command=actualizar_todas_zonas,
        bootstyle="info-round-toggle",
    ).pack(
        side="right",
    )

    def actualizar_disponibilidad_zonas(event=None):
        """
        En revisión habilita las zonas preparadas para prueba.
        En envío automático bloquea las no autorizadas.
        """

        es_envio = (
            modo_ejecucion.get()
            == "Envío automático"
        )

        clave_modo = (
            "envio"
            if es_envio
            else "revision"
        )

        for nombre_zona, cfg in ZONAS.items():

            disponible = cfg.get(
                clave_modo,
                False,
            )

            controles_zona[
                nombre_zona
            ].configure(
                state=(
                    "normal"
                    if disponible
                    else "disabled"
                )
            )

            if not disponible:
                variables_zona[
                    nombre_zona
                ].set(False)

        seleccionar_todas.set(False)
        sincronizar_todas_autorizadas()

    cmb_modo.bind(
        "<<ComboboxSelected>>",
        actualizar_disponibilidad_zonas,
    )

    actualizar_disponibilidad_zonas()

    fila_inferior = ttk.Frame(acciones)

    fila_inferior.pack(
        fill="x",
        pady=(12, 0),
    )

    ttk.Checkbutton(
        fila_inferior,
        text="Procesar únicamente el primer correo",
        variable=solo_primer_correo,
        bootstyle="info-round-toggle",
    ).pack(
        side="left",
    )

    ttk.Label(
        fila_inferior,
        text=(
            "Modo revisión: abre los correos en Outlook "
            "y no realiza ningún envío."
        ),
        bootstyle="secondary",
    ).pack(
        side="right",
    )

    # ======================================================
    # CONSOLA
    # ======================================================

    frm_consola = ttk.Labelframe(
        vista,
        text="Consola",
        padding=8,
    )

    frm_consola.pack(
        fill="both",
        expand=True,
    )

    txt_consola = ttk.Text(
        frm_consola,
        height=10,
        wrap="word",
        font=("Consolas", 10),
    )

    txt_consola.pack(
        fill="both",
        expand=True,
    )

    txt_consola.insert(
        "end",
        "Esperando ejecución...\n",
    )

    vista.txt_consola = txt_consola
    vista.boton_generar = boton_generar

    # ======================================================
    # FUNCIONES DE CONSOLA
    # ======================================================

    def escribir_consola(mensaje: str) -> None:
        """
        Escribe mensajes en la consola desde el hilo principal.
        """

        def actualizar():
            txt_consola.insert(
                "end",
                mensaje + "\n",
            )

            txt_consola.see("end")

        vista.after(
            0,
            actualizar,
        )

    def limpiar_consola() -> None:
        txt_consola.delete(
            "1.0",
            "end",
        )

    # ======================================================
    # FINALIZAR EJECUCIÓN
    # ======================================================

    def finalizar_ejecucion(resultado) -> None:
        """
        Restaura la interfaz después de una ejecución correcta.
        """

        boton_generar.configure(
            state="normal",
        )

        escribir_consola("")
        escribir_consola("=" * 60)
        escribir_consola("RESUMEN FINAL")
        escribir_consola("=" * 60)

        escribir_consola(
            f"✔ Correos generados : "
            f"{resultado.correos_generados}"
        )

        escribir_consola(
            f"✔ Total grupos      : "
            f"{resultado.total_grupos}"
        )

        escribir_consola(
            f"✔ Total pedidos     : "
            f"{resultado.total_pedidos:,}"
        )

        escribir_consola(
            f"✔ Tiempo ejecución  : "
            f"{resultado.tiempo_segundos:.2f} segundos"
        )

        escribir_consola(
            f"✔ Ruta de salida    : "
            f"{resultado.ruta_salida}"
        )

        vista.after(
            0,
            lambda: messagebox.showinfo(
                "Seguimiento ANS",
                (
                    "El proceso finalizó correctamente.\n\n"
                    f"Correos generados: "
                    f"{resultado.correos_generados}\n"
                    f"Total pedidos: "
                    f"{resultado.total_pedidos:,}"
                ),
            ),
        )

    # ======================================================
    # MANEJAR ERROR
    # ======================================================

    def manejar_error(error: Exception) -> None:
        """
        Restaura la interfaz y muestra el error ocurrido.
        """

        escribir_consola("")
        escribir_consola(
            f"❌ ERROR: {error}"
        )

        vista.after(
            0,
            lambda: boton_generar.configure(
                state="normal",
            ),
        )

        vista.after(
            0,
            lambda: messagebox.showerror(
                "Error en Seguimiento ANS",
                str(error),
            ),
        )

    # ======================================================
    # EJECUTAR EN SEGUNDO PLANO
    # ======================================================

    def ejecutar_proceso(
        enviar_automaticamente: bool,
        procesar_solo_primero: bool,
        zonas: tuple[str, ...],
    ) -> None:
        """
        Ejecuta el controlador sin bloquear DataSuite.

        Inicializa COM dentro del hilo para permitir
        la comunicación con Outlook.
        """

        pythoncom.CoInitialize()

        try:
            resultado = controller.ejecutar(
                archivo_fenix=ARCHIVO_FENIX,
                modo_prueba=MODO_PRUEBA,
                solo_primer_correo=procesar_solo_primero,
                abrir_outlook=True,
                enviar_automaticamente=enviar_automaticamente,
                zonas=zonas,
                informar=escribir_consola,
            )

            vista.after(
                0,
                lambda: finalizar_ejecucion(
                    resultado
                ),
            )

        except Exception as error:
            manejar_error(error)

        finally:
            pythoncom.CoUninitialize()

    # ======================================================
    # INICIAR EJECUCIÓN
    # ======================================================

    def iniciar_ejecucion() -> None:
        """
        Valida el modo seleccionado e inicia el proceso.
        """

        if not ARCHIVO_FENIX.exists():
            messagebox.showerror(
                "Archivo no encontrado",
                (
                    "No se encontró el archivo FENIX:\n\n"
                    f"{ARCHIVO_FENIX}"
                ),
            )
            return

        modo_seleccionado = (
            modo_ejecucion.get()
        )

        zonas_actuales = tuple(
            nombre_zona
            for nombre_zona, variable_zona
            in variables_zona.items()
            if variable_zona.get()
        )

        if not zonas_actuales:
            messagebox.showwarning(
                "Zona requerida",
                "Seleccione al menos una zona autorizada.",
            )
            return
        enviar_automaticamente = (
            modo_seleccionado
            == "Envío automático"
        )

        if enviar_automaticamente:

            zonas_bloqueadas = [
                zona
                for zona in zonas_actuales
                if not ZONAS[zona].get(
                    "envio",
                    False,
                )
            ]

            if zonas_bloqueadas:
                messagebox.showerror(
                    "Zona no autorizada",
                    (
                        "No está autorizado el envío automático para:\n\n"
                        + ", ".join(zonas_bloqueadas)
                    ),
                )
                return

        if enviar_automaticamente:

            if solo_primer_correo.get():
                cantidad = "1 correo"
            else:
                total_correos = sum(
                    ZONAS[zona][
                        "correos_estimados"
                    ]
                    for zona in zonas_actuales
                )

                cantidad = (
                    "1 correo"
                    if total_correos == 1
                    else f"{total_correos} correos"
                )

            destino = (
                "destinatarios de prueba"
                if MODO_PRUEBA
                else "destinatarios de producción"
            )

            confirmar = messagebox.askyesno(
                "Confirmar envío automático",
                (
                    f"Se enviarán automáticamente "
                    f"{cantidad}.\n\n"
                    f"Zonas: {', '.join(zonas_actuales)}.\n\n"
                    f"Destino: {destino}.\n\n"
                    "Los mensajes no se abrirán para "
                    "revisión manual.\n\n"
                    "¿Desea continuar?"
                ),
                icon="warning",
            )

            if not confirmar:
                return

        limpiar_consola()

        if MODO_PRUEBA:
            escribir_consola(
                "🧪 Destinatarios: PRUEBA"
            )
        else:
            escribir_consola(
                "⚠ Destinatarios: PRODUCCIÓN"
            )

        escribir_consola(
            f"📌 Modo de ejecución: "
            f"{modo_seleccionado}"
        )

        escribir_consola(
            "📍 Zonas seleccionadas: "
            + ", ".join(zonas_actuales)
        )

        total_estimado = sum(
            ZONAS[zona][
                "correos_estimados"
            ]
            for zona in zonas_actuales
        )

        escribir_consola(
            "📨 Correos a procesar: "
            + (
                "solo el primero"
                if solo_primer_correo.get()
                else str(total_estimado)
            )
        )

        escribir_consola("")

        boton_generar.configure(
            state="disabled",
        )

        procesar_solo_primero = (
            solo_primer_correo.get()
        )

        hilo = threading.Thread(
            target=ejecutar_proceso,
            args=(
                enviar_automaticamente,
                procesar_solo_primero,
                zonas_actuales,
            ),
            daemon=True,
        )

        hilo.start()

    # ======================================================
    # CONECTAR BOTÓN
    # ======================================================

    boton_generar.configure(
        command=iniciar_ejecucion,
    )
