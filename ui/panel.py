import ttkbootstrap as ttk


def crear_panel(app):
    """
    Crea el contenedor principal donde se
    cargarán todas las pantallas de la Suite.
    """

    # ==========================================
    # PANEL PRINCIPAL
    # ==========================================

    panel = ttk.Frame(
        app,
        padding=25
    )

    panel.grid(
        row=1,
        column=1,
        sticky="nsew"
    )

    panel.columnconfigure(
        0,
        weight=1
    )

    panel.rowconfigure(
        0,
        weight=1
    )

    return panel