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

    if df is None or df.empty:
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    # ======================================================
    # CONFIGURACIÓN COLUMNAS
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
    # GRID
    # ======================================================

    gb.configure_grid_options(

        animateRows=True,

        pagination=True,
        paginationPageSize=20,

        rowHeight=40,
        headerHeight=46,

        suppressRowClickSelection=True,
        enableCellTextSelection=True,

        rowSelection="single",

        domLayout="normal",

    )

    # ======================================================
    # ENCABEZADOS
    # ======================================================

    header_style = JsCode("""
    function(params){
        params.eGridHeader.style.background='#0F4C81';
        params.eGridHeader.style.color='white';
        params.eGridHeader.style.fontWeight='700';
        params.eGridHeader.style.fontSize='13px';
        params.eGridHeader.style.borderBottom='2px solid #0A3A62';
    }
    """)

    # ======================================================
    # FILAS
    # ======================================================

    row_style = JsCode("""

    function(params){

        if(params.node.rowIndex % 2 === 0){

            return{
                background:'#FFFFFF',
                borderBottom:'1px solid #E5E7EB'
            }

        }

        return{

            background:'#F4F8FD',
            borderBottom:'1px solid #E5E7EB'

        }

    }

    """)

    # ======================================================
    # RESALTAR FILA AL PASAR EL MOUSE
    # ======================================================

    css = {

        ".ag-root-wrapper": {
            "border": "1px solid #D6DEE8",
            "border-radius": "10px",
            "overflow": "hidden",
            "box-shadow": "0 3px 12px rgba(0,0,0,0.08)",
        },

        ".ag-header": {
            "background-color": "#0F4C81 !important",
            "border-bottom": "2px solid #0A3A62",
        },

        ".ag-header-cell": {
            "color": "white !important",
            "font-weight": "700 !important",
            "font-size": "13px !important",
            "border-right": "1px solid rgba(255,255,255,0.10)",
        },

        ".ag-header-cell-label": {
            "justify-content": "center",
        },

        ".ag-cell": {
            "font-size": "13px",
            "color": "#222",
            "border-right": "1px solid #EEF2F7",
            "display": "flex",
            "align-items": "center",
        },

        ".ag-row-hover": {
            "background-color": "#DCEEFF !important",
        },

        ".ag-row-selected": {
            "background-color": "#B9D9FF !important",
        },

        ".ag-paging-panel": {
            "font-size": "13px",
            "font-weight": "600",
            "padding": "8px",
        },

        ".ag-floating-filter-body input": {
            "border-radius": "6px",
            "border": "1px solid #CBD5E1",
            "padding": "5px",
            "font-size": "12px",
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

        theme="alpine",

        custom_css=css,

        allow_unsafe_jscode=True,

        fit_columns_on_grid_load=True,

        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,

        getRowStyle=row_style,

        custom_jscode={
            "onGridReady": header_style
        },

    )