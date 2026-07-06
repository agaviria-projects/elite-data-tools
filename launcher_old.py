import ttkbootstrap as ttk
from PIL import Image, ImageTk

# ==========================================================
# ELITE DATA TOOLS SUITE
# ==========================================================

app = ttk.Window(themename="darkly")

# ==========================================================
# ESTILOS PERSONALIZADOS
# ==========================================================

style = ttk.Style()

style.configure(
    "Gray.TFrame",
    background="#D8D8D8"
)

style.configure(
    "Gray.TLabelframe",
    background="#D8D8D8"
)

style.configure(
    "Gray.TLabelframe.Label",
    background="#D8D8D8",
    foreground="black"
)

# ==========================================================
# CONFIGURACIÓN
# ==========================================================

app.title("ELITE Data Tools")

app.geometry("1300x750")

app.minsize(1200, 700)

app.resizable(True, True)

# ==========================================================
# GRID PRINCIPAL
# ==========================================================

app.columnconfigure(0, weight=0)
app.columnconfigure(1, weight=1)

app.rowconfigure(0, weight=0)
app.rowconfigure(1, weight=1)
app.rowconfigure(2, weight=0)

# ==========================================================
# HEADER
# ==========================================================

header = ttk.Frame(
    app,
    padding=(20,8),
    style="Gray.TFrame"
)

header.grid(
    row=0,
    column=0,
    columnspan=2,
    sticky="ew"
)

header.columnconfigure(0, weight=1)

ttk.Label(
    header,
    text="ELITE DATA TOOLS",
    font=("Segoe UI", 18, "bold"),
    bootstyle="success"
).grid(
    row=0,
    column=0,
    sticky="ew"
)

ttk.Label(
    header,
    text="Enterprise Automation Suite   |   Versión 1.0",
    font=("Segoe UI", 9)
).grid(
    row=0,
    column=1,
    sticky="e"
)

ttk.Separator(header).grid(
    row=1,
    column=0,
    columnspan=2,
    sticky="ew",
    pady=(8, 0)
)

# ==========================================================
# SIDEBAR
# ==========================================================

sidebar = ttk.Frame(
    app,
    width=240,
    padding=30,
    style="Gray.TFrame"
)

sidebar.grid(
    row=1,
    column=0,
    sticky="nsew"
)

sidebar.grid_propagate(False)

ttk.Label(
    sidebar,
    text="ELITE",
    font=("Segoe UI",20,"bold"),
    bootstyle="success"
).pack(anchor="w")

ttk.Label(
    sidebar,
    text="Módulos",
    font=("Segoe UI",9)
).pack(anchor="w", pady=(0,15))

ttk.Separator(sidebar).pack(fill="x", pady=(0,15))

ttk.Frame(
    sidebar,
    height=10
).pack()

ttk.Label(
    sidebar,
    text="🏠  Inicio",
    font=("Segoe UI",11,"bold"),
    bootstyle="success"
).pack(anchor="w", pady=12)

ttk.Label(
    sidebar,
    text="📊  Informe Actas",
    font=("Segoe UI",11)
).pack(anchor="w", pady=12)

ttk.Label(
    sidebar,
    text="📄  Conciliación DRACO",
    font=("Segoe UI",11)
).pack(anchor="w", pady=12)

ttk.Label(
    sidebar,
    text="📍  Control ANS",
    font=("Segoe UI",11)
).pack(anchor="w", pady=12)

ttk.Label(
    sidebar,
    text="📦  Compresor PDF",
    font=("Segoe UI",11)
).pack(anchor="w", pady=12)

ttk.Label(
    sidebar,
    text="🗂  SIGEM",
    font=("Segoe UI",11)
).pack(anchor="w", pady=12)

ttk.Separator(sidebar).pack(
    fill="x",
    pady=25
)

ttk.Label(
    sidebar,
    text="⚙ Configuración",
    font=("Segoe UI",10)
).pack(anchor="w", pady=6)

ttk.Label(
    sidebar,
    text="ℹ Acerca de",
    font=("Segoe UI",10)
).pack(anchor="w")

# ==========================================================
# PANEL CENTRAL
# ==========================================================

panel = ttk.Frame(
    app,
    padding=35,
    style="Gray.TFrame"
)

panel.grid(
    row=1,
    column=1,
    sticky="nsew",
    padx=(10,20),
    pady=(10,20)
)

panel.columnconfigure(0, weight=1)

# ==========================================================
# CONTENEDOR HOME
# ==========================================================

home = ttk.Frame(
    panel,
    style="Gray.TFrame"
)

home.grid(
    row=0,
    column=0,
    sticky="nsew"
)

home.columnconfigure(0, weight=3)
home.columnconfigure(1, weight=1)

# ==========================================================
# PANTALLA DE INICIO
# ==========================================================

ttk.Label(
    home,
    text="👋 Bienvenido",
    font=("Segoe UI", 26, "bold"),
    foreground="black"
).grid(
    row=0,
    column=0,
    sticky="w"
)

ttk.Label(
    home,
    text="Centro de Automatización Empresarial",
    font=("Segoe UI", 16)
).grid(
    row=1,
    column=0,
    sticky="w",
    pady=(5,20)
)

ttk.Label(
    home,
    text=(
        "Centralice desde un único lugar todas las herramientas "
        "desarrolladas para ELITE Ingenieros S.A.S.\n\n"
        "Seleccione un módulo desde el menú lateral para comenzar."
    ),
    wraplength=850,
    justify="left",
    font=("Segoe UI", 11)
).grid(
    row=2,
    column=0,
    sticky="ew",
    pady=(15, 5)
)

ttk.Separator(home).grid(
    row=3,
    column=0,
    sticky="ew",
    pady=30
)

# ==========================================================
# DASHBOARD
# ==========================================================

dashboard = ttk.Frame(
    home,
    padding=(0,10),
    style="Gray.TFrame"
)

dashboard.grid(
    row=4,
    column=0,
    sticky="w",
    pady=(10,0)
)

dashboard.columnconfigure(0, weight=1)
dashboard.columnconfigure(1, weight=1)
dashboard.columnconfigure(2, weight=1)

# -------------------------
# Tarjeta 1
# -------------------------

card1 = ttk.Labelframe(
    dashboard,
    text="Herramientas",
    padding=30,
    bootstyle="success"
)

card1.grid(row=0, column=0, padx=(0,20))

ttk.Label(
    card1,
    text="5",
    font=("Segoe UI",28,"bold"),
    bootstyle="success"
).pack()

ttk.Label(
    card1,
    text="Módulos disponibles"
).pack()

# -------------------------
# Tarjeta 2
# -------------------------

card2 = ttk.Labelframe(
    dashboard,
    text="Estado",
    padding=30,
    bootstyle="info"
)

card2.grid(row=0, column=1, padx=(0,20))

ttk.Label(
    card2,
    text="✔",
    font=("Segoe UI",28,"bold"),
    bootstyle="success"
).pack()

ttk.Label(
    card2,
    text="Sistema listo"
).pack()

# -------------------------
# Tarjeta 3
# -------------------------

card3 = ttk.Labelframe(
    dashboard,
    text="Versión",
    padding=30,
    bootstyle="warning"
)

card3.grid(row=0, column=2)

ttk.Label(
    card3,
    text="1.0",
    font=("Segoe UI",28,"bold"),
    bootstyle="warning"
).pack()

ttk.Label(
    card3,
    text="Enterprise"
).pack()


# ==========================================================
# FOOTER
# ==========================================================

footer = ttk.Frame(
    app,
    padding=(15,8),
    style="Gray.TFrame"
)

footer.grid(
    row=2,
    column=0,
    columnspan=2,
    sticky="ew"
)

footer.columnconfigure(0, weight=1)

ttk.Separator(footer).grid(
    row=0,
    column=0,
    columnspan=2,
    sticky="ew"
)

ttk.Label(
    footer,
    text="Estado: Sistema listo",
    font=("Segoe UI",9)
).grid(
    row=1,
    column=0,
    sticky="w",
    pady=(6,0)
)

ttk.Label(
    footer,
    text="ELITE Ingenieros S.A.S.",
    font=("Segoe UI",9)
).grid(
    row=1,
    column=1,
    sticky="e",
    pady=(6,0)
)

# ==========================================================
# LOGO
# ==========================================================
imagen = Image.open("assets/logo.png")

imagen = imagen.resize((120,120))

logo = ImageTk.PhotoImage(imagen)

logo_label = ttk.Label(
    home,
    image=logo
)

logo_label.image = logo      # Mantener referencia

logo_label.grid(
    row=0,
    column=1,
    rowspan=4,
    padx=(60,20),
    sticky="ne"
)

app.mainloop()