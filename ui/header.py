import ttkbootstrap as ttk
from ui.styles import *
def crear_header(app):

    # =====================================
    # HEADER
    # =====================================

    header = ttk.Frame(
        app,
        padding=(20, 10)
    )

    header.grid(
        row=0,
        column=0,
        columnspan=2,
        sticky="ew"
    )

    header.columnconfigure(0, weight=1)

    # -------------------------------------

    ttk.Label(
        header,
        text="ELITE DATA TOOLS",
        font=FUENTE_TITULO,
        bootstyle="success"
    ).grid(
        row=0,
        column=0,
        sticky="w"
    )

    ttk.Label(
        header,
        text="Enterprise Automation Suite  |  Versión 1.0",
        font=FUENTE_PEQUEÑA
    ).grid(
        row=0,
        column=1,
        sticky="e"
    )

    ttk.Separator(
        header
    ).grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(8, 0)
    )

    return header