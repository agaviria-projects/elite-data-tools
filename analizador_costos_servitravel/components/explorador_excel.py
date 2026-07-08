import ttkbootstrap as ttk

from analizador_costos_servitravel.data.lector_excel import obtener_hojas


# ==========================================
# EXPLORADOR DE EXCEL
# ==========================================

class ExploradorExcel(ttk.Labelframe):

    def __init__(self, master):

        super().__init__(
            master,
            text=" Explorador Excel ",
            padding=15
        )

        self.pack(fill="both", expand=True)

        self.hojas = []

        self.cmb_hojas = None

        self.callback = None

        self._crear()

    # ======================================
    # INTERFAZ
    # ======================================

    def _crear(self):

        ttk.Label(
            self,
            text="Hojas disponibles"
        ).pack(anchor="w")

        try:

            self.hojas = obtener_hojas()

        except Exception as e:

            ttk.Label(
                self,
                text=str(e),
                bootstyle="danger"
            ).pack(anchor="w")

            return

        self.cmb_hojas = ttk.Combobox(
            self,
            values=self.hojas,
            state="readonly",
            width=45
        )

        self.cmb_hojas.pack(
            anchor="w",
            pady=10
        )

        if self.hojas:
            self.cmb_hojas.current(0)

        ttk.Button(
            self,
            text="📂 Abrir hoja",
            bootstyle="success",
            command=self.abrir_hoja
        ).pack(anchor="w")

    # ======================================
    # CALLBACK
    # ======================================

    def configurar_callback(self, callback):

        self.callback = callback

    # ======================================
    # EVENTO
    # ======================================

    def abrir_hoja(self):

        hoja = self.obtener_hoja()

        if hoja and self.callback:

            self.callback(hoja)

    # ======================================
    # GET
    # ======================================

    def obtener_hoja(self):

        if self.cmb_hojas is None:
            return None

        return self.cmb_hojas.get()