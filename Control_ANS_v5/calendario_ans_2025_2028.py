# ------------------------------------------------------------
# 🗓️ CALENDARIO ANS (2025–2028)
# ------------------------------------------------------------
# Autor: Héctor + IA (2025)
# Objetivo:
# Mostrar un calendario visual con días hábiles, fines de semana
# y festivos de Colombia entre 2025 y 2028.
# ------------------------------------------------------------

import tkinter as tk
from tkcalendar import Calendar
from datetime import date

# ------------------------------------------------------------
# FESTIVOS COLOMBIA 2025–2028 (principales)
# ------------------------------------------------------------
FESTIVOS = [
    # 2025
    "2025-01-01", "2025-01-06", "2025-03-24", "2025-04-17", "2025-04-18",
    "2025-05-01", "2025-06-23", "2025-06-30", "2025-07-20", "2025-08-07",
    "2025-08-18", "2025-10-13", "2025-11-03", "2025-11-17", "2025-12-08", "2025-12-25",
    # 2026
    "2026-01-01", "2026-01-12", "2026-03-23", "2026-04-02", "2026-04-03",
    "2026-05-01", "2026-05-18", "2026-06-08", "2026-06-15", "2026-07-20",
    "2026-08-07", "2026-08-17", "2026-10-12", "2026-11-02", "2026-11-16", "2026-12-08", "2026-12-25",
    # 2027
    "2027-01-01", "2027-01-11", "2027-03-22", "2027-04-01", "2027-04-02",
    "2027-05-01", "2027-05-24", "2027-06-14", "2027-06-21", "2027-07-20",
    "2027-08-07", "2027-08-16", "2027-10-18", "2027-11-01", "2027-11-15", "2027-12-08", "2027-12-25",
    # 2028
    "2028-01-01", "2028-01-10", "2028-03-20", "2028-04-13", "2028-04-14",
    "2028-05-01", "2028-05-29", "2028-06-19", "2028-06-26", "2028-07-20",
    "2028-08-07", "2028-08-21", "2028-10-16", "2028-11-06", "2028-11-13", "2028-12-08", "2028-12-25",
]

# ------------------------------------------------------------
# FUNCIÓN PARA MOSTRAR CALENDARIO
# ------------------------------------------------------------
def mostrar_calendario():
    ventana = tk.Toplevel()
    ventana.title("Calendario ANS – Días hábiles y festivos")
    ventana.geometry("360x420")
    ventana.resizable(False, False)

    # Widget calendario
    cal = Calendar(
        ventana,
        selectmode="day",
        year=2025,
        month=1,
        day=1,
        date_pattern="yyyy-mm-dd",
        mindate=date(2025, 1, 1),
        maxdate=date(2028, 12, 31),
    )
    cal.pack(pady=20)

    # Colorear fines de semana y festivos
    for y in range(2025, 2029):
        for m in range(1, 13):
            for d in range(1, 32):
                try:
                    dia = date(y, m, d)
                    dia_str = dia.strftime("%Y-%m-%d")
                    # Festivo
                    if dia_str in FESTIVOS:
                        cal.calevent_create(dia, "Festivo", "festivo")
                    # Fines de semana
                    elif dia.weekday() >= 5:  # sábado(5), domingo(6)
                        cal.calevent_create(dia, "Fin de semana", "finde")
                except ValueError:
                    continue

    # Configurar colores
    cal.tag_config("festivo", background="red", foreground="white")
    cal.tag_config("finde", background="#C0C0C0", foreground="black")

    # Botón para cerrar
    tk.Button(ventana, text="Cerrar", bg="gray", fg="white", command=ventana.destroy).pack(pady=10)

# ------------------------------------------------------------
# VENTANA PRINCIPAL PEQUEÑA (ICONO)
# ------------------------------------------------------------
root = tk.Tk()
root.title("Control ANS – Calendario")
root.geometry("200x80")
root.configure(bg="#FFFFFF")
root.resizable(False, False)

# Icono tipo calendario
btn = tk.Button(root, text="📅 Abrir Calendario", bg="#005C2E", fg="white", command=mostrar_calendario)
btn.pack(pady=20)

root.mainloop()
