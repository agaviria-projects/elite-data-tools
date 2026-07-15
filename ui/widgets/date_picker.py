import ttkbootstrap as ttk

from tkinter import StringVar

from tkinter import Toplevel
from tkcalendar import Calendar



# ==========================================================
# DATE PICKER
# ==========================================================

class DatePicker(ttk.Frame):

    def __init__(
        self,
        parent,
        label="Fecha",
        value=""
    ):

        super().__init__(parent)

        self.variable = StringVar(value=value)

        self.popup = None
        self.calendar = None

        # --------------------------------------------------
        # ETIQUETA
        # --------------------------------------------------

        ttk.Label(
            self,
            text=f"🗓 {label}",
            font=("Segoe UI", 10, "bold")
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(5, 2)
        )

        # --------------------------------------------------
        # CONTENEDOR
        # --------------------------------------------------

        contenedor = ttk.Frame(self)

        contenedor.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        contenedor.columnconfigure(
            0,
            weight=1
        )

        # --------------------------------------------------
        # ENTRY
        # --------------------------------------------------

        self.entry = ttk.Entry(
            contenedor,
            textvariable=self.variable,
            state="readonly"
        )

        self.entry.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        # --------------------------------------------------
        # BOTÓN
        # --------------------------------------------------

        self.boton = ttk.Button(
            contenedor,
            text="🗓",
            width=3,
            bootstyle="secondary",
            cursor="hand2",
            command=self.abrir_calendario
        )

        self.boton.grid(
            row=0,
            column=1,
            padx=(6, 0)
        )

        self.columnconfigure(
            0,
            weight=1
        )

    # ======================================================
    # CALENDARIO
    # ======================================================

    def abrir_calendario(self):

        if self.popup and self.popup.winfo_exists():
            self.popup.lift()
            return

        self.popup = Toplevel(self)
        self.popup.withdraw()

        self.popup.title("Seleccionar fecha")
        self.popup.resizable(False, False)
        self.popup.transient(self.winfo_toplevel())

        # --------------------------------------------------
        # CALENDARIO
        # --------------------------------------------------

        self.calendar = Calendar(
            self.popup,
            selectmode="day",
            date_pattern="yyyy-mm-dd"
        )

        self.calendar.pack(
            padx=10,
            pady=10
        )

        # --------------------------------------------------
        # BOTÓN ACEPTAR
        # --------------------------------------------------

        def aceptar():

            self.variable.set(
                self.calendar.get_date()
            )

            self.popup.destroy()

            self.popup = None

        ttk.Button(
            self.popup,
            text="Aceptar",
            bootstyle="success",
            cursor="hand2",
            command=aceptar
        ).pack(
            pady=(0, 10)
        )

        # --------------------------------------------------
        # CENTRAR VENTANA
        # --------------------------------------------------

        self.popup.update_idletasks()

        ancho = self.popup.winfo_reqwidth()
        alto = self.popup.winfo_reqheight()

        padre = self.winfo_toplevel()

        x = padre.winfo_rootx() + (padre.winfo_width() - ancho) // 2
        y = padre.winfo_rooty() + (padre.winfo_height() - alto) // 2

        self.popup.geometry(
            f"{ancho}x{alto}+{x}+{y}"
        )
        self.popup.deiconify()
        self.popup.lift()
        self.popup.focus_force()
    # ======================================================
    # GET
    # ======================================================

    def get(self):

        return self.variable.get()

    # ======================================================
    # SET
    # ======================================================

    def set(self, valor):

        self.variable.set(valor)

    # ======================================================
    # CLEAR
    # ======================================================

    def clear(self):

        self.variable.set("")        