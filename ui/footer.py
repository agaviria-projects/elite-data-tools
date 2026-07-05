import ttkbootstrap as ttk

from ui.styles import *


def crear_footer(app):
    """
    Crea la barra inferior de la aplicación.
    """

    # ==========================================
    # FOOTER
    # ==========================================

    footer = ttk.Frame(
        app,
        padding=(15, 8)
    )

    footer.grid(
        row=2,
        column=0,
        columnspan=2,
        sticky="ew"
    )

    footer.columnconfigure(
        0,
        weight=1
    )

    # ==========================================
    # SEPARADOR
    # ==========================================

    ttk.Separator(
        footer
    ).grid(
        row=0,
        column=0,
        columnspan=2,
        sticky="ew"
    )

    # ==========================================
    # ESTADO
    # ==========================================

    ttk.Label(
        footer,
        text="🟢 Sistema listo",
        font=FUENTE_PEQUEÑA
    ).grid(
        row=1,
        column=0,
        sticky="w",
        pady=(6, 0)
    )

    # ==========================================
    # EMPRESA
    # ==========================================

    ttk.Label(
        footer,
        text="ELITE Ingenieros S.A.S.",
        font=FUENTE_PEQUEÑA
    ).grid(
        row=1,
        column=1,
        sticky="e",
        pady=(6, 0)
    )

    return footer