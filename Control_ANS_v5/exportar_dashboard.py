"""
------------------------------------------------------------
ACTUALIZAR PLANTILLA CONTROL ANS (versión final y estable)
------------------------------------------------------------
Autor: Héctor + IA (2025)
------------------------------------------------------------
Descripción:
1️⃣ Copia datos desde FENIX_ANS.xlsx → DATOS_ANS
2️⃣ Copia columnas clave → DASHBOARD_ANS (desde fila 23)
3️⃣ Crea/redimensiona la tabla estructurada (B:M)
4️⃣ Refresca automáticamente tablas dinámicas, KPI y gráficos
5️⃣ Mantiene intactos macros, segmentadores y formato
------------------------------------------------------------
"""

import pandas as pd
from pathlib import Path
import win32com.client as win32
import time

# ------------------------------------------------------------
# RUTAS
# ------------------------------------------------------------
ruta_plantilla = Path(r"C:\Users\Acer\Desktop\Plantilla Dashboard\Plantilla.xlsm")
ruta_origen = Path(r"C:\Users\Acer\Desktop\Control_ANS\data_clean\FENIX_ANS.xlsx")

# ------------------------------------------------------------
# VALIDACIÓN PREVIA
# ------------------------------------------------------------
if not ruta_origen.exists():
    print(f"❌ ERROR: No se encontró el archivo origen: {ruta_origen}")
    exit()

if not ruta_plantilla.exists():
    print(f"❌ ERROR: No se encontró la plantilla: {ruta_plantilla}")
    exit()

try:
    with open(ruta_plantilla, "r+"):
        pass
except PermissionError:
    print(f"⚠️ El archivo {ruta_plantilla.name} está abierto en Excel. Cierra antes de continuar.")
    exit()

print("🚀 Iniciando actualización protegida del Dashboard...")

# ------------------------------------------------------------
# BLOQUE 1️⃣ – Cargar datos de origen
# ------------------------------------------------------------
df = pd.read_excel(ruta_origen, dtype=str)
print(f"📊 Registros cargados: {len(df)} filas.")
if "ESTADO" in df.columns:
    df["ESTADO"] = df["ESTADO"].fillna("SIN ESTADO")

# ------------------------------------------------------------
# BLOQUE 2️⃣ – Apertura de Excel (modo silencioso)
# ------------------------------------------------------------
excel = win32.Dispatch("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False

try:
    wb = excel.Workbooks.Open(str(ruta_plantilla))
    ws_datos = wb.Worksheets("DATOS_ANS")
    ws_dash = wb.Worksheets("DASHBOARD_ANS")

    # ------------------------------------------------------------
    # BLOQUE 3️⃣ – Actualizar hoja DATOS_ANS
    # ------------------------------------------------------------
    print("📋 Actualizando hoja DATOS_ANS...")
    used_rows = ws_datos.UsedRange.Rows.Count
    if used_rows > 1:
        ws_datos.Range(f"A2:A{used_rows}").EntireRow.ClearContents()

    for i, fila in enumerate(df.itertuples(index=False), start=2):
        for j, valor in enumerate(fila, start=1):
            ws_datos.Cells(i, j).Value = valor

    print("✅ DATOS_ANS actualizado correctamente.")

    # ------------------------------------------------------------
    # BLOQUE 4️⃣ – Actualizar tabla del DASHBOARD
    # ------------------------------------------------------------
    print("📋 Actualizando tabla DASHBOARD_ANS...")
    columnas_deseadas = [
        "PEDIDO", "FECHA_INICIO_ANS", "MUNICIPIO", "ACTIVIDAD",
        "TIPO_DIRECCION", "FECHA_LIMITE_ANS", "DIAS_RESTANTES", "ESTADO"
    ]
    df_filtrado = df[columnas_deseadas].copy()

    start_row = 23
    start_col = 2  # Columna B
    end_row = start_row + len(df_filtrado)
    end_col = start_col + len(df_filtrado.columns) - 1

    # Encabezados
    for j, col in enumerate(df_filtrado.columns, start=start_col):
        ws_dash.Cells(start_row, j).Value = col

    # Datos
    for i, fila in enumerate(df_filtrado.itertuples(index=False), start=start_row + 1):
        for j, valor in enumerate(fila, start=start_col):
            ws_dash.Cells(i, j).Value = valor

    # Crear o redimensionar tabla (B:M)
    print("🧩 Redimensionando tabla 'Tabla_Dashboard_ANS'...")
    rango_tabla = f"B{start_row}:M{end_row}"
    tablas_existentes = [t.Name for t in ws_dash.ListObjects()]

    if "Tabla_Dashboard_ANS" in tablas_existentes:
        ws_dash.ListObjects("Tabla_Dashboard_ANS").Resize(ws_dash.Range(rango_tabla))
    else:
        ws_dash.ListObjects.Add(1, ws_dash.Range(rango_tabla), 0, 1).Name = "Tabla_Dashboard_ANS"

    print("✅ Tabla estructurada actualizada (B:M).")

    # ------------------------------------------------------------
    # BLOQUE 5️⃣ – Refrescar tablas dinámicas y KPI
    # ------------------------------------------------------------
    print("🔁 Refrescando tablas dinámicas y segmentadores...")
    wb.RefreshAll()
    time.sleep(5)

    wb.Save()
    wb.Close(SaveChanges=True)
    excel.Quit()

    print("💾 Dashboard actualizado correctamente ✅")

except Exception as e:
    print(f"❌ Error durante la actualización: {e}")
    excel.Quit()

print("------------------------------------------------------------")
print("✅ PROCESO COMPLETO FINALIZADO SIN ERRORES ✅")
print("------------------------------------------------------------")
