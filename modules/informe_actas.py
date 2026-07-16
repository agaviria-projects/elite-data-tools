# Archivo base de modules/informe_actas.py
# (versión inicial profesional)

import subprocess
import sys
from pathlib import Path
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ui.base_view import crear_vista

import threading

BASE=Path(__file__).resolve().parent.parent
PROYECTO=BASE/"Proyecto_Actas"
proyecto_actual=PROYECTO

def validar_proyecto():
    return {
        "ACTAS_RAW":(proyecto_actual/"ACTAS_RAW").exists(),
        "CONFIG":(proyecto_actual/"CONFIG").exists(),
        "UNIFICADAS":(proyecto_actual/"UNIFICADAS").exists(),
        "CONSOLIDADO":(proyecto_actual/"CONSOLIDADO").exists(),
        "SCRIPT":(proyecto_actual/"consolidar_actas.py").exists(),
    }

def actualizar_estado(frame):
    for w in frame.winfo_children():
        w.destroy()
    for n,e in validar_proyecto().items():
        ttk.Label(frame,text=f'{"🟢" if e else "🔴"} {n}').pack(anchor="w",pady=2)

def cambiar_proyecto(var,frame):
    global proyecto_actual
    p=filedialog.askdirectory(title="Seleccione Proyecto_Actas")
    if not p:return
    proyecto_actual=Path(p)
    var.set(str(proyecto_actual))
    actualizar_estado(frame)

def ejecutar_actas(modo):

    script = proyecto_actual / "consolidar_actas.py"

    if not script.exists():
        messagebox.showerror(
            "Proyecto Actas",
            "No se encontró consolidar_actas.py"
        )
        return

    print("=" * 60)
    print("PYTHON DEL LAUNCHER")
    print(sys.executable)
    print("=" * 60)

    subprocess.Popen(
        [
            "cmd",
            "/c",
            sys.executable,
            str(script),
            "--modo",
            modo.lower()
        ],
        cwd=proyecto_actual,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

def crear_informe_actas(panel):
    vista=crear_vista(panel)
    ttk.Label(vista,text="📊 Informe Actas Fenix",font=("Segoe UI",24,"bold"),bootstyle="success").pack(anchor="w")
    ttk.Label(vista,text="Consolidación automática de las actas.").pack(anchor="w",pady=(0,15))
    cuerpo=ttk.Frame(vista);cuerpo.pack(fill="both",expand=True)
    cuerpo.columnconfigure((0,1),weight=1)
    izq=ttk.Frame(cuerpo);izq.grid(row=0,column=0,sticky="nsew",padx=(0,8))
    der=ttk.Frame(cuerpo);der.grid(row=0,column=1,sticky="nsew",padx=(8,0))
    ruta=ttk.StringVar(value=str(proyecto_actual))
    fp=ttk.Labelframe(izq,text="Proyecto",padding=10);fp.pack(fill="x")
    ttk.Entry(fp,textvariable=ruta,state="readonly").pack(fill="x",pady=(0,8))
    est=ttk.Labelframe(der,text="Estado del Proyecto",padding=10);est.pack(fill="both",expand=True)
    actualizar_estado(est)
    ttk.Button(fp,text="Cambiar carpeta",bootstyle="secondary", cursor="hand2",command=lambda:cambiar_proyecto(ruta,est)).pack(anchor="e")
    fm=ttk.Labelframe(vista,text="Modo de ejecución",padding=18);fm.pack(fill="x",pady=(22,15))
    modo=ttk.StringVar(value="reconstruir")
    ttk.Radiobutton(fm,text="Reconstruir",variable=modo,value="reconstruir",bootstyle="success").pack(anchor="w",pady=(2,6),padx=15)
    ttk.Radiobutton(fm,text="Anexar",variable=modo,value="anexar",bootstyle="success").pack(anchor="w",pady=(0,10),padx=15)
    ttk.Button(fm, text="▶ Generar Informe", bootstyle="success", width=24, cursor="hand2", command=lambda: ejecutar_actas(modo.get())).pack(pady=10)
    lc=ttk.Labelframe(vista,text="Consola",padding=8);lc.pack(fill="both",expand=True)
    t=ttk.Text(lc,height=8);t.pack(fill="both",expand=True)
    t.insert("end","Esperando ejecución...\n")
