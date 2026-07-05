import ttkbootstrap as ttk


def crear_vista(panel):
    """
    Limpia el panel principal y crea un
    contenedor para el módulo.
    """

    for widget in panel.winfo_children():
        widget.destroy()

    vista = ttk.Frame(panel)

    vista.pack(
        fill="both",
        expand=True
    )

    return vista