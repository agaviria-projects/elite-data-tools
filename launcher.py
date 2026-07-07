import ttkbootstrap as ttk

from pathlib import Path

from ui.styles import *
from ui.header import crear_header
from ui.sidebar import crear_sidebar
from ui.panel import crear_panel
from ui.footer import crear_footer
from utils.navigation import mostrar_home


BASE = Path(__file__).resolve().parent

ICONO = BASE / "assets" / "LOGO.ico"

# ==========================================
# VENTANA PRINCIPAL
# ==========================================

app = ttk.Window(
    themename="darkly"
)

app.title("ELITE Data Tools")

app.iconbitmap(str(ICONO))

app.geometry("1300x750")

app.state("zoomed")

app.minsize(1200,700)

app.resizable(True,True)

# ==========================================
# GRID PRINCIPAL
# ==========================================

app.columnconfigure(0,weight=0)

app.columnconfigure(1,weight=1)

app.rowconfigure(0,weight=0)

app.rowconfigure(1,weight=1)

app.rowconfigure(2,weight=0)

# ==========================================
crear_header(app)

panel = crear_panel(app)

crear_sidebar(app, panel)

mostrar_home(panel)

crear_footer(app)

app.mainloop()