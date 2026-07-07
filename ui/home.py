import ttkbootstrap as ttk

from PIL import Image, ImageTk

from pathlib import Path

from ui.styles import *

BASE = Path(__file__).resolve().parent.parent

RUTA_LOGO = BASE / "assets" / "fondo_elite.png"

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
            "ELITE DATA TOOLS es la plataforma corporativa desarrollada para "
            "ELITE Ingenieros S.A.S., diseñada para centralizar herramientas "
            "de automatización, procesamiento de datos, generación de informes "
            "y optimización de procesos empresariales desde un único entorno.\n\n"
        ),
        wraplength=950,
        justify="left",
        font=FUENTE_NORMAL
    ).pack(
        anchor="w",
        pady=(10, 0)
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
    # ==========================================
    # LOGO ELITE
    # ==========================================

    imagen = Image.open(RUTA_LOGO)

    ancho_max = 650
    alto_max = 220

    imagen.thumbnail((ancho_max, alto_max), Image.LANCZOS)

    logo = ImageTk.PhotoImage(imagen)

    logo = ImageTk.PhotoImage(imagen)

    lbl_logo = ttk.Label(
        home,
        image=logo
    )

    # Evita que Python elimine la imagen de memoria
    lbl_logo.image = logo

    lbl_logo.pack(
        pady=(15, 20)
    )