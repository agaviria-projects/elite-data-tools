import ttkbootstrap as ttk


def crear_seguimiento_ans(parent):
    """
    Crea la interfaz integrada del módulo
    Generador Informe ANS.
    """

    # ==========================================
    # CONTENEDOR PRINCIPAL
    # ==========================================

    contenedor = ttk.Frame(
        parent,
        padding=30,
    )

    contenedor.pack(
        fill="both",
        expand=True,
    )

    # ==========================================
    # ENCABEZADO
    # ==========================================
    ttk.Label(
        contenedor,
        text="📨 Seguimiento ANS",
        font=("Segoe UI", 22, "bold"),
        bootstyle="success",
    ).pack(
        anchor="w",
    )

    ttk.Label(
        contenedor,
        text=(
            "Generación y revisión de correos "
            "de seguimiento ANS"
        ),
        font=("Segoe UI", 11),
    ).pack(
        anchor="w",
        pady=(5, 20),
    )
        
    # ==========================================
    # PANEL DE INFORMACIÓN
    # ==========================================

    panel_informacion = ttk.Labelframe(
        contenedor,
        text="Información del módulo",
        padding=20,
        bootstyle="secondary",
    )

    panel_informacion.pack(
        fill="x",
        pady=(0, 15),
    )

    ttk.Label(
        panel_informacion,
        text="Nombre:",
        font=("Segoe UI", 10, "bold"),
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=(0, 10),
        pady=5,
    )

    ttk.Label(
        panel_informacion,
        text="Seguimiento ANS",
        font=("Segoe UI", 10),
    ).grid(
        row=0,
        column=1,
        sticky="w",
        pady=5,
    )

    ttk.Label(
        panel_informacion,
        text="Versión:",
        font=("Segoe UI", 10, "bold"),
    ).grid(
        row=1,
        column=0,
        sticky="w",
        padx=(0, 10),
        pady=5,
    )

    ttk.Label(
        panel_informacion,
        text="1.0",
        font=("Segoe UI", 10),
    ).grid(
        row=1,
        column=1,
        sticky="w",
        pady=5,
    )

    ttk.Label(
        panel_informacion,
        text="Estado:",
        font=("Segoe UI", 10, "bold"),
    ).grid(
        row=2,
        column=0,
        sticky="w",
        padx=(0, 10),
        pady=5,
    )

    ttk.Label(
        panel_informacion,
        text="● Sistema listo",
        font=("Segoe UI", 10, "bold"),
        bootstyle="success",
    ).grid(
        row=2,
        column=1,
        sticky="w",
        pady=5,
    )

    # ==========================================
    # MENSAJE TEMPORAL
    # ==========================================

    ttk.Label(
        contenedor,
        text=(
            "El módulo Seguimiento ANS fue cargado "
            "correctamente dentro de DataSuite."
        ),
        font=("Segoe UI", 11),
        bootstyle="secondary",
    ).pack(
        anchor="w",
        pady=20,
    )