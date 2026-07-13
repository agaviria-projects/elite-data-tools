from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    ColumnsAutoSizeMode,
    JsCode,
)

import pandas as pd
import streamlit as st


# ==========================================================
# TABLA CORPORATIVA PROFESIONAL
# ==========================================================

def mostrar_tabla(
    df: pd.DataFrame,
    height: int = 460,
):

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
    # GRID
    # ======================================================

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

        rowHeight=42,
        headerHeight=50,

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
        params.eGridHeader.style.background='#EEF2F7';
        params.eGridHeader.style.color='#1F2937';
        params.eGridHeader.style.fontWeight='700';
        params.eGridHeader.style.fontSize='13px';
        params.eGridHeader.style.borderBottom='1px solid #D1D5DB';
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

            background:'#F8FAFC',
            borderBottom:'1px solid #E5E7EB'

        }

    }

    """)

    # ======================================================
    # RESALTAR FILA AL PASAR EL MOUSE
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

        theme="streamlit",
        
        custom_css=css,

        allow_unsafe_jscode=True,

        fit_columns_on_grid_load=True,

        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,

        getRowStyle=row_style,

        custom_jscode={
            "onGridReady": header_style
        },

    )