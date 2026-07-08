print("===== EXPLORADOR COSTOS V2 =====")

import ttkbootstrap as ttk

from analizador_costos_servitravel.data.lector_excel import leer_hoja

from analizador_costos_servitravel.components.explorador_excel import ExploradorExcel
from analizador_costos_servitravel.components.resumen_dataframe import ResumenDataFrame
from analizador_costos_servitravel.components.visor_dataframe import VisorDataFrame
from analizador_costos_servitravel.analytics.perfilador_excel import perfil_dataframe

# ==========================================================
# EXPLORADOR DE COSTOS
# ==========================================================

class ExploradorCostos(ttk.Frame):

    def __init__(self, master):

        super().__init__(master)

        self.pack(
            fill="both",
            expand=True
        )

        self.explorador = None
        self.resumen = None
        self.visor = None

        self._crear_interfaz()

    # ======================================================
    # INTERFAZ
    # ======================================================

    def _crear_interfaz(self):

        # --------------------------------------------------
        # ORIGEN DE INFORMACIÓN
        # --------------------------------------------------

        self.explorador = ExploradorExcel(self)

        self.explorador.configure(
            text="Origen de información"
        )

        self.explorador.pack(
            fill="x",
            pady=(0, 10)
        )

        self.explorador.configurar_callback(
            self.cargar_hoja
        )

        # --------------------------------------------------
        # INDICADORES
        # --------------------------------------------------

        self.resumen = ResumenDataFrame(self)

        self.resumen.configure(
            text="Indicadores generales"
        )

        self.resumen.pack(
            fill="x",
            pady=(0, 10)
        )

        # --------------------------------------------------
        # DETALLE
        # --------------------------------------------------

        self.visor = VisorDataFrame(self)

        self.visor.pack(
            fill="both",
            expand=True
        )

    
    # ======================================================
    # CARGAR HOJA
    # ======================================================

    def cargar_hoja(self, hoja):

        try:

            df = leer_hoja(hoja)


            perfil = perfil_dataframe(df)

            self.resumen.actualizar_perfil(perfil)
           

            self.visor.mostrar(df)

            print("="*70)
            print("HOJA:", hoja)
            print(df.head())
            print(df.dtypes)
            print("="*70)

        except Exception as e:

            ttk.dialogs.Messagebox.show_error(

                message=str(e),

                title="Error"

            )