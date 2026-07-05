import ttkbootstrap as ttk

from ui.styles import *


def crear_home(parent):
    """
    Crea la pantalla principal de bienvenida.
    """

    # ==========================================
    # CONTENEDOR PRINCIPAL
    # ==========================================

    home = ttk.Frame(
        parent,
        padding=30
    )

    home.pack(
        fill="both",
        expand=True
    )

    # ==========================================
    # TÍTULO
    # ==========================================

    ttk.Label(
        home,
        text="👋 Bienvenido",
        font=FUENTE_TITULO,
        bootstyle="success"
    ).pack(
        anchor="w"
    )

    ttk.Label(
        home,
        text="Centro de Automatización Empresarial",
        font=FUENTE_SUBTITULO
    ).pack(
        anchor="w",
        pady=(5, 20)
    )

    # ==========================================
    # DESCRIPCIÓN
    # ==========================================

    ttk.Label(
        home,
        text=(
            "Seleccione un módulo desde el menú lateral.\n\n"
            "Desde esta Suite podrá ejecutar todas las herramientas\n"
            "desarrolladas para ELITE Ingenieros S.A.S."
        ),
        justify="left",
        font=FUENTE_NORMAL
    ).pack(
        anchor="w"
    )

    # ==========================================
    # SEPARADOR
    # ==========================================

    ttk.Separator(
        home
    ).pack(
        fill="x",
        pady=30
    )

    return home