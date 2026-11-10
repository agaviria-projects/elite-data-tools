import ttkbootstrap as ttk

import threading
import queue
import tkinter as tk
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


def configurar_icono_ventana(ventana):
    """Usa los recursos del proyecto, independientemente del directorio de inicio."""
    for nombre in ('LOGO.ico', 'icono.ico'):
        ruta_icono = BASE / 'assets' / nombre
        if ruta_icono.is_file():
            try:
                ventana.iconbitmap(str(ruta_icono))
                return
            except tk.TclError:
                continue
    ruta_png = BASE / 'assets' / 'LOGO.png'
    if ruta_png.is_file():
        try:
            imagen = tk.PhotoImage(master=ventana, file=str(ruta_png))
            ventana.iconphoto(False, imagen)
            ventana._icono_datasuite = imagen  # Conservar la referencia Tk.
        except tk.TclError:
            pass  # Un recurso inválido no debe bloquear la operación.


def dialogo_datasuite(padre, titulo, mensaje, confirmar=False):
    """Aviso modal propio con logo: no modifica iconos globales de Windows."""
    ventana = ttk.Toplevel(padre)
    ventana.withdraw()
    ventana.title(titulo)
    configurar_icono_ventana(ventana)
    ventana.transient(padre.winfo_toplevel())
    ventana.resizable(True, True)
    ancho = min(640, max(350, ventana.winfo_screenwidth() - 60))
    alto = min(540 if confirmar else 300, max(230, ventana.winfo_screenheight() - 100))
    ventana.geometry(f'{ancho}x{alto}')
    marco = ttk.Frame(ventana, padding=16)
    marco.pack(fill='both', expand=True)
    ttk.Label(marco, text=titulo, font=('Segoe UI', 13, 'bold'),
              bootstyle='info').pack(anchor='w', pady=(0, 12))
    cuerpo = ttk.Frame(marco)
    cuerpo.pack(fill='both', expand=True)
    texto = tk.Text(cuerpo, wrap='word', font=('Segoe UI', 10),
                    background=ttk.Style().colors.bg,
                    foreground=ttk.Style().colors.fg,
                    relief='flat', borderwidth=0)
    barra = ttk.Scrollbar(cuerpo, orient='vertical', command=texto.yview)
    barra.pack(side='right', fill='y')
    texto.pack(side='left', fill='both', expand=True)
    texto.configure(yscrollcommand=barra.set)
    texto.insert('1.0', mensaje)
    texto.configure(state='disabled')
    botones = ttk.Frame(marco)
    botones.pack(fill='x', pady=(12, 0))
    respuesta = [False]

    def cerrar(aceptar=False):
        respuesta[0] = aceptar
        ventana.destroy()

    if confirmar:
        ttk.Button(botones, text='Cancelar', bootstyle='secondary',
                    command=cerrar).pack(side='right')
        ttk.Button(botones, text='Continuar', bootstyle='success',
                    command=lambda: cerrar(True)).pack(side='right', padx=(0, 10))
    else:
        ttk.Button(botones, text='Aceptar', command=lambda: cerrar(True)).pack(side='right')
    ventana.protocol('WM_DELETE_WINDOW', cerrar)
    ventana.bind('<Escape>', lambda event: cerrar())
    ventana.deiconify()
    ventana.update_idletasks()
    raiz = padre.winfo_toplevel()
    x = max(0, min(raiz.winfo_rootx() + (raiz.winfo_width() - ancho) // 2,
                   ventana.winfo_screenwidth() - ancho))
    y = max(0, min(raiz.winfo_rooty() + (raiz.winfo_height() - alto) // 2,
                   ventana.winfo_screenheight() - alto))
    ventana.geometry(f'+{x}+{y}')
    ventana.wait_visibility()
    ventana.grab_set()
    padre.wait_window(ventana)
    return respuesta[0]


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

    try:
        from modules.correo_validacion_materiales import cargar_control_exportacion
        control = cargar_control_exportacion(proyecto_actual)
        # Invalidar antes de lanzar: incluso un error de sintaxis/importación del
        # validador debe impedir adjuntar el informe de una ejecución anterior.
        previo = control.iniciar_ejecucion(proyecto_actual)['ejecucion']
        ejecutar_secuencia(proyecto_actual, pasos, callback=escribir)
        informe, datos = control.obtener_informe_verificado(proyecto_actual)
        if datos['ejecucion'] == previo:
            raise ValueError('No se registró una ejecución nueva. Revise los errores de la consola.')
        escribir('\nValidación finalizada correctamente.\n' + control.resumen_control(informe, datos))
    except Exception as error:
        escribir('\nERROR: no se confirmó la validación. ' + str(error))


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

    # Panel superior desplazable y consola separada: los controles no pueden
    # consumir toda la altura y dejar la consola fuera de la ventana.
    division = ttk.Panedwindow(vista, orient='vertical')
    division.pack(fill='both', expand=True)
    superior = ttk.Frame(division)
    lienzo = tk.Canvas(superior, highlightthickness=0, borderwidth=0,
                       background=ttk.Style().colors.bg, height=320)
    barra_superior = ttk.Scrollbar(superior, orient='vertical', command=lienzo.yview)
    barra_superior.pack(side='right', fill='y')
    barra_horizontal = ttk.Scrollbar(superior, orient='horizontal', command=lienzo.xview)
    barra_horizontal.pack(side='bottom', fill='x')
    lienzo.pack(side='left', fill='both', expand=True)
    lienzo.configure(yscrollcommand=barra_superior.set,
                     xscrollcommand=barra_horizontal.set)
    controles = ttk.Frame(lienzo)
    ventana_controles = lienzo.create_window((0, 0), window=controles, anchor='nw')

    def ajustar_controles(event=None):
        lienzo.itemconfigure(ventana_controles,
            width=max(lienzo.winfo_width(), controles.winfo_reqwidth()))
        lienzo.configure(scrollregion=lienzo.bbox('all'))

    controles.bind('<Configure>', ajustar_controles)
    lienzo.bind('<Configure>', ajustar_controles)
    division.add(superior, weight=0)

    cuerpo = ttk.Frame(controles)

    cuerpo.pack(fill="x", expand=False)

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

        controles,

        text="Proceso",

        padding=12

    )

    acciones.pack(fill="x", pady=(14, 10))

    boton_validar = ttk.Button(

        acciones,

        text="▶ Validar Materiales",

        width=28,

        bootstyle="success",

        cursor="hand2",

        command=ejecutar_validacion

    )

    boton_validar.pack(pady=(2, 8))

    # ------------------------------------------------------
    # GENERACIÓN DE CORREOS
    # ------------------------------------------------------

    frm_correo = ttk.Frame(acciones)
    frm_correo.pack(fill="x")

    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    fecha_inicial = ttk.StringVar(value=fecha_hoy)
    fecha_final = ttk.StringVar(value=fecha_hoy)
    modo_correo = ttk.StringVar(value="Modo revisión")
    modalidad_adjuntos = ttk.StringVar(value="Libro completo")
    confirmar_lectura = ttk.BooleanVar(value=True)

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
    ttk.Combobox(
        frm_correo,
        textvariable=modalidad_adjuntos,
        values=["Libro completo", "Separados por hojas"],
        state="readonly",
        width=20,
    ).grid(row=0, column=7, padx=(0, 18), pady=4)

    boton_correo = ttk.Button(
        frm_correo,
        text="✉ Generar correos",
        width=23,
        bootstyle="info",
        cursor="hand2",
    )
    boton_correo.grid(row=0, column=8, pady=4)

    ttk.Checkbutton(
        frm_correo,
        text="Solicitar confirmación de lectura",
        variable=confirmar_lectura,
        bootstyle="success-round-toggle",
        cursor="hand2",
    ).grid(row=1, column=6, columnspan=3, pady=(5, 0), sticky="w")

    ttk.Label(
        acciones,
        text=(
            "Modo revisión abre el mensaje en Outlook sin enviarlo. "
            "Las fechas corresponden al rango digitado en la extracción de Fénix."
        ),
        bootstyle="secondary",
    ).pack(anchor="w", pady=(6, 0))

    from modules.seguimiento_lectura import (
        DESTINATARIOS, COPIAS, CORTES, BOGOTA, cargar_configuracion,
        guardar_configuracion, validar_opciones,
    )
    try:
        configuracion = cargar_configuracion()
    except (ValueError, KeyError, OSError) as error:
        messagebox.showerror('Configuración de recordatorios',
            'No se pudo cargar la configuración guardada. Revísela antes de enviar.\n' + str(error))
        from modules.seguimiento_lectura import INTERVALOS_POR_CORTE, MAXIMOS_POR_CORTE
        configuracion = dict(activo=False, corte='Mañana',
                             destinatarios=DESTINATARIOS + COPIAS,
                             esperas=dict(CORTES),
                             intervalos=dict(INTERVALOS_POR_CORTE),
                             maximos=dict(MAXIMOS_POR_CORTE))
    activar_seguimiento = ttk.BooleanVar(value=configuracion['activo'])
    corte = ttk.StringVar(value=configuracion['corte'])
    esperas_por_corte = {nombre: ttk.StringVar(value=str(configuracion['esperas'][nombre]))
                         for nombre in CORTES}
    intervalos_por_corte = {nombre: ttk.StringVar(value=str(configuracion['intervalos'][nombre]))
                            for nombre in CORTES}
    maximos_por_corte = {nombre: ttk.StringVar(value=str(configuracion['maximos'][nombre]))
                         for nombre in CORTES}
    seleccion_destinatarios = {
        direccion: ttk.BooleanVar(value=direccion in configuracion['destinatarios'])
        for direccion in DESTINATARIOS + COPIAS
    }
    seguimiento_frame = ttk.Frame(acciones)
    seguimiento_frame.pack(fill='x', pady=(8, 0))
    # Agrupar ajustes y consulta en una misma fila, sin un hueco flexible.
    ttk.Checkbutton(seguimiento_frame, text='Recordatorios automáticos',
                    variable=activar_seguimiento).grid(row=0, column=0, sticky='w')
    ttk.Label(seguimiento_frame, text='Corte:').grid(row=0, column=1, padx=(10, 4))
    selector_corte = ttk.Combobox(seguimiento_frame, textvariable=corte,
                                 values=list(CORTES), state='readonly', width=9)
    selector_corte.grid(row=0, column=2)
    ttk.Label(seguimiento_frame, text='Espera inicial (min):').grid(row=0, column=3, padx=(10, 4))
    entrada_espera = ttk.Entry(seguimiento_frame,
        textvariable=esperas_por_corte[corte.get()], width=5)
    entrada_espera.grid(row=0, column=4)
    ttk.Label(seguimiento_frame, text='Intervalo (min):').grid(row=0, column=5, padx=(10, 4))
    entrada_intervalo = ttk.Entry(seguimiento_frame,
        textvariable=intervalos_por_corte[corte.get()], width=4)
    entrada_intervalo.grid(row=0, column=6)
    ttk.Label(seguimiento_frame, text='Máximo:').grid(row=0, column=7, padx=(10, 4))
    entrada_maximo = ttk.Entry(seguimiento_frame,
        textvariable=maximos_por_corte[corte.get()], width=4)
    entrada_maximo.grid(row=0, column=8)

    def cambiar_corte(event=None):
        # Cada corte conserva lo digitado, incluso antes de Guardar ajustes.
        seleccionado = corte.get()
        entrada_espera.configure(textvariable=esperas_por_corte[seleccionado])
        entrada_intervalo.configure(textvariable=intervalos_por_corte[seleccionado])
        entrada_maximo.configure(textvariable=maximos_por_corte[seleccionado])

    selector_corte.bind('<<ComboboxSelected>>', cambiar_corte)
    resumen_destinatarios = ttk.StringVar()

    def resumir_destinatarios(*args):
        cantidad = sum(bool(variable.get()) for variable in seleccion_destinatarios.values())
        resumen_destinatarios.set(f'Recordatorios seleccionados: {cantidad}/11 · Correo inicial: 8 Para + 3 CC')

    for variable in seleccion_destinatarios.values():
        variable.trace_add('write', resumir_destinatarios)
    resumir_destinatarios()

    def elegir_destinatarios():
        ventana = ttk.Toplevel(vista)
        ventana.title('Destinatarios de recordatorios')
        configurar_icono_ventana(ventana)
        ventana.geometry('600x550')
        marco = ttk.Frame(ventana, padding=16)
        marco.pack(fill='both', expand=True)
        ttk.Label(marco, text='Marcar = activar recordatorios para los NUEVOS informes.').pack(anchor='w')
        ttk.Label(marco, text='Sin marcar = recibe el correo inicial, sin recordatorios.').pack(anchor='w', pady=(0, 10))
        for nombre, lista in (('Destinatarios principales', DESTINATARIOS), ('Copias (CC)', COPIAS)):
            ttk.Label(marco, text=nombre, font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(8, 4))
            for direccion in lista:
                ttk.Checkbutton(marco, text=direccion,
                    variable=seleccion_destinatarios[direccion]).pack(anchor='w', pady=2)
        ttk.Label(marco, text='Los seguimientos existentes se cancelan desde Ver seguimiento.').pack(anchor='w', pady=10)
        ttk.Button(marco, text='Listo', command=ventana.destroy).pack(anchor='e')

    ttk.Button(seguimiento_frame, text='Destinatarios', command=elegir_destinatarios).grid(
        row=1, column=0, pady=(8, 0), sticky='w')

    def recoger_opciones():
        try:
            esperas = {nombre: int(variable.get().strip())
                       for nombre, variable in esperas_por_corte.items()}
            intervalos = {nombre: int(variable.get().strip())
                          for nombre, variable in intervalos_por_corte.items()}
            maximos = {nombre: int(variable.get().strip())
                       for nombre, variable in maximos_por_corte.items()}
            seleccionado = corte.get()
            opciones = dict(
                activo=activar_seguimiento.get(), corte=seleccionado,
                esperas=esperas, intervalos=intervalos, maximos=maximos,
                espera=esperas[seleccionado],
                intervalo=intervalos[seleccionado],
                maximo=maximos[seleccionado],
                destinatarios=[direccion for direccion, variable in seleccion_destinatarios.items()
                               if variable.get()],
            )
        except (ValueError, KeyError):
            raise ValueError('Ingrese números enteros para las esperas, los intervalos y los máximos de ambos cortes.') from None
        for nombre in CORTES:
            validar_opciones(esperas[nombre], intervalos[nombre], maximos[nombre],
                             opciones['destinatarios'])
        if opciones['activo'] and not opciones['destinatarios']:
            raise ValueError('Seleccione al menos un destinatario de recordatorios.')
        return opciones

    def guardar_ajustes():
        try:
            guardar_configuracion(recoger_opciones())
        except (ValueError, OSError) as error:
            messagebox.showerror('No se guardaron los ajustes', str(error))
            return
        dialogo_datasuite(vista, 'Ajustes guardados',
            'Se guardaron por separado la espera, el intervalo y el máximo de Mañana y Tarde; también los destinatarios.\n'
            'No se envió ningún correo. Se aplicarán a informes nuevos.')

    ttk.Button(seguimiento_frame, text='Guardar ajustes', command=guardar_ajustes).grid(
        row=1, column=1, columnspan=2, padx=(10, 0), pady=(8, 0), sticky='w')
    ttk.Label(seguimiento_frame, textvariable=resumen_destinatarios).grid(
        row=1, column=3, columnspan=7, padx=(10, 0), pady=(8, 0), sticky='w')
    ttk.Label(acciones, text='Horario Colombia: hasta las 15:30. Sin confirmación no significa no leído. Revise el corte antes de enviar.',
              bootstyle='secondary').pack(anchor='w', pady=(5, 0))

    # ------------------------------------------------------

    consola = ttk.Labelframe(

        division,

        text="Consola",

        padding=8

    )

    consola.configure(height=160)
    consola.pack_propagate(False)
    division.add(consola, weight=1)

    def reservar_consola(event=None):
        altura = division.winfo_height()
        if altura < 200:
            return
        limite = max(60, altura - 155)
        if division.sashpos(0) > limite:
            division.sashpos(0, limite)

    division.bind('<Configure>', reservar_consola)
    vista.after_idle(reservar_consola)

    global txt_consola

    txt_consola = ttk.Text(

        consola,

        height=8,

        wrap="word"

    )

    txt_consola.pack(

        side="left",

        fill="both",

        expand=True

    )

    scroll_consola = ttk.Scrollbar(

        consola,

        orient="vertical",

        command=txt_consola.yview

    )

    scroll_consola.pack(side="right", fill="y")

    txt_consola.configure(yscrollcommand=scroll_consola.set)

    txt_consola.insert(

        "end",

        "Esperando ejecución...\n"

    )

    cola_correo = queue.Queue()

    def escribir_correo(mensaje):
        cola_correo.put(mensaje)

    def actualizar_cola():
        while True:
            try:
                mensaje = cola_correo.get_nowait()
            except queue.Empty:
                break
            if callable(mensaje):
                mensaje()
            else:
                txt_consola.insert('end', str(mensaje) + '\n')
                txt_consola.see('end')
        vista.after(300, actualizar_cola)

    vista.after(300, actualizar_cola)
    from modules.seguimiento_lectura import iniciar_monitor, consultar, cancelar
    iniciar_monitor(escribir_correo)

    def ver_seguimiento():
        from modules.informe_seguimiento import (
            validar_fechas, fecha_registro, estado_visible,
            consultar_informe, exportar_informe,
        )
        ventana = ttk.Toplevel(vista)
        ventana.title('Seguimiento de correos')
        configurar_icono_ventana(ventana)
        ventana.geometry('1120x500')
        ventana.minsize(760, 350)
        filtros = ttk.Frame(ventana, padding=(10, 8))
        filtros.pack(fill='x')
        hoy = datetime.now(BOGOTA).strftime('%d/%m/%Y')
        desde_informe = ttk.StringVar(value=hoy)
        hasta_informe = ttk.StringVar(value=hoy)
        ttk.Label(filtros, text='Desde:').pack(side='left', padx=(0, 5))
        ttk.Entry(filtros, textvariable=desde_informe, width=12).pack(side='left')
        ttk.Label(filtros, text='Hasta:').pack(side='left', padx=(12, 5))
        ttk.Entry(filtros, textvariable=hasta_informe, width=12).pack(side='left')
        ttk.Label(filtros, text='DD/MM/AAAA · fecha del envío original',
                  bootstyle='secondary').pack(side='left', padx=12)
        estado_consulta = ttk.StringVar(value='')
        ttk.Label(ventana, textvariable=estado_consulta).pack(anchor='w', padx=10, pady=(0, 5))
        marco_tabla = ttk.Frame(ventana)
        marco_tabla.pack(fill='both', expand=True)
        columnas = ('creado', 'asunto', 'destinatario', 'rol', 'estado', 'intentos', 'maximo', 'proximo', 'detalle')
        tabla = ttk.Treeview(marco_tabla, columns=columnas, show='headings', height=12)
        for campo in columnas:
            tabla.heading(campo, text='Intentos de recordatorio' if campo == 'intentos' else campo.capitalize())
            tabla.column(campo, width=140 if campo != 'detalle' else 330)
        scroll_vertical = ttk.Scrollbar(marco_tabla, orient='vertical', command=tabla.yview)
        scroll_vertical.pack(side='right', fill='y')
        tabla.pack(side='left', fill='both', expand=True)
        scroll_tabla = ttk.Scrollbar(ventana, orient='horizontal', command=tabla.xview)
        scroll_tabla.pack(fill='x')
        tabla.configure(xscrollcommand=scroll_tabla.set, yscrollcommand=scroll_vertical.set)
        ttk.Label(ventana, text='Sin confirmación no significa no leído. Los envíos no verificados se filtran por creación.',
                  bootstyle='secondary').pack(anchor='w', padx=10)

        def refrescar():
            try:
                inicio, fin = validar_fechas(desde_informe.get(), hasta_informe.get())
                filas = [fila for fila in consultar() if inicio <= fecha_registro(fila) <= fin]
            except Exception as error:
                messagebox.showerror('No se pudo consultar el seguimiento', str(error), parent=ventana)
                return
            tabla.delete(*tabla.get_children())
            for fila in filas:
                estado = fila['estado']
                etiqueta_estado, detalle = estado_visible(fila)
                if fila['estado_informe'] in ('revision_requerida', 'error_sin_reintento', 'sin_envio_verificado'):
                    estado = fila['estado_informe']
                    detalle = fila['detalle_informe']
                if estado == 'intento_recordatorio':
                    estado = 'intento incierto: revisar Outlook'
                proximo = datetime.fromtimestamp(fila['proximo'], BOGOTA).strftime('%d/%m %H:%M') if fila['proximo'] and estado == 'esperando_confirmacion' else '—'
                tabla.insert('', 'end', iid=str(fila['id']), values=(
                    datetime.fromtimestamp(fila['creado'], BOGOTA).strftime('%d/%m %H:%M'),
                    fila['asunto'], fila['destinatario'], fila['rol'], etiqueta_estado,
                    fila['intentos'], fila['maximo'], proximo, detalle))
            estado_consulta.set(f'{len(filas)} registros · del {inicio:%d/%m/%Y} al {fin:%d/%m/%Y} · estados guardados en DataSuite')

        def exportar():
            try:
                inicio, fin = validar_fechas(desde_informe.get(), hasta_informe.get())
            except ValueError as error:
                messagebox.showerror('Fechas del informe', str(error), parent=ventana)
                return
            destino = filedialog.asksaveasfilename(parent=ventana,
                title='Guardar informe de confirmaciones de lectura',
                initialdir=str(BASE / 'seguimiento_correos'),
                initialfile=f'CONFIRMACIONES_LECTURA_{inicio:%Y-%m-%d}_al_{fin:%Y-%m-%d}_{datetime.now(BOGOTA):%H%M%S}.xlsx',
                defaultextension='.xlsx', filetypes=[('Libro de Excel', '*.xlsx')],
                confirmoverwrite=True)
            if not destino:
                return
            boton_exportar.configure(state='disabled')
            resultado = queue.Queue()

            def generar():
                try:
                    datos = consultar_informe(inicio, fin)
                    if not datos['registros']:
                        resultado.put(('vacio', 'No hay registros de seguimiento para las fechas seleccionadas. No se creó ningún archivo.'))
                        return
                    archivo = exportar_informe(datos, destino, sobrescribir=True)
                    resultado.put(('ok', str(archivo)))
                except Exception as error:
                    resultado.put(('error', str(error)))

            def terminar():
                if not ventana.winfo_exists():
                    return
                try:
                    tipo, texto = resultado.get_nowait()
                except queue.Empty:
                    ventana.after(150, terminar)
                    return
                boton_exportar.configure(state='normal')
                if tipo == 'error':
                    messagebox.showerror('No se exportó el informe', texto, parent=ventana)
                elif tipo == 'vacio':
                    messagebox.showinfo('Informe de confirmaciones', texto, parent=ventana)
                else:
                    messagebox.showinfo('Informe exportado',
                        'Se guardó el Excel con Resumen diario y Detalle.\n\n' + texto
                        + '\n\nNo se envió ningún correo ni se modificaron los seguimientos.', parent=ventana)

            threading.Thread(target=generar, daemon=True).start()
            ventana.after(150, terminar)

        def detener_seleccionado():
            seleccion = tabla.selection()
            if seleccion and messagebox.askyesno('Cancelar seguimiento', '¿Detener futuros recordatorios del informe seleccionado? Los ya enviados no se retiran.', parent=ventana):
                for identificador in seleccion:
                    cancelar(int(identificador))
                refrescar()

        ttk.Button(ventana, text='Actualizar', command=refrescar).pack(side='left', padx=8, pady=8)
        boton_exportar = ttk.Button(ventana, text='Exportar informe', command=exportar, bootstyle='success')
        boton_exportar.pack(side='left', padx=8, pady=8)
        ttk.Button(ventana, text='Cancelar seleccionado', command=detener_seleccionado).pack(side='left', padx=8)
        refrescar()

    ttk.Button(seguimiento_frame, text='Ver seguimiento', command=ver_seguimiento).grid(
        row=0, column=9, padx=(16, 0), sticky='w')

    def validar_fecha(texto):
        try:
            datetime.strptime(texto.strip(), "%d/%m/%Y")
            return True
        except ValueError:
            return False

    def ejecutar_correo(
        inicial, final, automatico, presentacion, solicitar_lectura, opciones, proyecto, ejecucion
    ):
        try:
            import pythoncom
            from modules.correo_validacion_materiales import (
                cargar_control_exportacion,
                crear_correo_outlook,
                generar_adjuntos_por_hoja,
            )

            pythoncom.CoInitialize()
            try:
                escribir_correo("📂 Verificando el informe y los exportes de la última validación...")
                control = cargar_control_exportacion(proyecto)
                informe = control.copiar_informe_verificado(proyecto, ejecucion)
                escribir_correo(f"📄 Informe: {informe.name}")
                if presentacion == "Separados por hojas":
                    escribir_correo(
                        "📎 Generando archivos separados por hoja..."
                    )
                    adjuntos = generar_adjuntos_por_hoja(informe)
                else:
                    escribir_correo("📎 Adjuntando el libro completo...")
                    adjuntos = [informe]
                escribir_correo(f"✅ Adjuntos preparados: {len(adjuntos)}")
                token = crear_correo_outlook(
                    inicial,
                    final,
                    adjuntos,
                    enviar_automaticamente=automatico,
                    modalidad_adjuntos=presentacion,
                    solicitar_confirmacion_lectura=solicitar_lectura,
                    seguimiento=opciones,
                )
                if token:
                    escribir_correo('Seguimiento registrado: ' + token)
                if automatico:
                    escribir_correo('✅ Envío solicitado a Outlook: 8 destinatarios y 3 CC. No demuestra entrega.')
                else:
                    escribir_correo(
                        "✅ Correo abierto en Outlook para revisión."
                    )
            finally:
                pythoncom.CoUninitialize()
        except Exception as error:
            escribir_correo(f"❌ ERROR: {error}")
            cola_correo.put(lambda detalle=str(error): messagebox.showerror('Error al generar correo', detalle))
        finally:
            cola_correo.put(lambda: boton_correo.configure(state='normal'))

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
        presentacion = modalidad_adjuntos.get()
        solicitar_lectura = confirmar_lectura.get()
        from modules.seguimiento_lectura import validar_opciones
        try:
            opciones = recoger_opciones()
            validar_opciones(opciones['espera'], opciones['intervalo'], opciones['maximo'],
                             opciones['destinatarios'])
            if opciones['activo'] and not solicitar_lectura:
                raise ValueError('Activa la solicitud de confirmación para usar recordatorios.')
            if opciones['activo'] and not opciones['destinatarios']:
                raise ValueError('Seleccione al menos un destinatario de recordatorios.')
            if datetime.strptime(inicial, '%d/%m/%Y') > datetime.strptime(final, '%d/%m/%Y'):
                raise ValueError('La fecha inicial no puede superar la final.')
        except ValueError as error:
            messagebox.showerror('Configuración no válida', str(error))
            return
        try:
            from modules.correo_validacion_materiales import cargar_control_exportacion
            control = cargar_control_exportacion(proyecto_actual)
            informe, datos_control = control.obtener_informe_verificado(proyecto_actual)
            resumen_exportes = control.resumen_control(informe, datos_control)
        except Exception as error:
            messagebox.showerror('No se puede verificar el adjunto', str(error))
            return
        continuar = dialogo_datasuite(
                vista,
                'Confirmar generación de correo',
                (
                    resumen_exportes + '\n\n'
                    + 'Correo inicial: 8 destinatarios principales y 3 CC.\n'
                    + ('Envío automático.\n' if automatico else 'Se abrirá en Outlook: envíalo manualmente sin modificar los destinatarios.\n')
                    + f'Recordatorios: {"Activados" if opciones["activo"] else "Desactivados"}; seleccionados {len(opciones["destinatarios"])}/11.\n'
                    + f'Corte {opciones["corte"]}; espera {opciones["espera"]} min; intervalo {opciones["intervalo"]} min; máximo {opciones["maximo"]}. Hasta las 15:30 (Colombia).\n'
                    + 'Para: ' + '; '.join(DESTINATARIOS) + '\nCC: ' + '; '.join(COPIAS) + '\n'
                    +
                    f"Período: {inicial} al {final}\n"
                    f"Presentación: {presentacion}\n\n"
                    "¿Desea continuar?"
                ),
                confirmar=True,
            )
        if not continuar:
            return

        txt_consola.delete("1.0", "end")
        escribir_correo(
            f"📌 Período del correo: {inicial} al {final}"
        )
        escribir_correo(f"📨 Modo: {modo_correo.get()}")
        escribir_correo(f"📎 Presentación: {presentacion}")
        escribir_correo(
            "📬 Confirmación de lectura: "
            + ("Solicitada" if solicitar_lectura else "No solicitada")
        )
        boton_correo.configure(state="disabled")
        threading.Thread(
            target=ejecutar_correo,
            args=(
                inicial,
                final,
                automatico,
                presentacion,
                solicitar_lectura,
                opciones,
                proyecto_actual,
                datos_control['ejecucion'],
            ),
            daemon=True,
        ).start()

    boton_correo.configure(command=iniciar_correo)