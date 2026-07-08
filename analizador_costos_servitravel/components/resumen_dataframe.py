import ttkbootstrap as ttk

import pandas as pd


# ==========================================
# RESUMEN DATAFRAME
# ==========================================

class ResumenDataFrame(ttk.Labelframe):

    def __init__(self, master):

        super().__init__(
            master,
            text=" Resumen de la Hoja ",
            padding=15
        )

        self.pack(
            fill="x",
            pady=(0, 10)
        )

        self.labels = {}

        self._crear_interfaz()

    # ======================================
    # INTERFAZ
    # ======================================

    def _crear_interfaz(self):

        contenedor = ttk.Frame(self)

        contenedor.pack(fill="x")

        for columna in range(4):
            contenedor.columnconfigure(columna, weight=1)

        tarjetas = [

            ("📄 Registros", "registros"),
            ("📑 Columnas", "columnas"),
            ("💾 Memoria", "memoria"),
            ("🔁 Duplicados", "duplicados"),

            ("⚠️ Nulos", "nulos"),
            ("🔢 Numéricas", "numericas"),
            ("🔤 Texto", "texto"),
            ("📅 Fechas", "fechas")

        ]

        for i, (titulo, clave) in enumerate(tarjetas):

            card = ttk.Frame(
                contenedor,
                padding=10,
                bootstyle="light"
            )

            fila = i // 4
            columna = i % 4

            card.grid(
                row=fila,
                column=columna,
                padx=5,
                pady=5,
                sticky="nsew"
            )

            ttk.Label(
                card,
                text=titulo,
                font=("Segoe UI", 9)
            ).pack()

            lbl = ttk.Label(
                card,
                text="-",
                font=("Segoe UI", 16, "bold"),
                bootstyle="success"
            )

            lbl.pack()

            self.labels[clave] = lbl

    # ======================================
    # ACTUALIZAR
    # ======================================

    def actualizar(self, df):

        if df is None or df.empty:

            self.limpiar()
            return

        memoria = (
            df.memory_usage(deep=True)
              .sum()
              / 1024
              / 1024
        )

        self.labels["registros"].config(
            text=f"{len(df):,}"
        )

        self.labels["columnas"].config(
            text=f"{len(df.columns)}"
        )

        self.labels["memoria"].config(
            text=f"{memoria:.2f} MB"
        )

        self.labels["duplicados"].config(
            text=f"{df.duplicated().sum():,}"
        )

        self.labels["nulos"].config(
            text=f"{df.isna().sum().sum():,}"
        )

        self.labels["numericas"].config(
            text=str(
                len(
                    df.select_dtypes(
                        include="number"
                    ).columns
                )
            )
        )

        self.labels["texto"].config(
            text=str(
                len(
                    df.select_dtypes(
                        include="object"
                    ).columns
                )
            )
        )

        self.labels["fechas"].config(
            text=str(
                len(
                    df.select_dtypes(
                        include="datetime"
                    ).columns
                )
            )
        )

    # ======================================
    # LIMPIAR
    # ======================================

    def limpiar(self):

        for lbl in self.labels.values():

            lbl.config(text="-")

    # ======================================
    # ACTUALIZAR PERFIL
    # ======================================

    def actualizar_perfil(self, perfil):

        self.labels["registros"].config(
            text=f'{perfil["registros"]:,}'
        )

        self.labels["columnas"].config(
            text=perfil["columnas"]
        )

        self.labels["memoria"].config(
            text=f'{perfil["memoria"]:.2f} MB'
        )

        self.labels["duplicados"].config(
            text=perfil["duplicados"]
        )

        detalle = perfil["detalle_columnas"]

        numericas = sum(
            1 for c in detalle
            if c["tipo"] in (
                "int64",
                "float64",
                "Int64"
            )
        )

        fechas = sum(
            1 for c in detalle
            if "datetime" in c["tipo"]
        )

        texto = len(detalle) - numericas - fechas

        nulos = sum(
            c["nulos"]
            for c in detalle
        )

        self.labels["nulos"].config(
            text=f"{nulos:,}"
        )

        self.labels["numericas"].config(
            text=numericas
        )

        self.labels["texto"].config(
            text=texto
        )

        self.labels["fechas"].config(
            text=fechas
        )            