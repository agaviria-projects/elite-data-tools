"""
------------------------------------------------------------
LIMPIEZA BASE FÉNIX – Proyecto Control_ANS_FENIX
------------------------------------------------------------
Autor: Héctor + IA (2025)
------------------------------------------------------------
Descripción:
- Detecta automáticamente TODOS los CSV pendientes_*.csv.
- Consolida Metropolitana, Suroeste y Occidente.
- Normaliza nombres de columnas.
- Mantiene columnas clave, creando las faltantes vacías.
- Rellena celdas vacías con 'SIN DATOS'.
- Filtra actividades válidas.
- Limpia comillas y espacios.
- Calcula días pactados.
- Exporta a Excel con tabla estructurada + hoja resumen.
------------------------------------------------------------
"""

import pandas as pd
from pathlib import Path
from openpyxl.worksheet.table import Table, TableStyleInfo
import unicodedata
import sys

# ------------------------------------------------------------
# CONFIGURACIÓN DE RUTAS
# ------------------------------------------------------------
base_path = Path(__file__).resolve().parent
ruta_clean = base_path / "data_clean" / "FENIX_CLEAN.xlsx"

# ------------------------------------------------------------
# CARGA DE TODOS LOS CSV DE PENDIENTES
# ------------------------------------------------------------
archivos_csv = sorted(base_path.glob("data_raw/pendientes_*.csv"), key=lambda x: x.stat().st_mtime)

if not archivos_csv:
    raise FileNotFoundError("❌ No se encontró ningún archivo pendientes_*.csv en data_raw/")

print("📂 Archivos CSV detectados:")
dfs = []

for ruta in archivos_csv:
    try:
        print(f"   - Leyendo: {ruta.name}")
        with open(ruta, "r", encoding="latin-1", errors="ignore") as f:
            df_temp = pd.read_csv(
                f,
                sep=",",
                dtype=str,
                quotechar='"',
                on_bad_lines="skip",
                engine="python"
            )

        # ✅ CONCEPTO SE DEFINE AQUÍ (ANTES DEL APPEND)
        nombre_archivo = ruta.name.upper()
        if "PPRG" in nombre_archivo:
            df_temp["CONCEPTO"] = "PPRG"
        else:
            df_temp["CONCEPTO"] = "PROG"

        print(f"     Registros: {len(df_temp)}")
        dfs.append(df_temp)

    except Exception as e:
        print(f"❌ Error leyendo {ruta.name}: {e}")

df = pd.concat(dfs, ignore_index=True)
print(f"\n📊 Total registros consolidados: {len(df)}")


# ------------------------------------------------------------
# NORMALIZACIÓN DE COLUMNAS
# ------------------------------------------------------------
def normalizar_columna(nombre):
    nombre = str(nombre).strip().upper().replace(" ", "_")
    return ''.join(
        c for c in unicodedata.normalize("NFD", nombre)
        if unicodedata.category(c) != "Mn"
    )

df.columns = [normalizar_columna(c) for c in df.columns]

df = df.loc[:, ~df.columns.duplicated()]

# ------------------------------------------------------------
# COLUMNAS REQUERIDAS
# ------------------------------------------------------------
columnas_utiles = [
    "PEDIDO", "PRODUCTO_ID", "TIPO_TRABAJO", "TIPO_ELEMENTO_ID",
    "FECHA_RECIBO", "FECHA_INICIO_ANS", "CLIENTEID", "NOMBRE_CLIENTE",
    "TELEFONO_CONTACTO", "CELULAR_CONTACTO", "DIRECCION",
    "MUNICIPIO", "INSTALACION", "AREA_TRABAJO", "ACTIVIDAD",
    "NOMBRE", "TIPO_DIRECCION","CONCEPTO"
]

for col in columnas_utiles:
    if col not in df.columns:
        df[col] = None

df = df[columnas_utiles].copy()

# # ------------------------------------------------------------
# # FILTRO DE ACTIVIDADES VÁLIDAS
# # ------------------------------------------------------------
# actividades_validas = [
#     "ACREV", "ALEGN", "ALEGA", "ALECA", "ALEMN", "ACAMN",
#     "AMRTR", "APLIN", "REEQU", "INPRE", "DIPRE", "ARTER", "AEJDO"

# df = df[df["ACTIVIDAD"].isin(actividades_validas)]

# ]

# ------------------------------------------------------------
# FILTRO DE ACTIVIDADES SEGÚN CONCEPTO (LÓGICA DE NEGOCIO)
# ------------------------------------------------------------

actividades_prog = {
    "ACREV", "ALEGN", "ALEGA", "ALECA", "ALEMN", "ACAMN",
    "AMRTR", "APLIN", "REEQU", "INPRE", "DIPRE", "ARTER", "AEJDO","VITEC",
}

actividades_pprg = {
    "ACREV", "ALEMN", "AMRTR", "APLIN",
    "REEQU", "INPRE", "DIPRE", "ARTER", "AEJDO","VITEC"
}

df = df[
    (
        (df["CONCEPTO"] == "PROG") &
        (df["ACTIVIDAD"].isin(actividades_prog))
    )
    |
    (
        (df["CONCEPTO"] == "PPRG") &
        (df["ACTIVIDAD"].isin(actividades_pprg))
    )
]

print("\nVALIDACIÓN CONCEPTO vs ACTIVIDAD")
print(df.groupby("CONCEPTO")["ACTIVIDAD"].unique())


# ------------------------------------------------------------
# FILTRO DE NOMBRES PROHIBIDOS
# ------------------------------------------------------------
nombres_excluir = [
    "MET Rev-Inst-Concentra E_CR014",
    "Revisor Inst. Particulares Metrosur"
]
df = df[~df["NOMBRE"].isin(nombres_excluir)]

# ------------------------------------------------------------
# LIMPIEZA DE TEXTO
# ------------------------------------------------------------
for col in ["DIRECCION", "INSTALACION"]:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace("^'", "", regex=True)
        .str.replace("'", "", regex=False)
        .str.strip()
    )

# ------------------------------------------------------------
# CLASIFICACIÓN TIPO_DIRECCION (NORMALIZADA)
# ------------------------------------------------------------
prefijos_urbanos = ("116", "136", "103", "114", "117", "119", "163", "140", "159", "167")

def clasificar_tipo_direccion(direccion, tipo_original):

    # Normalizar tipo_original
    if pd.isna(tipo_original):
        tipo_base = ""
    else:
        tipo_base = str(tipo_original).strip().upper()

    # Si no hay dirección, devolver tipo normalizado
    if pd.isna(direccion):
        return tipo_base

    val = str(direccion).upper()

    # Direcciones explícitamente urbanas por nomenclatura
    if val.startswith(("CR ", "CL ", "CRA ", "CALLE", "CARRERA", "AV ")):
        return "URBANO"

    # Extraer números
    nums = "".join(c for c in val if c.isdigit())
    if len(nums) >= 6:
        for p in prefijos_urbanos:
            if nums.startswith(p):
                return "URBANO"

    # Detectar rural explícito
    if "RURAL" in val:
        return "RURAL"

    # Fallback seguro
    return tipo_base

# ------------------------------------------------------------
# APLICAR CLASIFICACIÓN Y FORZAR MAYÚSCULAS
# ------------------------------------------------------------
df["TIPO_DIRECCION"] = df.apply(
    lambda f: clasificar_tipo_direccion(f["DIRECCION"], f["TIPO_DIRECCION"]),
    axis=1
)

# Blindaje final: todo en MAYÚSCULAS
df["TIPO_DIRECCION"] = (
    df["TIPO_DIRECCION"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# ------------------------------------------------------------
# NORMALIZACIÓN DE FECHAS
# ------------------------------------------------------------
columnas_fecha = ["FECHA_RECIBO", "FECHA_INICIO_ANS"]

for col in columnas_fecha:
    df[col] = pd.to_datetime(
        df[col],
        errors="coerce"
    )

# Rellenar SOLO columnas que NO son fechas
columnas_no_fecha = [c for c in df.columns if c not in columnas_fecha]

columnas_no_fecha_validas = [
    c for c in columnas_no_fecha
    if c in df.columns and not pd.api.types.is_datetime64_any_dtype(df[c])
]

for col in columnas_no_fecha_validas:
    df[col] = df[col].fillna("SIN DATOS")


# print("\n🔎 VALIDACIÓN FECHAS – PEDIDO 23008885")
# print(
#     df.loc[
#         df["PEDIDO"].astype(str).str.strip() == "23008885",
#         ["PEDIDO", "FECHA_INICIO_ANS", "FECHA_RECIBO"]
#     ]
# )

print("Tipo FECHA_INICIO_ANS:", df["FECHA_INICIO_ANS"].dtype)

ruta_correcciones = base_path / "data_raw" / "correcciones_fenix_ans.xlsx"

if ruta_correcciones.exists():
    df_corr = pd.read_excel(ruta_correcciones, dtype=str)

    df_corr.columns = [normalizar_columna(c) for c in df_corr.columns]

    # Columnas mínimas esperadas
    # PEDIDO | FECHA_INICIO_ANS_CORREGIDA
    df_corr["PEDIDO"] = df_corr["PEDIDO"].astype(str).str.strip()

    df_corr["FECHA_INICIO_ANS"] = pd.to_datetime(
        df_corr["FECHA_INICIO_ANS"],
        errors="coerce"
    )

    print(f"🛠️ Correcciones ANS detectadas: {len(df_corr)}")
else:
    df_corr = None
# ------------------------------------------------------------
# 🛠️ CORREGIR FECHA_INICIO_ANS (BUSCARV SIN CREAR COLUMNAS)
# ------------------------------------------------------------
if df_corr is not None and not df_corr.empty:

    # Normalizar pedidos
    df["PEDIDO"] = df["PEDIDO"].astype(str).str.strip()
    df_corr["PEDIDO"] = df_corr["PEDIDO"].astype(str).str.strip()

    # Crear diccionario: PEDIDO → FECHA_INICIO_ANS corregida
    mapa_fechas = dict(
        zip(
            df_corr["PEDIDO"],
            df_corr["FECHA_INICIO_ANS"]
        )
    )

    # Reemplazar fecha SOLO si el pedido existe en correcciones
    df["FECHA_INICIO_ANS"] = df.apply(
        lambda r: mapa_fechas.get(r["PEDIDO"], r["FECHA_INICIO_ANS"]),
        axis=1
    )

    print(f"✅ FECHA_INICIO_ANS corregida para {len(mapa_fechas)} pedidos")
else:
    print("ℹ️ No hay correcciones de fecha ANS para aplicar.")

# ------------------------------------------------------------
# 🛠️ CORREGIR TIPO_DIRECCION (BUSCARV SIN CREAR COLUMNAS)
# Fuente: data_raw/correcciones_fenix_tipo_direccion.xlsx
# Esperado: PEDIDO | TIPO_DIRECCION
# ------------------------------------------------------------
ruta_corr_tipo = base_path / "data_raw" / "correcciones_fenix_tipo_direccion.xlsx"

if ruta_corr_tipo.exists():
    df_tipo = pd.read_excel(ruta_corr_tipo, dtype=str)
    df_tipo.columns = [normalizar_columna(c) for c in df_tipo.columns]

    if "PEDIDO" in df_tipo.columns and "TIPO_DIRECCION" in df_tipo.columns:
        # Normalizar llaves
        df["PEDIDO"] = df["PEDIDO"].astype(str).str.strip()
        df_tipo["PEDIDO"] = df_tipo["PEDIDO"].astype(str).str.strip()

        # Normalizar valor (URBANO/RURAL)
        df_tipo["TIPO_DIRECCION"] = (
            df_tipo["TIPO_DIRECCION"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        mapa_tipo = dict(zip(df_tipo["PEDIDO"], df_tipo["TIPO_DIRECCION"]))

        # Reemplazar SOLO si el pedido existe en correcciones
        df["TIPO_DIRECCION"] = df.apply(
            lambda r: mapa_tipo.get(r["PEDIDO"], r["TIPO_DIRECCION"]),
            axis=1
        )

        # Blindaje final
        df["TIPO_DIRECCION"] = (
            df["TIPO_DIRECCION"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        print(f"✅ TIPO_DIRECCION corregido para {len(mapa_tipo)} pedidos")
    else:
        print("⚠️ correcciones_fenix_tipo_direccion.xlsx no tiene columnas PEDIDO y TIPO_DIRECCION")
else:
    print("ℹ️ No hay correcciones de TIPO_DIRECCION para aplicar.")
# ------------------------------------------------------------
# CÁLCULO DIAS_PACTADOS
# ------------------------------------------------------------
def calcular_dias_pactados(fila):
    if fila["ACTIVIDAD"] == "ALEGN":
        return 7 if fila["TIPO_DIRECCION"] == "URBANO" else 10
    if fila["ACTIVIDAD"] == "ALEGA":
        return 7 if fila["TIPO_DIRECCION"] == "URBANO" else 10
    return 0

df["DIAS_PACTADOS"] = df.apply(calcular_dias_pactados, axis=1)

# ------------------------------------------------------------
# 🧪 VALIDACIÓN RÁPIDA – CONCEPTO PROG / PPRG
# ------------------------------------------------------------
if "CONCEPTO" in df.columns:
    print("\n📊 Validación Concepto (PROG / PPRG):")
    print(df["CONCEPTO"].value_counts())
else:
    print("⚠️ La columna 'Concepto' NO existe en el DataFrame")

# ------------------------------------------------------------
# EXPORTACIÓN A EXCEL
# ------------------------------------------------------------
ruta_clean.parent.mkdir(exist_ok=True)

with pd.ExcelWriter(ruta_clean, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="FENIX_CLEAN")
    ws = writer.sheets["FENIX_CLEAN"]

    rango = f"A1:{chr(64+df.shape[1])}{df.shape[0]+1}"
    tabla = Table(displayName="TABLA_FENIX", ref=rango)
    tabla.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showRowStripes=True
    )
    ws.add_table(tabla)

print("✅ FENIX_CLEAN.xlsx generado correctamente con todas las subzonas.")
print(f"📊 Total registros finales: {len(df)}")