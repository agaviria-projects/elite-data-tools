"""
==========================================================
SEGUIMIENTO INTELIGENTE ANS
----------------------------------------------------------
Archivo : columnas.py
Autor   : ELITE Ingenieros
Objetivo:
Definir las columnas obligatorias que debe contener
el archivo FENIX_ANS.xlsx para su procesamiento.
==========================================================
"""

# ==========================================================
# COLUMNAS OBLIGATORIAS
# ==========================================================

COLUMNAS_REQUERIDAS = [

    "PEDIDO",
    "FECHA_INICIO_ANS",
    "DIRECCION",
    "MUNICIPIO",
    "TIPO_DIRECCION",
    "CONCEPTO",
    "ACTIVIDAD",
    "PRODUCTO_ID",
    "DIAS_PACTADOS",
    "FECHA_LIMITE_ANS",
    "DIAS_RESTANTES",
    "ESTADO",
    "SUBPED",

    # Campos existentes en FENIX_ANS para control ELITE/EPM.
    "DIAS_PACTADOS_EPM",
    "FECHA_LIMITE_EPM",
    "DIAS_RESTANTES_EPM",
    "ESTADO_EPM",
    "VENCIDO_ELITE",
    "VENCIDO_EPM",

]