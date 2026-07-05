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

