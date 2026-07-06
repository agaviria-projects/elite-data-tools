"""
------------------------------------------------------------
PANEL DE CONTROL ANS – ELITE Ingenieros S.A.S.
------------------------------------------------------------
Autor: Héctor A. Gaviria + IA (2025)
------------------------------------------------------------
"""

import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox as mbox
from PIL import Image, ImageTk
import sys
import io
from datetime import datetime
from modules.calendario_ans import abrir_calendario

# ------------------------------------------------------------
# CONFIGURACIÓN UTF-8 GLOBAL
# ------------------------------------------------------------
if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding is None or sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ------------------------------------------------------------
# RUTA DE ARCHIVOS
# ------------------------------------------------------------
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RUTA_LOGO = BASE_DIR / "assets" / "logo.png"
RUTA_SCRIPT_ANS = r"calculos_ans.py"
RUTA_SCRIPT_LIMPIEZA = r"limpieza_fenix.py"
RUTA_SCRIPT_MERGE = r"merge_fenix_actas.py"
RUTA_MAPA = r"data_output/mapa_ans.html"
RUTA_DASHBOARD = BASE_DIR /"dashboard"/"Dashboard.xlsm"
RUTA_SCRIPT_ANS_EPM = r"calculos_ans_epm.py"
RUTA_ICONO_ENRUTAMIENTO = BASE_DIR / "assets" / "enrutamiento.png"
RUTA_ROUTING_APP_DIR = BASE_DIR / "routing_app"
RUTA_STREAMLIT_APP = RUTA_ROUTING_APP_DIR / "app.py"

# ============================================================
# ANIMACIÓN HOVER (ELEGANTE Y SEGURA)
# ============================================================
def aplicar_hover(boton, color_hover="#2ECC71"):
    color_normal = boton.cget("bg")

    def entrar(event):
        boton.config(bg=color_hover)

    def salir(event):
        boton.config(bg=color_normal)

    boton.bind("<Enter>", entrar)
    boton.bind("<Leave>", salir)

# ------------------------------------------------------------
# TOOLTIP SIMPLE (Tkinter)
# ------------------------------------------------------------
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None

        widget.bind("<Enter>", self.mostrar)
        widget.bind("<Leave>", self.ocultar)

    def mostrar(self, event=None):
        if self.tipwindow or not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() - 10

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # sin bordes
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#333333",
            foreground="white",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 9)
        )
        label.pack(ipadx=6, ipady=3)

    def ocultar(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


# ------------------------------------------------------------
# FUNCIONES DE INTERFAZ
# ------------------------------------------------------------
def resaltar_boton(boton):
    color_original = boton.cget("bg")
    boton.config(bg="#27AE60")
    ventana.update_idletasks()
    return color_original

def restaurar_boton(boton, color_original):
    boton.config(bg=color_original)
    ventana.update_idletasks()

# ------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE EJECUCIÓN
# ------------------------------------------------------------
def ejecutar_comando(nombre, comando, boton=None):
    def tarea():
        log_text.insert(tk.END, f"\n🚀 Iniciando {nombre}...\n", "info")
        log_text.see(tk.END)

        barra_progreso["value"] = 0
        ventana.update_idletasks()

        hora = datetime.now().strftime("%I:%M %p")
        pie_estado.config(text=f"🔄 Procesando {nombre}... | {hora}", fg="#1A5276")
        ventana.update_idletasks()

        color_original = resaltar_boton(boton) if boton else None

        try:
            barra_progreso.config(mode="indeterminate")
            barra_progreso.start(20)

            proceso = subprocess.Popen(
                comando,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                encoding="utf-8"
            )

            for linea in iter(proceso.stdout.readline, ''):
                log_text.insert(tk.END, linea)
                log_text.see(tk.END)
                ventana.update_idletasks()

            proceso.wait()

            barra_progreso.stop()
            barra_progreso.config(mode="determinate")

            if proceso.returncode == 0:
                barra_progreso["value"] = 100
                ventana.update_idletasks()
                log_text.insert(tk.END, f"\n✅ {nombre} completado con éxito.\n", "success")
                pie_estado.config(text=f"✅ {nombre} completado con éxito. | {hora}", fg="#27AE60")
            else:
                log_text.insert(tk.END, f"\n❌ Error en {nombre} (código {proceso.returncode}).\n", "error")
                pie_estado.config(text=f"⚠️ Error en {nombre}. Revisa el log.", fg="#C0392B")

        except Exception as e:
            barra_progreso.stop()
            barra_progreso.config(mode="determinate", value=100)
            log_text.insert(tk.END, f"\n⚠️ Error inesperado: {e}\n", "error")
            pie_estado.config(text=f"⚠️ Error inesperado", fg="#C0392B")

        finally:
            if boton and color_original:
                restaurar_boton(boton, color_original)
            log_text.insert(tk.END, "-" * 60 + "\n", "separador")
            log_text.see(tk.END)
            pie_estado.config(text="⚙️ Esperando acción del usuario...", fg="#1B263B")
            ventana.update_idletasks()
            ventana.after(1500, lambda: barra_progreso.config(value=0))

    threading.Thread(target=tarea, daemon=True).start()
# ------------------------------------------------------------
# FUNCIÓN: EJECUTAR ACTAS (merge_fenix_actas.py)
# ------------------------------------------------------------
def ejecutar_actas():
    def tarea():
        try:
            log_text.insert(tk.END, "\n📁 Ejecutando cruce Fénix vs ACTAS...\n", "info")
            log_text.see(tk.END)

            hora = datetime.now().strftime("%I:%M %p")
            pie_estado.config(text=f"📁 Ejecutando ACTAS... | {hora}", fg="#7D6608")
            ventana.update_idletasks()

            barra_progreso.config(mode="indeterminate")
            barra_progreso.start(20)

            proceso = subprocess.Popen(
                [sys.executable, "-X", "utf8", RUTA_SCRIPT_MERGE],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8"
            )

            for linea in iter(proceso.stdout.readline, ''):
                log_text.insert(tk.END, linea)
                log_text.see(tk.END)
                ventana.update_idletasks()

            proceso.wait()

            barra_progreso.stop()
            barra_progreso.config(mode="determinate", value=100)

            if proceso.returncode == 0:
                log_text.insert(tk.END, "\n✅ ACTAS ejecutado correctamente.\n", "success")
                pie_estado.config(text=f"✅ ACTAS OK | {hora}", fg="#1E8449")
            else:
                log_text.insert(tk.END, "\n❌ Error ejecutando ACTAS.\n", "error")
                pie_estado.config(text="⚠️ Error en ACTAS", fg="#C0392B")

        except Exception as e:
            log_text.insert(tk.END, f"\n⚠️ Error ACTAS: {e}\n", "error")
            pie_estado.config(text="⚠️ Error inesperado ACTAS", fg="#C0392B")

        finally:
            ventana.after(1500, lambda: barra_progreso.config(value=0))
            log_text.insert(tk.END, "-" * 60 + "\n", "separador")
            log_text.see(tk.END)

        ventana.after(3000, lambda: pie_estado.config(
        text="⚙️ Esperando acción del usuario...",
        fg="#1B263B"
        ))   

    threading.Thread(target=tarea, daemon=True).start()

# ------------------------------------------------------------
# FUNCIÓN: CONTROL ANS EPM (DISCRETO)
# ------------------------------------------------------------
def ejecutar_control_ans_epm():
    comando = f'python -X utf8 "{RUTA_SCRIPT_ANS_EPM}"'
    ejecutar_comando("Control ANS EPM", comando)

# ------------------------------------------------------------
# FUNCIÓN EJECUTAR INFORME COMPLETO
# ------------------------------------------------------------
def ejecutar_informe():
    def tarea():
        color_original = None
        try:
            log_text.insert(tk.END, "\n🚀 Iniciando proceso completo Informe ANS...\n", "info")
            log_text.see(tk.END)
            ventana.update_idletasks()

            color_original = resaltar_boton(btn_informe)
            barra_progreso.config(mode="indeterminate")
            barra_progreso.start(20)

            python_exe = sys.executable
            base_dir = os.path.dirname(os.path.abspath(__file__))

            ruta_limpieza = os.path.join(base_dir, RUTA_SCRIPT_LIMPIEZA)
            ruta_calculos = os.path.join(base_dir, RUTA_SCRIPT_ANS)
            ruta_digitacion = os.path.join(base_dir, "cruce_digitacion_fenix.py")
            ruta_merge = os.path.join(base_dir, "merge_fenix_actas.py")

            def run_and_stream(args, titulo):
                log_text.insert(tk.END, f"\n▶ {titulo}\n", "info")
                log_text.see(tk.END)

                p = subprocess.Popen(
                    args,
                    cwd=base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8"
                )
                for l in iter(p.stdout.readline, ''):
                    log_text.insert(tk.END, l)
                    log_text.see(tk.END)
                    ventana.update_idletasks()

                p.wait()
                if p.returncode != 0:
                    log_text.insert(tk.END, f"\n❌ Falló: {titulo} (código {p.returncode})\n", "error")
                    raise RuntimeError(f"Falló {titulo} (code {p.returncode})")

                log_text.insert(tk.END, f"\n✅ OK: {titulo}\n", "success")
                return True

            # ---- 1) LIMPIEZA ----
            run_and_stream([python_exe, "-X", "utf8", ruta_limpieza], "Limpieza Fénix (limpieza_fenix.py)")

            # ---- 2) CÁLCULOS ----
            run_and_stream([python_exe, "-X", "utf8", ruta_calculos], "Cálculos ANS (calculos_ans.py)")

            # ---- 2.5) CRUCE DIGITACIÓN FÉNIX ----
            run_and_stream([python_exe, "-X", "utf8", ruta_digitacion], "Cruce Digitación Fénix (cruce_digitacion_fenix.py)")

            # ---- 3) MERGE (SOLO SI EXISTE LIQUIDACIÓN/ACTAS) ----
            data_raw_dir = os.path.join(base_dir, "data_raw")

            # Ajusta el patrón si tu archivo tiene otro nombre fijo
            hay_liquidacion = False
            if os.path.isdir(data_raw_dir):
                for f in os.listdir(data_raw_dir):
                    fn = f.lower()
                    if fn.startswith("liquidacion_acta") and fn.endswith(".txt"):
                        hay_liquidacion = True
                        break

            if not hay_liquidacion:
                log_text.insert(
                    tk.END,
                    "\n⚠️ Se omite MERGE (merge_fenix_actas.py): no se encontró Liquidacion_Acta_*.txt en data_raw.\n",
                    "info"
                )
                log_text.see(tk.END)
            else:
                run_and_stream([python_exe, "-X", "utf8", ruta_merge], "Cruce Programación vs Actas (merge_fenix_actas.py)")

            # ---- 4) GENERAR MAPA ANS ----
            log_text.insert(tk.END, "\n🌎 Generando Mapa ANS...\n", "info")
            log_text.see(tk.END)

            if generar_mapa():
                log_text.insert(tk.END, "   ✔ Mapa ANS generado correctamente.\n", "success")
            else:
                log_text.insert(tk.END, "   ❌ Hubo un error al generar el mapa ANS.\n", "error")

            log_text.insert(tk.END, "\n✅ Informe completado.\n", "success")
            mbox.showinfo("Control ANS", "Informe ANS generado correctamente.")

        except Exception as e:
            log_text.insert(tk.END, f"\n⚠️ Proceso detenido: {e}\n", "error")
            mbox.showerror("Control ANS", f"Proceso detenido:\n{e}")

        finally:
            barra_progreso.stop()
            if color_original is not None:
                restaurar_boton(btn_informe, color_original)

    threading.Thread(target=tarea, daemon=True).start()

def generar_mapa():
    """Genera el mapa ANS antes de abrirlo"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_script = os.path.join(base_dir, "mapa_ans.py")

        if not os.path.exists(ruta_script):
            mbox.showerror("Mapa ANS", "❌ No se encontró mapa_ans.py")
            return False

        proceso = subprocess.Popen(
            [sys.executable, "-X", "utf8", ruta_script],
            cwd=base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8"
        )

        for linea in iter(proceso.stdout.readline, ''):
            log_text.insert(tk.END, linea)
            log_text.see(tk.END)

        proceso.wait()
        return proceso.returncode == 0

    except Exception as e:
        mbox.showerror("Mapa ANS", f"Error al generar el mapa: {e}")
        return False


# ------------------------------------------------------------
# FUNCIÓN: ABRIR MAPA
# ------------------------------------------------------------
def abrir_mapa():
    """Genera el mapa ANS y lo abre actualizado"""
    try:
        log_text.insert(tk.END, "\n🔄 Generando VISOR GEOGRÁFICO ANS...\n", "info")
        log_text.see(tk.END)

        ok = generar_mapa()

        if not ok:
            mbox.showerror("Mapa ANS", "❌ Error generando mapa ANS.")
            return

        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), RUTA_MAPA)

        if not os.path.exists(ruta):
            mbox.showerror("Mapa ANS", "❌ No se generó mapa_ans.html")
            return

        os.startfile(ruta)
        log_text.insert(tk.END, "🗺️ Mapa actualizado y abierto correctamente.\n", "success")

    except Exception as e:
        mbox.showerror("Error", f"No se pudo abrir el mapa: {e}")
# ------------------------------------------------------------
# FUNCIÓN: ABRIR DASHBOARD EXCEL
# ------------------------------------------------------------
def abrir_dashboard():
    try:
        if not RUTA_DASHBOARD.exists():
            mbox.showerror(
                "Dashboard no encontrado",
                f"No se encontró el Dashboard en:\n{RUTA_DASHBOARD}"
            )
            return

        os.startfile(RUTA_DASHBOARD)

        log_text.insert(tk.END, "📊 Dashboard abierto correctamente.\n", "success")
        log_text.see(tk.END)

    except Exception as e:
        mbox.showerror("Error", f"No se pudo abrir el Dashboard:\n{e}")
def abrir_routing_streamlit():
    try:
        if not RUTA_STREAMLIT_APP.exists():
            mbox.showerror("Enrutamiento", f"No se encontró:\n{RUTA_STREAMLIT_APP}")
            return

        # Ejecuta streamlit usando el python del venv actual
        cmd = [sys.executable, "-m", "streamlit", "run", str(RUTA_STREAMLIT_APP), "--server.headless", "true"]

        # Levanta el proceso sin bloquear la UI
        subprocess.Popen(
            cmd,
            cwd=str(RUTA_ROUTING_APP_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
        )

        # Abre el navegador (espera breve para que streamlit arranque)
        ventana.after(1200, lambda: os.startfile("http://localhost:8501"))

        log_text.insert(tk.END, "🧭 Enrutamiento: Streamlit iniciado (localhost:8501)\n", "success")
        log_text.see(tk.END)

    except Exception as e:
        mbox.showerror("Enrutamiento", f"No se pudo iniciar Streamlit:\n{e}")

# ------------------------------------------------------------
# INTERFAZ PRINCIPAL
# ------------------------------------------------------------
ventana = tk.Tk()
ventana.title("Control ANS - ELITE Ingenieros S.A.S.")
ventana.config(bg="#EAEDED")

# ------------------------------------------------------------
# BARRA SUPERIOR
# ------------------------------------------------------------
frame_topbar = tk.Frame(ventana, bg="#1E8449", height=22)
frame_topbar.pack(fill="x")

reloj_top = tk.Label(frame_topbar, font=("Segoe UI", 9, "bold"),
                     fg="white", bg="#1E8449", anchor="e")
reloj_top.pack(side="right", padx=15)

def actualizar_hora_top():
    reloj_top.config(text=datetime.now().strftime("%I:%M:%S %p"))
    ventana.after(1000, actualizar_hora_top)

actualizar_hora_top()

# ------------------------------------------------------------
# TAMAÑO VENTANA
# ------------------------------------------------------------
screen_w = ventana.winfo_screenwidth()
screen_h = ventana.winfo_screenheight()
ancho = int(screen_w * 0.55)
alto = int(screen_h * 0.88)
x = (screen_w // 2) - (ancho // 2)
y = (screen_h // 2) - (alto // 2)
ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
ventana.resizable(False, False)

# ------------------------------------------------------------
# # ENCABEZADO
# # ------------------------------------------------------------
# frame_banner = tk.Frame(ventana, bg="#EAEDED", height=120)
# frame_banner.pack(fill="x")

# frame_superior = tk.Frame(frame_banner, bg="#EAEDED")
# frame_superior.pack(pady=(10, 0))

# try:
#     logo_img = Image.open(RUTA_LOGO)
#     logo_img = logo_img.resize((70, 70), Image.Resampling.LANCZOS)
#     logo = ImageTk.PhotoImage(logo_img)
#     tk.Label(frame_superior, image=logo, bg="#EAEDED").pack(side="left", padx=15)
# except:
#     tk.Label(frame_superior, text="[Logo no encontrado]", bg="#EAEDED").pack(side="left", padx=15)

# tk.Label(frame_superior, text="ELITE ", font=("Segoe UI", 18, "bold"),
#          fg="black", bg="#EAEDED").pack(side="left")
# tk.Label(frame_superior, text="Ingenieros S.A.S.", font=("Segoe UI", 18, "bold"),
#          fg="#1E8449", bg="#EAEDED").pack(side="left")

# tk.Label(frame_banner, text="Control ANS", font=("Segoe UI", 14, "bold"),
#          fg="#1B263B", bg="#EAEDED").pack(pady=(0, 10))
# ------------------------------------------------------------
# ENCABEZADO (Versión elegante v4 mejorada)
# ------------------------------------------------------------
frame_banner = tk.Frame(ventana, bg="#EAEDED", height=110)
frame_banner.pack(fill="x")

frame_superior = tk.Frame(frame_banner, bg="#EAEDED")
frame_superior.pack(pady=(5, 0))

try:
    # Logo más pequeño y centrado
    logo_img = Image.open(RUTA_LOGO)
    logo_img = logo_img.resize((70, 70), Image.Resampling.LANCZOS)  # 👈 tamaño ajustado
    logo = ImageTk.PhotoImage(logo_img)

    tk.Label(frame_superior, image=logo, bg="#EAEDED").pack(side="left", padx=15)
except:
    tk.Label(frame_superior, text="[Logo no encontrado]", bg="#EAEDED").pack(side="left", padx=10)

# Nombre de la empresa más alineado
tk.Label(frame_superior,
         text="ELITE ",
         font=("Segoe UI", 20, "bold"),
         fg="#000000",
         bg="#EAEDED").pack(side="left")

tk.Label(frame_superior,
         text="Ingenieros S.A.S.",
         font=("Segoe UI", 20, "bold"),
         fg="#000000",
         bg="#EAEDED").pack(side="left")

# Subtítulo centrado
tk.Label(frame_banner,
         text="Control ANS",
         font=("Segoe UI", 16, "bold"),
         fg="#145A32",
         bg="#EAEDED").pack(pady=(0, 5))

from tkinter import ttk

ttk.Separator(ventana, orient="horizontal").pack(fill="x", pady=(0, 5))

# ------------------------------------------------------------
# BOTONES PRINCIPALES
# ------------------------------------------------------------
frame_botones = tk.Frame(ventana, bg="#EAEDED")
frame_botones.pack(pady=5, fill="x")
frame_botones.columnconfigure((0, 1, 2, 3), weight=1)

# ---- EJECUTAR INFORME ----
btn_informe = tk.Button(
    frame_botones,
    text="GENERAR\nINFORME ANS",
    command=ejecutar_informe,
    width=20, height=2,
    bg="#1E8449", fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="ridge", borderwidth=3,
    cursor="hand2"
)           
btn_informe.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
aplicar_hover(btn_informe)

# ---- CONTROL ALMACÉN ----
RUTA_SCRIPT_VALIDACION = r"validar_export_almacen.py"

def ejecutar_validacion():
    comando = f'python -X utf8 "{RUTA_SCRIPT_VALIDACION}"'
    ejecutar_comando("Control Almacén ANS", comando, btn_validar)

btn_validar = tk.Button(
    frame_botones,
    text="VALIDACIÓN\nMANO DE OBRA Vs MATERIALES",
    command=ejecutar_validacion,
    width=28, height=2,
    bg="#1E8449", fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="ridge", borderwidth=3,
    cursor="hand2"   # 👈 AQUÍ
)

btn_validar.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
aplicar_hover(btn_validar)

# ---- DESCARGAR EVIDENCIAS ----
RUTA_SCRIPT_COMPRESOR = r"C:\Users\hector.gaviria\Desktop\PDF_ZIP\zip.py"

def ejecutar_compresor_pdf():
    comando = f'python -X utf8 "{RUTA_SCRIPT_COMPRESOR}"'
    ejecutar_comando(
        "Compresor PDF",
        comando,
         btn_compresor_pdf
    )

# def ejecutar_descarga_drive():
#     comando = f'python -X utf8 "{RUTA_SCRIPT_DESCARGA}"'
#     ejecutar_comando("Selector de fecha para Evidencias Drive", comando, btn_descarga_drive)


# btn_descarga_drive = tk.Button(
#     frame_botones,
#     text="DESCARGAR\nEVIDENCIAS DRIVE",
#     command=ejecutar_descarga_drive,
btn_compresor_pdf = tk.Button(
    frame_botones,
    text="COMPRESOR\nPDF",
    command=ejecutar_compresor_pdf,
    width=20, height=2,
    bg="#1E8449", fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="ridge", borderwidth=3,
    cursor="hand2"   
)

btn_compresor_pdf.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
aplicar_hover(btn_compresor_pdf)

# ---- PAPELERA API ----
RUTA_SCRIPT_PAPELERA = r"descargar_evidencias_drive.py"

def ejecutar_papelera_drive():
    comando = f'python -X utf8 "{RUTA_SCRIPT_PAPELERA}"'
    ejecutar_comando("Mover Evidencias a PAPELERA_API", comando, btn_papelera_drive)

btn_papelera_drive = tk.Button(
    frame_botones,
    text="MOVER A\nPAPELERA API",
    command=ejecutar_papelera_drive,
    width=20, height=2,
    bg="#1E8449", fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="ridge", borderwidth=3,
    cursor="hand2"   
)
                               
btn_papelera_drive.grid(row=0, column=3, padx=10, pady=5, sticky="ew")
aplicar_hover(btn_papelera_drive, "#E74C3C")

# ------------------------------------------------------------
# BOTÓN VISOR GEOGRÁFICO (ahora igual a los demás)
# ------------------------------------------------------------
frame_visor = tk.Frame(ventana, bg="#EAEDED")
frame_visor.pack(pady=(5, 10))

btn_visor = tk.Button(
    frame_visor,
    text="VISOR GEOGRÁFICO ANS",
    width=20, height=2,                # 👈 MISMO TAMAÑO QUE LOS OTROS
    bg="#1E8449", fg="white",      
    font=("Segoe UI", 10, "bold"),     # 👈 MISMA FUENTE
    relief="ridge", borderwidth=3,
    cursor="hand2",
    command=abrir_mapa
)

btn_visor.pack()
aplicar_hover(btn_visor, "#1F618D")     # 👈 Hover azul claro


# ------------------------------------------------------------
# BARRA PROGRESO
# ------------------------------------------------------------
barra_progreso = ttk.Progressbar(ventana, orient="horizontal",
                                 mode="determinate", length=450, maximum=100)
barra_progreso.pack(pady=(5, 5))

# ------------------------------------------------------------
# ÁREA LOG
# ------------------------------------------------------------
frame_log = tk.Frame(ventana, bg="#EAEDED")
frame_log.pack(fill="both", expand=False, pady=(5, 0))

log_text = scrolledtext.ScrolledText(frame_log, width=90, height=10,
                                     bg="white", font=("Consolas", 9))
log_text.pack(padx=15, pady=(5, 10), expand=True, fill="both")

log_text.tag_config("info", foreground="#2980B9")
log_text.tag_config("success", foreground="#27AE60")
log_text.tag_config("error", foreground="#C0392B")
log_text.tag_config("separador", foreground="#95A5A6")

# ------------------------------------------------------------
# BOTÓN SALIR
# ------------------------------------------------------------
frame_salida = tk.Frame(ventana, bg="#EAEDED")
frame_salida.pack(pady=(0, 10))

btn_salir = tk.Button(
    frame_salida,
    text="SALIR DEL PANEL",
    command=ventana.quit,
    width=25, height=2,
    bg="#1E8449", fg="white",
    font=("Segoe UI", 10, "bold"),
    relief="ridge", borderwidth=3,
    cursor="hand2"   
)

btn_salir.pack()
aplicar_hover(btn_salir)

# ------------------------------------------------------------
# PIE DE PÁGINA
# ------------------------------------------------------------
frame_footer = tk.Frame(ventana, bg="#EAEDED")
frame_footer.pack(side="bottom", fill="x", pady=(10, 15), ipady=10)

tk.Frame(frame_footer, bg="#B3B6B7", height=4).pack(fill="x", pady=(5, 8))

frame_pie = tk.Frame(frame_footer, bg="#EAEDED")
frame_pie.pack(fill="x", pady=(5, 5))

pie_estado = tk.Label(frame_pie,
                      text="⚙️ Esperando acción del usuario...",
                      font=("Segoe UI", 9, "italic"),
                      fg="#1B263B", bg="#EAEDED")
pie_estado.pack(side="left", padx=(15, 0))

pie_corporativo = tk.Label(frame_pie,
    text="© 2025 ELITE Ingenieros S.A.S.  |  Pasión por lo que hacemos.",
    font=("Segoe UI", 9, "italic"), fg="#1B263B", bg="#EAEDED")
pie_corporativo.pack(side="right", padx=(0, 15))

# ------------------------------------------------------------
# ICONO PEQUEÑO DEL CALENDARIO  
# ------------------------------------------------------------
try:
    icono_cal_img = Image.open(BASE_DIR / "assets" / "calendario.png")
    icono_cal_img = icono_cal_img.resize((42, 42), Image.Resampling.LANCZOS)
    icono_cal = ImageTk.PhotoImage(icono_cal_img)

    lbl_calendario = tk.Label(
        ventana,
        image=icono_cal,
        bg="#EAEDED",
        cursor="hand2"
    )
    lbl_calendario.image = icono_cal

    ToolTip(lbl_calendario, "Calendario")

    # esquina inferior derecha
    lbl_calendario.place(relx=0.45, rely=0.90)

    lbl_calendario.bind("<Button-1>", lambda e: abrir_calendario())

except Exception as e:
    print("⚠ Error cargando icono calendario:", e)
# # ------------------------------------------------------------
# # ICONO ACTAS
# # ------------------------------------------------------------
# try:
#     icono_actas_img = Image.open(BASE_DIR / "assets" / "actas.png")
#     icono_actas_img = icono_actas_img.resize((42, 42), Image.Resampling.LANCZOS)
#     icono_actas = ImageTk.PhotoImage(icono_actas_img)

#     lbl_actas = tk.Label(
#         ventana,
#         image=icono_actas,
#         bg="#EAEDED",
#         cursor="hand2"
#     )
#     lbl_actas.image = icono_actas

#     ToolTip(lbl_actas, "Cruce Fénix vs Actas")

#     # posición: a la derecha del calendario
#     lbl_actas.place(relx=0.12, rely=0.79)

#     lbl_actas.bind("<Button-1>", lambda e: ejecutar_actas())

# except Exception as e:
#     print("⚠ Error cargando icono ACTAS:", e)

# ------------------------------------------------------------
# ICONO DASHBOARD
# ------------------------------------------------------------
try:
    icono_dash_img = Image.open(BASE_DIR / "assets" / "panel.png")
    icono_dash_img = icono_dash_img.resize((42, 42), Image.Resampling.LANCZOS)
    icono_dash = ImageTk.PhotoImage(icono_dash_img)

    lbl_dashboard = tk.Label(
        ventana,
        image=icono_dash,
        bg="#EAEDED",
        cursor="hand2"
    )
    lbl_dashboard.image = icono_dash

    ToolTip(lbl_dashboard, "Dashboard ANS")

    # posición: a la izquierda del icono ACTAS
    lbl_dashboard.place(relx=0.02, rely=0.79)

    lbl_dashboard.bind("<Button-1>", lambda e: abrir_dashboard())

except Exception as e:
    print("⚠ Error cargando icono DASHBOARD:", e)

# ------------------------------------------------------------
# ICONO CONTROL ANS EPM (DISCRETO)
# ------------------------------------------------------------
try:
    icono_epm_img = Image.open(BASE_DIR / "assets" / "ans_epm.png")
    icono_epm_img = icono_epm_img.resize((42, 42), Image.Resampling.LANCZOS)
    icono_epm = ImageTk.PhotoImage(icono_epm_img)

    lbl_epm = tk.Label(
        ventana,
        image=icono_epm,
        bg="#EAEDED",
        cursor="hand2"
    )
    lbl_epm.image = icono_epm

    ToolTip(lbl_epm, "Control ANS EPM")

    # 👉 POSICIÓN EXACTA (donde estaba la X roja)
    lbl_epm.place(relx=0.12, rely=0.78)

    lbl_epm.bind("<Button-1>", lambda e: ejecutar_control_ans_epm())

except Exception as e:
    print("⚠ Error cargando icono Control ANS EPM:", e)

# ------------------------------------------------------------
# ICONO ENRUTAMIENTO (NUEVO)
# ------------------------------------------------------------
try:
    icono_enru_img = Image.open(RUTA_ICONO_ENRUTAMIENTO)
    icono_enru_img = icono_enru_img.resize((80, 60), Image.Resampling.LANCZOS)
    icono_enru = ImageTk.PhotoImage(icono_enru_img)

    lbl_enrutamiento = tk.Label(
        ventana,
        image=icono_enru,
        bg="#EAEDED",
        cursor="hand2"
    )
    lbl_enrutamiento.image = icono_enru

    ToolTip(lbl_enrutamiento, "Enrutamiento")

    # 👉 Ubicación: a la derecha del icono EPM (ajusta si quiere
    # s)
    lbl_enrutamiento.place(relx=0.22, rely=0.78)

    # Acción al dar click (por ahora abre el visor geográfico)
    lbl_enrutamiento.bind("<Button-1>", lambda e: abrir_routing_streamlit())

except Exception as e:
    print("⚠ Error cargando icono ENRUTAMIENTO:", e)


# ------------------------------------------------------------
# INICIAR INTERFAZ
# ------------------------------------------------------------
ventana.mainloop()
