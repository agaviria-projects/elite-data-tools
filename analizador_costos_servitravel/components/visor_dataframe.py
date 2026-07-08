import ttkbootstrap as ttk

from tkinter import ttk as tkttk

import pandas as pd


# ==========================================
# VISOR DATAFRAME
# ==========================================

class VisorDataFrame(ttk.Labelframe):

    def __init__(self, master):

        super().__init__(
            master,
            text=" Vista de Datos ",
            padding=15
        )

        self.pack(
            fill="both",
            expand=True
        )

        self.df = pd.DataFrame()

        self.lbl_resumen = None
        self.tree = None

        self._crear_interfaz()

    # ======================================
    # INTERFAZ
    # ======================================

    def _crear_interfaz(self):

        self.lbl_resumen = ttk.Label(
            self,
            text="No hay datos cargados."
        )

        self.lbl_resumen.pack(
            anchor="w",
            pady=(0, 10)
        )

        contenedor = ttk.Frame(self)

        contenedor.pack(
            fill="both",
            expand=True
        )

        scroll_y = ttk.Scrollbar(
            contenedor,
            orient="vertical"
        )

        scroll_x = ttk.Scrollbar(
            contenedor,
            orient="horizontal"
        )

        self.tree = tkttk.Treeview(
            contenedor,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        scroll_y.config(
            command=self.tree.yview
        )

        scroll_x.config(
            command=self.tree.xview
        )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scroll_y.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        scroll_x.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        contenedor.rowconfigure(
            0,
            weight=1
        )

        contenedor.columnconfigure(
            0,
            weight=1
        )

    # ======================================
    # MOSTRAR DATAFRAME
    # ======================================

    def mostrar(self, df):

        self.df = df.copy()

        self.tree.delete(
            *self.tree.get_children()
        )

        columnas = list(df.columns)

        self.tree["columns"] = columnas

        for columna in columnas:

            self.tree.heading(
                columna,
                text=columna
            )

            self.tree.column(
                columna,
                width=140,
                anchor="w"
            )

        for fila in df.head(300).itertuples(index=False):

            self.tree.insert(
                "",
                "end",
                values=list(fila)
            )

        memoria = (
            df.memory_usage(deep=True).sum()
            / 1024
            / 1024
        )

        self.lbl_resumen.config(

            text=(
                f"Registros: {len(df):,}    "
                f"Columnas: {len(df.columns)}    "
                f"Memoria: {memoria:.2f} MB"
            )

        )

    # ======================================
    # LIMPIAR
    # ======================================

    def limpiar(self):

        self.tree.delete(
            *self.tree.get_children()
        )

        self.lbl_resumen.config(
            text="No hay datos cargados."
        )

        self.df = pd.DataFrame()