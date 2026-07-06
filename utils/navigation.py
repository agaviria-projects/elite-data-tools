"""
=========================================
Administrador de navegación
=========================================
"""

# Vista actualmente cargada
vista_actual = None


# ==========================================
# LIMPIAR PANEL
# ==========================================

def limpiar_panel(panel):
    """
    Elimina todos los widgets contenidos
    dentro del panel principal.
    """

    for widget in panel.winfo_children():
        widget.destroy()


# ==========================================
# HOME
# ==========================================

def mostrar_home(panel):
    """
    Muestra la pantalla de inicio.
    """

    from ui.home import crear_home

    limpiar_panel(panel)

    crear_home(panel)


# ==========================================
# INFORME ACTAS
# ==========================================

def mostrar_informe_actas(panel):
    """
    Muestra el módulo Informe Actas.
    """

    from modules.informe_actas import crear_informe_actas

    limpiar_panel(panel)

    crear_informe_actas(panel)

# ==========================================
# CONTROL ANS
# ==========================================

def mostrar_control_ans(panel):
    """
    Muestra el módulo Control ANS.
    """

    from modules.control_ans import crear_control_ans

    limpiar_panel(panel)

    crear_control_ans(panel)


# ==========================================
# GENERADOR INFORME ANS
# ==========================================

def mostrar_generador_ans(panel):
    """
    Muestra el módulo Generador Informe ANS.
    """

    from modules.generador_ans import crear_generador_ans

    limpiar_panel(panel)

    crear_generador_ans(panel)

# ==========================================
# VALIDACIÓN MATERIALES
# ==========================================

def mostrar_validacion_materiales(panel):
    """
    Muestra el módulo Validación Materiales.
    """

    from modules.validacion_materiales import crear_validacion_materiales

    limpiar_panel(panel)

    crear_validacion_materiales(panel)    

# ==========================================
# COMPRESOR PDF
# ==========================================

def mostrar_compresor_pdf(panel):
    """
    Muestra el módulo Compresor PDF.
    """

    from modules.compresor_pdf import crear_compresor_pdf

    limpiar_panel(panel)

    crear_compresor_pdf(panel)