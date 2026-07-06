# ------------------------------------------------------------
# 🗓️ CALENDARIO ANS (2025–2028) – VERSIÓN FINAL
# ------------------------------------------------------------
# Héctor + IA (2025)
# ------------------------------------------------------------

import tkinter as tk
from tkcalendar import Calendar
from datetime import date

# ===============================
# FESTIVOS COLOMBIA 2025–2028
# ===============================
FESTIVOS = {
    # 2025
    "2025-01-01","2025-01-06","2025-03-24","2025-04-17","2025-04-18",
    "2025-05-01","2025-06-23","2025-06-30","2025-07-20","2025-08-07",
    "2025-08-18","2025-10-13","2025-11-03","2025-11-17","2025-12-08","2025-12-25",
    # 2026
    "2026-01-01","2026-01-12","2026-03-23","2026-04-02","2026-04-03",
    "2026-05-01","2026-05-18","2026-06-08","2026-06-15","2026-07-20",
    "2026-08-07","2026-08-17","2026-10-12","2026-11-02","2026-11-16","2026-12-08","2026-12-25",
    # 2027
    "2027-01-01","2027-01-11","2027-03-22","2027-04-01","2027-04-02",
    "2027-05-01","2027-05-24","2027-06-14","2027-06-21","2027-07-20",
    "2027-08-07","2027-08-16","2027-10-18","2027-11-01","2027-11-15","2027-12-08","2027-12-25",
    # 2028
    "2028-01-01","2028-01-10","2028-03-20","2028-04-13","2028-04-14",
    "2028-05-01","2028-05-29","2028-06-19","2028-06-26","2028-07-20",
    "2028-08-07","2028-08-21","2028-10-16","2028-11-06","2028-11-13","2028-12-08","2028-12-25",
}

# ===============================
# FUNCIÓN PRINCIPAL
# ===============================
def abrir_calendario():
    win = tk.Toplevel()
    win.title("Calendario ANS - Elite Ingenieros")
    win.geometry("360x250")
    win.resizable(False, False)
    win.configure(bg="#FFFFFF")

    # 🔥🔥🔥 POSICIONAR EL CALENDARIO A LA DERECHA DEL PANEL PRINCIPAL
    win.update_idletasks()
    main_x = win.master.winfo_x()
    main_y = win.master.winfo_y()
    main_w = win.master.winfo_width()
    win.geometry(f"+{main_x + main_w - 150}+{main_y + 80}")
    # 🔥🔥🔥 FIN DEL BLOQUE

    cal = Calendar(
        win,
        selectmode="none",
        year=2025,
        month=1,
        day=1,
        date_pattern="yyyy-mm-dd",
        mindate=date(2025, 1, 1),
        maxdate=date(2028, 12, 31),
        weekendbackground="#C0C0C0",
        weekendforeground="black"
    )
    cal.pack(pady=5)

    # ===== Colorear festivos y fines de semana =====
    for year in range(2025, 2029):
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    d = date(year, month, day)
                    d_str = d.strftime("%Y-%m-%d")

                    # Festivos en ROJO
                    if d_str in FESTIVOS:
                        cal.calevent_create(d, "Festivo", "festivo")

                    # Domingos en rojo
                    elif d.weekday() == 6:
                        cal.calevent_create(d, "Domingo", "domingo")

                except:
                    continue

    # Configuración visual
    cal.tag_config("festivo", background="red", foreground="white")
    cal.tag_config("domingo", background="#FF7575", foreground="black")

    tk.Button(
        win, text="Cerrar", bg="#333", fg="white",
        command=win.destroy
    ).pack(pady=5)

