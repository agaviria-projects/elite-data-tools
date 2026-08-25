from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    ColumnsAutoSizeMode,
    JsCode,
)

import pandas as pd


# ==========================================================
# TABLA CORPORATIVA PROFESIONAL
# ==========================================================

def mostrar_tabla(
    df: pd.DataFrame,
    height: int = 460,
):
    """
    Muestra un DataFrame con estilo corporativo usando AgGrid.

    Incluye:
    - Filtros por columna.
    - Filtro flotante debajo de cada encabezado.
    - Ordenamiento.
    - Redimensionamiento de columnas.
    - Selección de texto.
    - Filas alternadas.
    - Hover y selección.
    - Paginación.
    """

    if df is None or df.empty:
        return

    # ======================================================
    # COPIA DEL DATAFRAME
    # ======================================================

    df = df.copy()

    # ======================================================
    # GRID
    # ======================================================

    gb = GridOptionsBuilder.from_dataframe(df)

    # ======================================================
    # CONFIGURACIÓN GENERAL DE COLUMNAS
    # ======================================================

    gb.configure_default_column(
        sortable=True,
        filter=True,
        floatingFilter=True,
        editable=False,
        resizable=True,
        minWidth=120,
        cellStyle={
            "fontSize": "13px",
            "fontWeight": "500",
            "display": "flex",
            "alignItems": "center",
        },
    )

    # ======================================================
    # CONFIGURACIÓN DEL GRID
    # ======================================================

    gb.configure_grid_options(
        animateRows=True,
        pagination=True,
        paginationPageSize=20,
        rowHeight=42,
        headerHeight=50,
        floatingFiltersHeight=42,
        suppressRowClickSelection=True,
        enableCellTextSelection=True,
        ensureDomOrder=True,
        rowSelection="single",
        domLayout="normal",
    )

    # ======================================================
    # ESTILO DE FILAS
    # ======================================================

    row_style = JsCode(
        """
        function(params) {

            if (params.node.rowIndex % 2 === 0) {
                return {
                    background: '#FFFFFF',
                    borderBottom: '1px solid #E5E7EB'
                };
            }

            return {
                background: '#F8FAFC',
                borderBottom: '1px solid #E5E7EB'
            };
        }
        """
    )

    # ======================================================
    # CSS CORPORATIVO
    # ======================================================

    css = {
        ".ag-root-wrapper": {
            "border": "1px solid #E5E7EB",
            "border-radius": "12px",
            "overflow": "hidden",
            "box-shadow": "0 6px 18px rgba(15,23,42,.08)",
        },

        ".ag-header": {
            "background-color": "#EEF2F7 !important",
            "border-bottom": "1px solid #D1D5DB",
        },

        ".ag-header-cell": {
            "color": "#1F2937 !important",
            "font-weight": "700 !important",
            "font-size": "13px !important",
            "border-right": "1px solid #E5E7EB",
        },

        ".ag-header-cell-label": {
            "justify-content": "center",
        },

        ".ag-floating-filter": {
            "background-color": "#F8FAFC !important",
            "border-right": "1px solid #E5E7EB",
        },

        ".ag-floating-filter-body input": {
            "border-radius": "6px",
            "border": "1px solid #CBD5E1",
            "padding": "5px 7px",
            "font-size": "12px",
            "background-color": "#FFFFFF",
        },

        ".ag-cell": {
            "font-size": "13px",
            "color": "#222",
            "border-right": "1px solid #EEF2F7",
            "display": "flex",
            "align-items": "center",
        },

        ".ag-row-hover": {
            "background-color": "#ECFDF3 !important",
        },

        ".ag-row-selected": {
            "background-color": "#D1FAE5 !important",
        },

        ".ag-paging-panel": {
            "font-size": "13px",
            "font-weight": "600",
            "padding": "8px",
            "border-top": "1px solid #E5E7EB",
        },

        ".ag-checkbox-input-wrapper": {
            "transform": "scale(1.05)",
        },
    }

    # ======================================================
    # AGGRID
    # ======================================================

    AgGrid(
        df,
        gridOptions=gb.build(),
        height=height,
        theme="streamlit",
        custom_css=css,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        getRowStyle=row_style,
    )
