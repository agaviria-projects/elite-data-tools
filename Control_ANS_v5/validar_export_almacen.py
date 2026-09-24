# ============================================================
# VALIDAR EXPORT ALMACÉN
# Nuevo propósito:
# Validación Mano de Obra vs Materiales obligatorios
# ============================================================

from pathlib import Path
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import DataBarRule


def normalizar_mo(valor):
    if pd.isna(valor):
        return None

    import re

    valor = str(valor).upper().strip()

    # Captura A02U, A02, C04U, C04
    match = re.match(r"^([ABC]\d{2})", valor)
    if match:
        return match.group(1)

    # Captura B15R, B17R, etc.
    match = re.match(r"^(B\d{2}R)", valor)
    if match:
        return match.group(1)

    return valor


def normalizar_material(valor):
    if pd.isna(valor):
        return None

    return str(valor).upper().strip()


print("🚀 INICIANDO VALIDACIÓN MANO DE OBRA vs MATERIALES")
print("📍 Archivo ejecutado:", __file__)

# ============================================================
# RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ruta_base_mo = BASE_DIR / "data_master" / "RELACION_MO_MATERIALES.xlsx"

# ============================================================
# CARGA BASE MAESTRA (INSPECCIÓN)
# ============================================================

if not ruta_base_mo.exists():
    raise FileNotFoundError(f"No se encontró la base maestra: {ruta_base_mo}")

df_base = pd.read_excel(ruta_base_mo, dtype=str)

print("📘 Columnas detectadas en la base maestra:")
print(list(df_base.columns))

print("\n📄 Primeras filas:")
print(df_base.head(10))

# ============================================================
# NORMALIZAR BASE MAESTRA MO → LISTA DE MATERIALES
# ============================================================

# Identificar columnas
col_mo = "CÓDIGO ÍTEM MO"

COLS_NO_MATERIAL = set()

cols_materiales = [c for c in df_base.columns if c not in {col_mo, *COLS_NO_MATERIAL}]


# Limpiar y construir lista de materiales por MO
df_base_norm = (
    df_base.assign(
        materiales_obligatorios=lambda d: d[cols_materiales].apply(
            lambda fila: [
                normalizar_material(x)
                for x in fila
                if pd.notna(x) and str(x).strip().upper() != "N/A"
            ],
            axis=1,
        )
    )[[col_mo, "materiales_obligatorios"]]
)

print("\n🧩 Base maestra normalizada:")
print(df_base_norm[df_base_norm[col_mo].str.strip().str.upper().eq("A05")])
print(df_base_norm.head(10))

# ============================================================
# CARGA AUTOMÁTICA DE TXT DE MO vs MATERIALES
# ============================================================

ruta_txt = BASE_DIR / "data_mo_materiales"

if not ruta_txt.exists():
    raise FileNotFoundError("No existe la carpeta data_mo_materiales")

archivos_txt = list(ruta_txt.glob("*.txt"))

if not archivos_txt:
    raise FileNotFoundError("No hay archivos TXT en data_mo_materiales")

print(f"📂 Archivos TXT encontrados: {len(archivos_txt)}")

df_list = []

for archivo in archivos_txt:
    print(f"📄 Leyendo: {archivo.name}")

    df_tmp = pd.read_csv(
        archivo,
        sep="|",            # ⚠️ ajusta si el separador es otro
        dtype=str,
        encoding="latin-1"  # típico en FENIX
    )

    df_tmp["ARCHIVO_ORIGEN"] = archivo.name
    df_list.append(df_tmp)

df_export = pd.concat(df_list, ignore_index=True)

print("\n📦 Columnas detectadas en TXT:")
print(list(df_export.columns))

print("\n📄 Primeras filas consolidadas:")
print(df_export.head(10))

print("\n📦 Columnas detectadas en ALMACEN_EXPORT:")
print(list(df_export.columns))

print("\n📄 Primeras filas ALMACEN_EXPORT:")
print(df_export.head(10))

# ============================================================
# VALIDACIÓN MO vs MATERIALES (LÓGICA PRINCIPAL)
# ============================================================

# ================================
# 1) MANO DE OBRA (solo CON)
# ================================
df_mo = df_export[df_export["tipo"] == "CON"].copy()
df_mo["MO_BASE"] = df_mo["item_cont"].apply(normalizar_mo)

df_mo = df_mo[
    df_mo["pedido"].notna() &
    df_mo["MO_BASE"].notna()
][["pedido", "subz", "MO_BASE"]]

# ================================
# 2) MATERIALES (solo SUM)
# ================================
df_mat = df_export[df_export["tipo"] == "SUM"].copy()
df_mat["MATERIAL"] = df_mat["item_res"].apply(normalizar_material)

df_mat = df_mat[
    df_mat["pedido"].notna() &
    df_mat["MATERIAL"].notna()
][["pedido", "MATERIAL"]]

# df_mat["MATERIAL"] = df_mat["MATERIAL"].str.strip()

df_export_con = df_export[
    (df_export["tipo"] == "CON") &
    (df_export["item_cont"].notna())
].copy()

# 4️⃣ Agrupar materiales entregados por pedido + MO
df_entregados = (
    df_mo
    .merge(df_mat, on="pedido", how="left")
    .groupby(["pedido", "subz", "MO_BASE"])["MATERIAL"]
    .apply(lambda x: sorted(set(x.dropna())))
    .reset_index(name="materiales_entregados")
)

# --- Preparar base maestra como diccionario
mo_to_materiales = dict(
    zip(
        df_base_norm["CÓDIGO ÍTEM MO"],
        df_base_norm["materiales_obligatorios"]
    )
)

resultados = []

for _, row in df_entregados.iterrows():
    pedido = row["pedido"]
    subzona = row["subz"]
    mo = row["MO_BASE"]
    entregados = set(row["materiales_entregados"])

    if mo not in mo_to_materiales:
        resultados.append({
            "pedido": pedido,
            "subzona": row["subz"],
            "mano_obra": mo,
            "estado": "Código de mano de obra no existe en la base maestra",
            "estado_codigo": "NO EXISTEN EN BD",
            "faltantes": "",
            "sobrantes": ", ".join(entregados)
        })
        continue

    obligatorios = set(mo_to_materiales[mo])

    faltantes = sorted(obligatorios - entregados)
    sobrantes = sorted(entregados - obligatorios)

    if not faltantes and not sobrantes:
        estado = "Materiales correctos"
        estado_codigo = "OK"
    elif faltantes and not sobrantes:
        estado = "Faltan materiales obligatorios"
        estado_codigo = "FALTAN"
    elif sobrantes and not faltantes:
        estado = "Materiales sobrantes"
        estado_codigo = "SOBRAN"
    else:
        estado = "Faltan y sobran materiales"
        estado_codigo = "AMBOS"

    resultados.append({
        "pedido": pedido,
        "subzona": subzona,
        "mano_obra": mo,
        "estado": estado,
        "estado_codigo": estado_codigo,
        "faltantes": ", ".join(faltantes),
        "sobrantes": ", ".join(sobrantes)
    })

df_resultado = pd.DataFrame(resultados)

print("\n📊 RESULTADO VALIDACIÓN (vista previa):")
print(df_resultado.head(20))

# ============================================================
# BLOQUE NUEVO (NO TOCA LÓGICA EXISTENTE):
# Reglas especiales "UNO DE", ignorar materiales, y alerta cantidad>1 para MO Cxx
# ============================================================

# --- 1) Reglas "UNO DE" (si aparece cualquiera del grupo, el grupo se considera cumplido)
REGLAS_UNO_DE = {
    # A12: si aparece 200092 o 200093 => OK (no faltante por ese grupo)
    "A12": [{"200092", "200093"}],

    # A05: UNO DE LOS CINCO (incluye 323739)
    "A05": [{"200492", "200410", "200411", "200493", "323739"}],

    # A23: si aparece uno de estos 4 => OK
    "A23": [{"200493", "200411", "200492", "200410"}],

    # A17: si aparece 210954 o 210949 => OK
    "A17": [{"210954", "210949"}],

    # A22: si aparece uno de estos 4 => OK
    "A22": [{"200410", "200493", "200411", "200492"}],

    # A31: si aparece 211618 o 336759 => OK
    "A31": [{"211618", "336759"}],

    # A06: UNO DE LOS CINCO (incluye 323739)
    "A06": [{"200493", "200411", "200492", "200410", "323739"}],

    # A08: UNO DE LOS CUATRO
    "A08": [{"200410", "200493", "200411", "200492"}],
}

# --- 2) Materiales a ignorar (amarillos) si aparecen, para que NO cuenten como sobrantes
MATERIALES_IGNORAR_GLOBAL = {"215887", "219404"}

# ============================================================
# REGLAS DE MATERIALES POR SUBZONA
# ============================================================

MATERIALES_SOLO_POR_SUBZONA = {
    "200099": {"NDC"},
}



def _recalcular_estado(obligatorios_set, entregados_set):
    """Replica la lógica de estado sin tocar el loop original."""
    faltantes = sorted(obligatorios_set - entregados_set)
    sobrantes = sorted(entregados_set - obligatorios_set)

    if not faltantes and not sobrantes:
        return ("Materiales correctos", "OK", "", "")
    if faltantes and not sobrantes:
        return ("Faltan materiales obligatorios", "FALTAN", ", ".join(faltantes), "")
    if sobrantes and not faltantes:
        return ("Materiales sobrantes", "SOBRAN", "", ", ".join(sobrantes))

    return ("Faltan y sobran materiales", "AMBOS", ", ".join(faltantes), ", ".join(sobrantes))


def _aplicar_reglas_uno_de(mo, obligatorios_set, entregados_set):
    """
    Si existe regla UNO_DE para la MO:
      - si el entregado cumple algún grupo (intersección), entonces ese grupo queda 'cumplido'
      - por tanto se eliminan como faltantes los elementos faltantes de ese grupo
    """
    grupos = REGLAS_UNO_DE.get(mo, [])
    if not grupos:
        return obligatorios_set  # sin cambios

    obligatorios_corregidos = set(obligatorios_set)

    for grupo in grupos:
        # Si entregados tiene al menos uno del grupo, el grupo se considera cumplido
        if entregados_set.intersection(grupo):
            # Entonces NO exigimos los otros del grupo
            obligatorios_corregidos -= (grupo - entregados_set)

    return obligatorios_corregidos


# --- 3) Mapa rápido de entregados por (pedido, subz, mo)
_entregados_map = {}
for _, r in df_entregados.iterrows():
    k = (r["pedido"], r["subz"], r["MO_BASE"])
    _entregados_map[k] = set(r["materiales_entregados"] or [])


# --- 4) Post-proceso de df_resultado: corrige A05/A12/A23 y aplica ignorados para Cxx (sobrantes)
def _post_procesar_validacion(df_resultado_in):
    df = df_resultado_in.copy()

    for c in ["faltantes", "sobrantes", "estado", "estado_codigo", "mano_obra", "pedido", "subzona"]:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str)

    mask_okbd = df["estado_codigo"] != "NO EXISTEN EN BD"

    for i, row in df[mask_okbd].iterrows():
        pedido = row["pedido"]
        subz = row["subzona"]
        mo = row["mano_obra"]

        key = (pedido, subz, mo)
        entregados = set(_entregados_map.get(key, set()))

        if mo.startswith("C"):
            entregados = set([x for x in entregados if x not in MATERIALES_IGNORAR_GLOBAL])

        if key not in _entregados_map:
            continue

        obligatorios = set(
            mo_to_materiales.get(mo, [])
        )

        # ============================================================
        # REGLAS DE MATERIALES SEGÚN SUBZONA
        #
        # Ejemplo:
        # 200099 solamente aplica para NDC
        # ============================================================
        for material, subzonas_permitidas in MATERIALES_SOLO_POR_SUBZONA.items():

            if subz not in subzonas_permitidas:

                # Fuera de la subzona permitida, el material NO APLICA.
                # No debe generar ni FALTANTE ni SOBRANTE.
                obligatorios.discard(material)
                entregados.discard(material)

        # Aplicar reglas UNO DE existentes
        obligatorios = _aplicar_reglas_uno_de(
            mo,
            obligatorios,
            entregados
        )

        estado, estado_codigo, faltantes_str, sobrantes_str = (
            _recalcular_estado(
                obligatorios,
                entregados
            )
        )

        # ============================================================
        # 🔴 ALERTA ESPECÍFICA A31 (conflicto + cantidad)
        # ============================================================

        if mo == "A31":

            tiene_211618 = "211618" in entregados
            tiene_336759 = "336759" in entregados

            # 🔴 PRIORIDAD 1: CONFLICTO
            if tiene_211618 and tiene_336759:
                estado = "Revisar: A31 tiene ambos códigos (211618 y 336759)"
                estado_codigo = "REVISAR_A31"
                faltantes_str = ""
                sobrantes_str = ""

            else:
                # 🟠 PRIORIDAD 2: CANTIDAD > 1
                df_sum = df_export[df_export["tipo"] == "SUM"]
                df_sum = df_sum[df_sum["pedido"] == pedido].copy()

                df_sum["MAT"] = df_sum["item_res"].astype(str).str.strip()
                df_sum["CANT_NUM"] = pd.to_numeric(df_sum["cantidad"], errors="coerce").fillna(0)

                df_a31 = df_sum[df_sum["MAT"].isin(["211618", "336759"])]
                mayores = df_a31[df_a31["CANT_NUM"] > 1]

                if not mayores.empty:
                    detalle = ", ".join(
                        [f"{r['MAT']}={int(r['CANT_NUM'])}" for _, r in mayores.iterrows()]
                    )

                    estado = f"Revisar cantidades A31: {detalle}"
                    estado_codigo = "CANTIDAD_A31>1"
                    faltantes_str = ""
                    sobrantes_str = ""

        # 🔥 GUARDAR CAMBIOS (CRÍTICO)
        df.at[i, "estado"] = estado
        df.at[i, "estado_codigo"] = estado_codigo
        df.at[i, "faltantes"] = faltantes_str
        df.at[i, "sobrantes"] = sobrantes_str

    return df


# 🔥 ESTA LÍNEA NO SE BORRA
df_resultado = _post_procesar_validacion(df_resultado)

# ============================================================
# BLOQUE NUEVO: si materiales están en BD pero se consideran "NO APLICAN",
# eliminarlos de faltantes/sobrantes para MO que empiezan con C
# ============================================================

def _quitar_no_aplican_en_resultado(df_in, no_aplican_set):
    df = df_in.copy()
    df["faltantes"] = df["faltantes"].fillna("").astype(str)
    df["sobrantes"] = df["sobrantes"].fillna("").astype(str)

    mask_c = df["mano_obra"].fillna("").astype(str).str.startswith("C")

    def _filtrar_lista_txt(txt):
        items = [x.strip() for x in txt.split(",") if x.strip()]
        items = [x for x in items if x not in no_aplican_set]
        return ", ".join(items)

    df.loc[mask_c, "faltantes"] = df.loc[mask_c, "faltantes"].apply(_filtrar_lista_txt)
    df.loc[mask_c, "sobrantes"] = df.loc[mask_c, "sobrantes"].apply(_filtrar_lista_txt)

    # Recalcular estado/estado_codigo basado en strings (simple)
    for i, r in df[mask_c].iterrows():
        f = r["faltantes"].strip()
        s = r["sobrantes"].strip()

        if not f and not s:
            df.at[i, "estado"] = "Materiales correctos"
            df.at[i, "estado_codigo"] = "OK"
        elif f and not s:
            df.at[i, "estado"] = "Faltan materiales obligatorios"
            df.at[i, "estado_codigo"] = "FALTAN"
        elif s and not f:
            df.at[i, "estado"] = "Materiales sobrantes"
            df.at[i, "estado_codigo"] = "SOBRAN"
        else:
            df.at[i, "estado"] = "Faltan y sobran materiales"
            df.at[i, "estado_codigo"] = "AMBOS"

    return df
# ============================================================
# 🆕 EXCEPCIÓN POR MO:
# Para item C04 se debe EXCLUIR el material 215887A
# (no debe aparecer como faltante ni sobrante SOLO para C04)
# ============================================================

MATERIALES_EXCLUIR_POR_MO = {
    "C04": {"215887A"},
}

def _excluir_materiales_por_mo_en_resultado(df_in, reglas_exclusion):
    df = df_in.copy()

    # Asegurar columnas texto
    for c in ["mano_obra", "faltantes", "sobrantes", "estado", "estado_codigo"]:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str)

    def _filtrar_txt_por_set(txt, excluir_set):
        items = [x.strip() for x in txt.split(",") if x.strip()]
        items = [x for x in items if x not in excluir_set]
        return ", ".join(items)

    # Aplicar exclusión solo a los MO definidos
    for mo, excluir_set in reglas_exclusion.items():
        mask_mo = df["mano_obra"].str.upper().str.strip().eq(str(mo).upper().strip())

        if "faltantes" in df.columns:
            df.loc[mask_mo, "faltantes"] = df.loc[mask_mo, "faltantes"].apply(
                lambda t: _filtrar_txt_por_set(t, excluir_set)
            )

        if "sobrantes" in df.columns:
            df.loc[mask_mo, "sobrantes"] = df.loc[mask_mo, "sobrantes"].apply(
                lambda t: _filtrar_txt_por_set(t, excluir_set)
            )

        # Recalcular estado basado en strings finales
        for i, r in df[mask_mo].iterrows():
            f = (r.get("faltantes", "") or "").strip()
            s = (r.get("sobrantes", "") or "").strip()

            if not f and not s:
                df.at[i, "estado"] = "Materiales correctos"
                df.at[i, "estado_codigo"] = "OK"
            elif f and not s:
                df.at[i, "estado"] = "Faltan materiales obligatorios"
                df.at[i, "estado_codigo"] = "FALTAN"
            elif s and not f:
                df.at[i, "estado"] = "Materiales sobrantes"
                df.at[i, "estado_codigo"] = "SOBRAN"
            else:
                df.at[i, "estado"] = "Faltan y sobran materiales"
                df.at[i, "estado_codigo"] = "AMBOS"

    return df


df_resultado = _excluir_materiales_por_mo_en_resultado(df_resultado, MATERIALES_EXCLUIR_POR_MO)
df_resultado = _quitar_no_aplican_en_resultado(df_resultado, MATERIALES_IGNORAR_GLOBAL)

# ============================================================
# 🧪 QA: Confirmar exclusión 215887A SOLO para C04
# ============================================================

mask_c04 = df_resultado["mano_obra"].fillna("").astype(str).str.upper().str.strip().eq("C04")

c04_con_215887a_falt = df_resultado.loc[
    mask_c04 & df_resultado["faltantes"].fillna("").astype(str).str.contains(r"\b215887A\b", na=False),
    ["pedido", "subzona", "mano_obra", "estado_codigo", "faltantes"]
]

total_c04 = int(mask_c04.sum())
total_c04_con_215887a = int(len(c04_con_215887a_falt))

print(f"🧪 QA C04 -> Total filas C04: {total_c04}")
print(f"🧪 QA C04 -> Aún con 215887A en FALTANTES: {total_c04_con_215887a}")

if total_c04_con_215887a > 0:
    print("⚠️ Ejemplos donde todavía aparece 215887A como faltante (debería ser 0):")
    print(c04_con_215887a_falt.head(10).to_string(index=False))
else:
    print("✅ OK: se elimina de la BD el material 215887A no es faltante para C04.")


# ============================================================
# ALERTA: Para MO que comiencen con C, si cantidad > 1 en la extracción => marcar alerta
# ============================================================

def _alertas_cantidad_c(df_export_in):
    df_con = df_export_in[df_export_in["tipo"] == "CON"].copy()
    df_con["MO_BASE"] = df_con["item_cont"].apply(normalizar_mo)

    if "cantidad" in df_con.columns:
        df_con["CANT_NUM"] = pd.to_numeric(df_con["cantidad"], errors="coerce").fillna(0)
    else:
        df_con["CANT_NUM"] = 0

    df_con = df_con[df_con["MO_BASE"].astype(str).str.startswith("C")]

    df_alert = df_con[df_con["CANT_NUM"] > 1][["pedido", "subz", "MO_BASE", "CANT_NUM"]].copy()

    if df_alert.empty:
        return pd.DataFrame(columns=["pedido", "subzona", "mano_obra", "ALERTA_CANTIDAD", "DETALLE_CANTIDAD"])

    df_alert["DET"] = df_alert.apply(lambda r: f"{r['MO_BASE']}={int(r['CANT_NUM'])}", axis=1)

    out = (
        df_alert
        .groupby(["pedido", "subz", "MO_BASE"])["DET"]
        .apply(lambda x: ", ".join(sorted(set(x))))
        .reset_index()
        .rename(columns={"subz": "subzona", "MO_BASE": "mano_obra"})
    )

    out["ALERTA_CANTIDAD"] = "CANTIDAD>1"
    out["DETALLE_CANTIDAD"] = out["DET"]
    out = out.drop(columns=["DET"])

    return out[["pedido", "subzona", "mano_obra", "ALERTA_CANTIDAD", "DETALLE_CANTIDAD"]]


df_alertas = _alertas_cantidad_c(df_export_con)

# Merge de alertas (sin romper nada)
if not df_alertas.empty:
    df_resultado = df_resultado.merge(
        df_alertas,
        on=["pedido", "subzona", "mano_obra"],
        how="left"
    )
else:
    df_resultado["ALERTA_CANTIDAD"] = ""
    df_resultado["DETALLE_CANTIDAD"] = ""

df_resultado["ALERTA_CANTIDAD"] = df_resultado["ALERTA_CANTIDAD"].fillna("")
df_resultado["DETALLE_CANTIDAD"] = df_resultado["DETALLE_CANTIDAD"].fillna("")

# ============================================================
# 🆕 ALERTAS ADICIONALES (NO TOCA LÓGICA EXISTENTE)
# 1) Duplicados de Mano de Obra por pedido (incluye A, B, C y D)
# 2) Para MO que comiencen con A: si cantidad > 1 => alerta (igual lógica que Cxx)
# ============================================================

def _alerta_duplicados_mo(df_export_in):
    """
    Detecta duplicados de MO_BASE por pedido + subz.
    Aplica para cualquier mano de obra:
    Axx, Bxx, Cxx, Dxx, B15R, B17R, etc.
    """

    df_con = df_export_in[
        df_export_in["tipo"] == "CON"
    ].copy()

    df_con["MO_BASE"] = (
        df_con["item_cont"]
        .apply(normalizar_mo)
    )

    df_con = df_con[
        df_con["pedido"].notna() &
        df_con["subz"].notna() &
        df_con["MO_BASE"].notna()
    ][["pedido", "subz", "MO_BASE"]]

    df_cnt = (
        df_con
        .groupby(
            ["pedido", "subz", "MO_BASE"]
        )
        .size()
        .reset_index(name="REP")
    )

    df_dup = df_cnt[
        df_cnt["REP"] > 1
    ].copy()

    if df_dup.empty:
        return pd.DataFrame(
            columns=[
                "pedido",
                "subzona",
                "mano_obra",
                "ALERTA_DUPLICADO_MO",
                "DETALLE_DUPLICADO_MO"
            ]
        )

    df_dup["DET"] = df_dup.apply(
        lambda r: f"{r['MO_BASE']} x{int(r['REP'])}",
        axis=1
    )

    out = (
        df_dup
        .groupby(["pedido", "subz"])["DET"]
        .apply(lambda x: ", ".join(sorted(set(x))))
        .reset_index()
        .rename(columns={"subz": "subzona"})
    )

    out["ALERTA_DUPLICADO_MO"] = "MO_DUPLICADA"
    out["DETALLE_DUPLICADO_MO"] = out["DET"]

    out = out.drop(columns=["DET"])

    out["mano_obra"] = ""

    return out[
        [
            "pedido",
            "subzona",
            "mano_obra",
            "ALERTA_DUPLICADO_MO",
            "DETALLE_DUPLICADO_MO"
        ]
    ]


def _alertas_cantidad_prefijo(df_export_in, prefijo="A"):
    """
    Misma lógica de Cxx cantidad>1, pero para prefijo (ej: 'A').
    """
    df_con = df_export_in[df_export_in["tipo"] == "CON"].copy()
    df_con["MO_BASE"] = df_con["item_cont"].apply(normalizar_mo)

    if "cantidad" in df_con.columns:
        df_con["CANT_NUM"] = pd.to_numeric(
            df_con["cantidad"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip(),
            errors="coerce"
        ).fillna(0)
    else:
        df_con["CANT_NUM"] = 0
    print("\n========== DEBUG CANTIDADES A ==========")

    print(
        df_con[
            ["pedido", "subz", "MO_BASE", "cantidad", "CANT_NUM"]
        ]
        .query("MO_BASE.str.startswith('A')", engine="python")
        .head(30)
        .to_string(index=False)
    )    
    print(df_con["MO_BASE"].unique())

    df_con = df_con[
        df_con["pedido"].notna() &
        df_con["subz"].notna() &
        df_con["MO_BASE"].notna()
    ][["pedido", "subz", "MO_BASE", "CANT_NUM"]]

    df_con = df_con[df_con["MO_BASE"].astype(str).str.startswith(prefijo)]

    df_alert = df_con[df_con["CANT_NUM"] > 1].copy()
    if df_alert.empty:
        return pd.DataFrame(columns=["pedido", "subzona", "mano_obra", "ALERTA_CANTIDAD_A", "DETALLE_CANTIDAD_A"])

    df_alert["DET"] = df_alert.apply(lambda r: f"{r['MO_BASE']}={int(r['CANT_NUM'])}", axis=1)

    out = (
        df_alert.groupby(["pedido", "subz", "MO_BASE"])["DET"]
        .apply(lambda x: ", ".join(sorted(set(x))))
        .reset_index()
        .rename(columns={"subz": "subzona", "MO_BASE": "mano_obra"})
    )

    out["ALERTA_CANTIDAD_A"] = "CANTIDAD_A>1"
    out["DETALLE_CANTIDAD_A"] = out["DET"]
    out = out.drop(columns=["DET"])

    return out[["pedido", "subzona", "mano_obra", "ALERTA_CANTIDAD_A", "DETALLE_CANTIDAD_A"]]


def _alertas_cantidad_d(df_export_in):
    """
    Detecta cantidad > 1 únicamente para las MO D01-D04,
    tanto urbanas como rurales.
    """
    items_d_controlados = {
        "D01U", "D01R",
        "D02U", "D02R",
        "D03U", "D03R",
        "D04U", "D04R",
    }

    df_con = df_export_in[
        df_export_in["tipo"] == "CON"
    ].copy()

    df_con["MO_BASE"] = (
        df_con["item_cont"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    if "cantidad" in df_con.columns:
        df_con["CANT_NUM"] = pd.to_numeric(
            df_con["cantidad"]
            .fillna("")
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip(),
            errors="coerce"
        ).fillna(0)
    else:
        df_con["CANT_NUM"] = 0

    df_alert = df_con[
        df_con["pedido"].notna()
        & df_con["subz"].notna()
        & df_con["MO_BASE"].isin(items_d_controlados)
        & (df_con["CANT_NUM"] > 1)
    ][
        ["pedido", "subz", "MO_BASE", "CANT_NUM"]
    ].copy()

    if df_alert.empty:
        return pd.DataFrame(
            columns=[
                "pedido",
                "subzona",
                "mano_obra",
                "ALERTA_CANTIDAD_D",
                "DETALLE_CANTIDAD_D",
            ]
        )

    df_alert["DET"] = df_alert.apply(
        lambda r: f"{r['MO_BASE']}={r['CANT_NUM']:g}",
        axis=1
    )

    out = (
        df_alert
        .groupby(["pedido", "subz", "MO_BASE"])["DET"]
        .apply(lambda x: ", ".join(sorted(set(x))))
        .reset_index()
        .rename(
            columns={
                "subz": "subzona",
                "MO_BASE": "mano_obra",
            }
        )
    )

    out["ALERTA_CANTIDAD_D"] = "CANTIDAD_D>1"
    out["DETALLE_CANTIDAD_D"] = out["DET"]

    return out[
        [
            "pedido",
            "subzona",
            "mano_obra",
            "ALERTA_CANTIDAD_D",
            "DETALLE_CANTIDAD_D",
        ]
    ]


def _alertas_cantidad_f(df_export_in):
    """
    Detecta cantidad > 1 únicamente para las MO F01U y F01R.
    """
    items_f_controlados = {"F01U", "F01R"}

    df_con = df_export_in[
        df_export_in["tipo"] == "CON"
    ].copy()

    df_con["MO_BASE"] = (
        df_con["item_cont"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    if "cantidad" in df_con.columns:
        df_con["CANT_NUM"] = pd.to_numeric(
            df_con["cantidad"]
            .fillna("")
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip(),
            errors="coerce"
        ).fillna(0)
    else:
        df_con["CANT_NUM"] = 0

    df_alert = df_con[
        df_con["pedido"].notna()
        & df_con["subz"].notna()
        & df_con["MO_BASE"].isin(items_f_controlados)
        & (df_con["CANT_NUM"] > 1)
    ][
        ["pedido", "subz", "MO_BASE", "CANT_NUM"]
    ].copy()

    if df_alert.empty:
        return pd.DataFrame(
            columns=[
                "pedido",
                "subzona",
                "mano_obra",
                "ALERTA_CANTIDAD_F",
                "DETALLE_CANTIDAD_F",
            ]
        )

    df_alert["DET"] = df_alert.apply(
        lambda r: f"{r['MO_BASE']}={r['CANT_NUM']:g}",
        axis=1
    )

    out = (
        df_alert
        .groupby(["pedido", "subz", "MO_BASE"])["DET"]
        .apply(lambda x: ", ".join(sorted(set(x))))
        .reset_index()
        .rename(
            columns={
                "subz": "subzona",
                "MO_BASE": "mano_obra",
            }
        )
    )

    out["ALERTA_CANTIDAD_F"] = "CANTIDAD_F>1"
    out["DETALLE_CANTIDAD_F"] = out["DET"]

    return out[
        [
            "pedido",
            "subzona",
            "mano_obra",
            "ALERTA_CANTIDAD_F",
            "DETALLE_CANTIDAD_F",
        ]
    ]


# --- 1) Ejecutar alerta de duplicados para cualquier MO tipo CON
df_dup_mo = _alerta_duplicados_mo(
    df_export
)

# Merge por pedido/subzona (aplica a todas las filas de ese pedido/subzona)
if not df_dup_mo.empty:
    df_resultado = df_resultado.merge(
        df_dup_mo[["pedido", "subzona", "ALERTA_DUPLICADO_MO", "DETALLE_DUPLICADO_MO"]],
        on=["pedido", "subzona"],
        how="left"
    )
else:
    df_resultado["ALERTA_DUPLICADO_MO"] = ""
    df_resultado["DETALLE_DUPLICADO_MO"] = ""

df_resultado["ALERTA_DUPLICADO_MO"] = df_resultado["ALERTA_DUPLICADO_MO"].fillna("")
df_resultado["DETALLE_DUPLICADO_MO"] = df_resultado["DETALLE_DUPLICADO_MO"].fillna("")


# --- 2) Ejecutar alerta cantidad>1 para Axx
df_alertas_a = _alertas_cantidad_prefijo(df_export, prefijo="A")

print("\n========== DEBUG ALERTAS A ==========")
print(df_alertas_a.head(20).to_string(index=False))
print("Total alertas A:", len(df_alertas_a))

# Merge por pedido/subzona/mano_obra (igual que Cxx)
if not df_alertas_a.empty:
    df_resultado = df_resultado.merge(
        df_alertas_a,
        on=["pedido", "subzona", "mano_obra"],
        how="left"
    )
else:
    df_resultado["ALERTA_CANTIDAD_A"] = ""
    df_resultado["DETALLE_CANTIDAD_A"] = ""

df_resultado["ALERTA_CANTIDAD_A"] = df_resultado["ALERTA_CANTIDAD_A"].fillna("")
df_resultado["DETALLE_CANTIDAD_A"] = df_resultado["DETALLE_CANTIDAD_A"].fillna("")


# --- 3) Ejecutar alerta cantidad>1 para D01-D04 (U/R)
df_alertas_d = _alertas_cantidad_d(df_export)

if not df_alertas_d.empty:
    df_resultado = df_resultado.merge(
        df_alertas_d,
        on=["pedido", "subzona", "mano_obra"],
        how="left"
    )
else:
    df_resultado["ALERTA_CANTIDAD_D"] = ""
    df_resultado["DETALLE_CANTIDAD_D"] = ""

df_resultado["ALERTA_CANTIDAD_D"] = (
    df_resultado["ALERTA_CANTIDAD_D"].fillna("")
)
df_resultado["DETALLE_CANTIDAD_D"] = (
    df_resultado["DETALLE_CANTIDAD_D"].fillna("")
)

mask_alert_d = df_resultado["ALERTA_CANTIDAD_D"].eq(
    "CANTIDAD_D>1"
)
df_resultado.loc[
    mask_alert_d,
    "estado"
] = "Presenta novedad en las cantidades (D)"
df_resultado.loc[mask_alert_d, "faltantes"] = ""
df_resultado.loc[mask_alert_d, "sobrantes"] = ""


# --- 4) Ejecutar alerta cantidad>1 para F01U/F01R
df_alertas_f = _alertas_cantidad_f(df_export)

if not df_alertas_f.empty:
    df_resultado = df_resultado.merge(
        df_alertas_f,
        on=["pedido", "subzona", "mano_obra"],
        how="left"
    )
else:
    df_resultado["ALERTA_CANTIDAD_F"] = ""
    df_resultado["DETALLE_CANTIDAD_F"] = ""

df_resultado["ALERTA_CANTIDAD_F"] = (
    df_resultado["ALERTA_CANTIDAD_F"].fillna("")
)
df_resultado["DETALLE_CANTIDAD_F"] = (
    df_resultado["DETALLE_CANTIDAD_F"].fillna("")
)

mask_alert_f = df_resultado["ALERTA_CANTIDAD_F"].eq(
    "CANTIDAD_F>1"
)
df_resultado.loc[
    mask_alert_f,
    "estado"
] = "Presenta novedad en las cantidades (F)"
df_resultado.loc[mask_alert_f, "faltantes"] = ""
df_resultado.loc[mask_alert_f, "sobrantes"] = ""


# --- 5) Si hay alerta Axx cantidad>1: estado = novedad cantidades (sin borrar estado_codigo)
mask_alert_a = df_resultado["ALERTA_CANTIDAD_A"].eq("CANTIDAD_A>1")
df_resultado.loc[mask_alert_a, "estado"] = "Presenta novedad en las cantidades (A)"
df_resultado.loc[mask_alert_a, "faltantes"] = ""
df_resultado.loc[mask_alert_a, "sobrantes"] = ""


# ============================================================
# ✅
# - Si hay alerta Cxx cantidad>1:
#     estado = "Presenta novedad en las cantidades"
#     estado_codigo queda igual (OK/FALTAN/SOBRAN/AMBOS)
#     faltantes/sobrantes vacíos
# ============================================================

mask_alert = df_resultado["ALERTA_CANTIDAD"].eq("CANTIDAD>1")
df_resultado.loc[mask_alert, "estado"] = "Presenta novedad en las cantidades"
df_resultado.loc[mask_alert, "faltantes"] = ""
df_resultado.loc[mask_alert, "sobrantes"] = ""


# ============================================================
# DIAGNÓSTICO ALERTAS Cxx cantidad>1 (solo info)
# ============================================================

total_alertas = int((df_resultado["ALERTA_CANTIDAD"] == "CANTIDAD>1").sum())
print(f"🚨 Alertas Cxx por cantidad>1 detectadas: {total_alertas}")

if total_alertas > 0:
    print("📌 Ejemplos de alertas (pedido, subzona, mano_obra, DETALLE_CANTIDAD):")
    print(
        df_resultado.loc[df_resultado["ALERTA_CANTIDAD"] == "CANTIDAD>1",
                         ["pedido", "subzona", "mano_obra", "DETALLE_CANTIDAD"]]
        .head(10)
        .to_string(index=False)
    )


# ============================================================
# LIMPIEZA DE SALIDA (solo presentación)
# - Quita columnas de auditoría que “enredan” el informe
# - Ordena columnas clave
# ============================================================

COLUMNAS_SALIDA = [
    "pedido", "subzona", "mano_obra",
    "estado", "estado_codigo",
    "faltantes",
    "ALERTA_CANTIDAD", "DETALLE_CANTIDAD",
    "ALERTA_CANTIDAD_A", "DETALLE_CANTIDAD_A",
    "ALERTA_CANTIDAD_D", "DETALLE_CANTIDAD_D",
    "ALERTA_CANTIDAD_F", "DETALLE_CANTIDAD_F",
    "ALERTA_DUPLICADO_MO", "DETALLE_DUPLICADO_MO",
    "sobrantes"
]

COLUMNAS_SALIDA = [c for c in COLUMNAS_SALIDA if c in df_resultado.columns]
df_resultado = df_resultado[COLUMNAS_SALIDA].copy()

# Renombrar columnas solo para presentación (minúsculas con sufijo en MAYÚSCULA)
df_resultado = df_resultado.rename(columns={
    "ALERTA_CANTIDAD": "alerta_cantidad_C",
    "DETALLE_CANTIDAD": "detalle_cantidad_C",
    "ALERTA_DUPLICADO_MO": "alerta_duplicado_MO",
    "DETALLE_DUPLICADO_MO": "detalle_duplicado_MO",
    "ALERTA_CANTIDAD_A": "alerta_cantidad_A",
    "DETALLE_CANTIDAD_A": "detalle_cantidad_A",
    "ALERTA_CANTIDAD_D": "alerta_cantidad_D",
    "DETALLE_CANTIDAD_D": "detalle_cantidad_D",
    "ALERTA_CANTIDAD_F": "alerta_cantidad_F",
    "DETALLE_CANTIDAD_F": "detalle_cantidad_F",
})
# ============================================================
# HOJA DUPLICADOS MO
# ============================================================

df_con_dup = df_export[
    df_export["tipo"] == "CON"
].copy()

df_con_dup["MO_BASE"] = (
    df_con_dup["item_cont"]
    .apply(normalizar_mo)
)

df_mo_duplicadas = (
    df_con_dup
    .groupby(
        ["pedido", "subz", "MO_BASE"]
    )
    .size()
    .reset_index(name="veces")
)

df_mo_duplicadas = df_mo_duplicadas[
    df_mo_duplicadas["veces"] > 1
]

df_mo_duplicadas = df_mo_duplicadas.rename(
    columns={
        "subz": "subzona",
        "MO_BASE": "mano_obra"
    }
)

print(
    f"🚨 Manos de obra duplicadas encontradas: "
    f"{len(df_mo_duplicadas)}"
)

# ============================================================
# HOJA NUEVA: MATERIALES_CANTIDAD
# Detecta materiales SUM con cantidad > 1
# ============================================================

df_material_cantidad = df_export[
    df_export["tipo"] == "SUM"
].copy()

df_material_cantidad["material"] = (
    df_material_cantidad["item_res"]
    .astype(str)
    .str.strip()
)

df_material_cantidad["cantidad"] = pd.to_numeric(
    df_material_cantidad["cantidad"]
    .astype(str)
    .str.replace(",", ".", regex=False)
    .str.strip(),
    errors="coerce"
).fillna(0)

df_material_cantidad = df_material_cantidad[
    df_material_cantidad["cantidad"] > 1
][
    ["pedido", "subz", "material", "cantidad"]
].copy()

df_material_cantidad = df_material_cantidad.rename(
    columns={
        "subz": "subzona"
    }
)

df_material_cantidad["alerta"] = "MATERIAL_CANTIDAD>1"

df_material_cantidad["detalle"] = (
    df_material_cantidad["material"].astype(str)
    + "="
    + df_material_cantidad["cantidad"].astype(str)
)

print(
    f"🚨 Materiales con cantidad > 1 encontrados: "
    f"{len(df_material_cantidad)}"
)

# ============================================================
# HOJA NUEVA: ALERTA_RURAL_URBANO
#
# RESPONSABILIDAD EXCLUSIVA:
# Validar correspondencia entre:
#   urbrur
#   item_cont
#
# Regla:
# - urbrur = R -> item_cont debe terminar en R
# - urbrur = U -> item_cont debe terminar en U
#
# Esta hoja NO valida actividades.
# ============================================================

def validar_correspondencia_rural_urbano(df_export_in):

    columnas_salida = [
        "pedido",
        "subzona",
        "urbrur",
        "item_cont",
        "terminacion_item",
        "estado",
        "detalle",
    ]

    columnas_requeridas = {
        "pedido",
        "subz",
        "urbrur",
        "item_cont",
    }

    columnas_faltantes = (
        columnas_requeridas
        - set(df_export_in.columns)
    )

    if columnas_faltantes:
        print(
            "⚠️ No se pudo ejecutar ALERTA_RURAL_URBANO. "
            f"Faltan columnas: {sorted(columnas_faltantes)}"
        )

        return pd.DataFrame(
            columns=columnas_salida
        )

    df_ru = df_export_in[
        [
            "pedido",
            "subz",
            "urbrur",
            "item_cont",
        ]
    ].copy()

    # ---------------------------------------------
    # Normalizar
    # ---------------------------------------------

    df_ru["urbrur"] = (
        df_ru["urbrur"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df_ru["item_cont"] = (
        df_ru["item_cont"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    # ---------------------------------------------
    # Solo códigos que comiencen con letra
    # ---------------------------------------------

    mask_inicia_letra = (
        df_ru["item_cont"]
        .str.match(r"^[A-Z]", na=False)
    )

    mask_ru_valido = (
        df_ru["urbrur"]
        .isin(["R", "U"])
    )

    df_ru = df_ru[
        mask_inicia_letra
        & mask_ru_valido
    ].copy()

    if df_ru.empty:
        return pd.DataFrame(
            columns=columnas_salida
        )

    # ---------------------------------------------
    # Última letra
    # ---------------------------------------------

    df_ru["terminacion_item"] = (
        df_ru["item_cont"]
        .str[-1]
    )

    # ---------------------------------------------
    # Solo validar terminaciones U o R
    # Excluir A, P y cualquier otra terminación
    # ---------------------------------------------

    df_ru = df_ru[
        df_ru["terminacion_item"].isin([
            "U",
            "R"
        ])
    ].copy()

    if df_ru.empty:
        return pd.DataFrame(
            columns=columnas_salida
        )

    # ---------------------------------------------
    # Detectar inconsistencia
    # ---------------------------------------------

    mask_inconsistente = (
        (
            df_ru["urbrur"].eq("R")
            & ~df_ru["terminacion_item"].eq("R")
        )
        |
        (
            df_ru["urbrur"].eq("U")
            & ~df_ru["terminacion_item"].eq("U")
        )
    )

    df_alerta_ru = df_ru[
        mask_inconsistente
    ].copy()

    if df_alerta_ru.empty:
        return pd.DataFrame(
            columns=columnas_salida
        )

    df_alerta_ru["estado"] = (
        "INCONSISTENCIA_RURAL_URBANO"
    )

    def construir_detalle(fila):

        clasificacion = fila["urbrur"]
        item = fila["item_cont"]
        terminacion = fila["terminacion_item"]

        if clasificacion == "R":
            esperado = "R"
            tipo_zona = "RURAL"
        else:
            esperado = "U"
            tipo_zona = "URBANO"

        return (
            f"Zona {tipo_zona}: el código {item} "
            f"termina en {terminacion} y debería terminar en {esperado}"
        )

    df_alerta_ru["detalle"] = (
        df_alerta_ru.apply(
            construir_detalle,
            axis=1
        )
    )

    df_alerta_ru = (
        df_alerta_ru
        .rename(
            columns={
                "subz": "subzona"
            }
        )
        .sort_values(
            by=[
                "subzona",
                "pedido",
                "item_cont",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )

    return df_alerta_ru[
        columnas_salida
    ]


df_alerta_rural_urbano = (
    validar_correspondencia_rural_urbano(
        df_export
    )
)

print(
    "🚨 Inconsistencias Rural/Urbano encontradas: "
    f"{len(df_alerta_rural_urbano)}"
)


# ============================================================
# HOJA NUEVA: ALERTA_ACTIVIDADES
#
# RESPONSABILIDAD EXCLUSIVA:
# Validar reglas específicas por actividad.
#
# AMRTR:
#   - Debe tener D04U o D04R
#   - Debe tener D02U o D02R
#   - Debe tener D03U o D03R
#   - Cualquier otro D genera alerta
#
# ACREV:
#   - Debe tener D01U Y D01R
#   - Cualquier otro D genera alerta
#
# ACAMN y ALECA:
#   - Deben tener C05U o C05R
#   - Cualquier item_cont diferente genera alerta
#
# ALEGA y ALEGN:
#   - Deben tener uno de C01U/R, C02U/R, C03U/R o C04U/R
#   - Cualquier item_cont diferente genera alerta
#
# AEJDO:
#   - Debe tener:
#       CALE1F
#       A12U o A12R
#       A18U o A18R
#       A19U o A19R
#
# Esta hoja NO valida Rural/Urbano.
# ============================================================

def validar_reglas_actividades(df_export_in):

    columnas_salida = [
        "pedido",
        "subzona",
        "actividad",
        "tipo_alerta",
        "items_encontrados",
        "items_faltantes",
        "items_no_permitidos",
        "detalle",
    ]

    columnas_requeridas = {
        "pedido",
        "subz",
        "actividad",
        "item_cont",
        "item_res",
    }

    columnas_faltantes = (
        columnas_requeridas
        - set(df_export_in.columns)
    )

    if columnas_faltantes:
        print(
            "⚠️ No se pudo ejecutar ALERTA_ACTIVIDADES. "
            f"Faltan columnas: {sorted(columnas_faltantes)}"
        )

        return pd.DataFrame(
            columns=columnas_salida
        )

    df = df_export_in.copy()

    for columna in [
        "pedido",
        "subz",
        "actividad",
        "item_cont",
        "item_res",
    ]:
        df[columna] = (
            df[columna]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
        )

    resultados = []

    for (pedido, subzona, actividad), grupo in df.groupby(
        ["pedido", "subz", "actividad"]
    ):

        items_cont = {
            x for x in grupo["item_cont"]
            if x
        }

        items_res = {
            x for x in grupo["item_res"]
            if x
        }

        # ====================================================
        # AMRTR
        #
        # Códigos válidos:
        # D02U, D02R, D03U, D03R, D04U, D04R
        #
        # Reglas:
        # - Si tiene al menos uno válido -> cumple presencia
        # - Si no tiene ninguno -> FALTA ÍTEM VÁLIDO
        # - Si tiene otro Dxx -> ERROR EN DIGITACIÓN
        # ====================================================

        if actividad == "AMRTR":

            permitidos = {
                "D02U", "D02R",
                "D03U", "D03R",
                "D04U", "D04R",
            }

            items_d = {
                x for x in items_cont
                if x.startswith("D")
            }

            items_validos = sorted(
                items_d & permitidos
            )

            no_permitidos = sorted(
                items_d - permitidos
            )

            faltantes = []

            if not items_validos:
                faltantes.append(
                    "D02U/D02R o D03U/D03R o D04U/D04R"
                )

            if faltantes or no_permitidos:

                detalle = []

                if faltantes:
                    detalle.append(
                        "Falta ítem válido para AMRTR"
                    )

                if no_permitidos:
                    detalle.append(
                        "ERROR EN DIGITACIÓN: "
                        + ", ".join(no_permitidos)
                    )

                resultados.append({
                    "pedido": pedido,
                    "subzona": subzona,
                    "actividad": actividad,
                    "tipo_alerta": (
                        "ERROR EN DIGITACIÓN"
                        if no_permitidos
                        else "FALTA ÍTEM VÁLIDO"
                    ),
                    "items_encontrados": ", ".join(
                        sorted(items_d)
                    ),
                    "items_faltantes": ", ".join(
                        faltantes
                    ),
                    "items_no_permitidos": ", ".join(
                        no_permitidos
                    ),
                    "detalle": " | ".join(
                        detalle
                    ),
                })

        # ====================================================
        # ACREV
        #
        # Códigos válidos:
        # D01U o D01R
        #
        # Reglas:
        # - Si tiene uno de los dos -> cumple presencia
        # - Si no tiene ninguno -> FALTA ÍTEM VÁLIDO
        # - Si tiene otro Dxx -> ERROR EN DIGITACIÓN
        # ====================================================

        elif actividad == "ACREV":

            permitidos = {
                "D01U",
                "D01R",
            }

            items_d = {
                x for x in items_cont
                if x.startswith("D")
            }

            items_validos = sorted(
                items_d & permitidos
            )

            no_permitidos = sorted(
                items_d - permitidos
            )

            faltantes = []

            if not items_validos:
                faltantes.append(
                    "D01U o D01R"
                )

            if faltantes or no_permitidos:

                detalle = []

                if faltantes:
                    detalle.append(
                        "Falta ítem válido para ACREV"
                    )

                if no_permitidos:
                    detalle.append(
                        "ERROR EN DIGITACIÓN: "
                        + ", ".join(no_permitidos)
                    )

                resultados.append({
                    "pedido": pedido,
                    "subzona": subzona,
                    "actividad": actividad,
                    "tipo_alerta": (
                        "ERROR EN DIGITACIÓN"
                        if no_permitidos
                        else "FALTA ÍTEM VÁLIDO"
                    ),
                    "items_encontrados": ", ".join(
                        sorted(items_d)
                    ),
                    "items_faltantes": ", ".join(
                        faltantes
                    ),
                    "items_no_permitidos": ", ".join(
                        no_permitidos
                    ),
                    "detalle": " | ".join(
                        detalle
                    ),
                })

        # ====================================================
        # ACAMN / ALECA
        # Código obligatorio válido: C05U o C05R
        # ====================================================

        elif actividad in {"ACAMN", "ALECA"}:

            permitidos = {
                "C05U",
                "C05R",
            }

            items_validos = sorted(
                items_cont & permitidos
            )

            no_permitidos = sorted(
                items_cont - permitidos
            )

            faltantes = []

            if not items_validos:
                faltantes.append(
                    "C05U o C05R"
                )

            if faltantes or no_permitidos:

                detalle = []

                if faltantes:
                    detalle.append(
                        f"Falta ítem válido para {actividad}"
                    )

                if no_permitidos:
                    detalle.append(
                        "ERROR EN DIGITACIÓN: "
                        + ", ".join(no_permitidos)
                    )

                resultados.append({
                    "pedido": pedido,
                    "subzona": subzona,
                    "actividad": actividad,
                    "tipo_alerta": (
                        "ERROR EN DIGITACIÓN"
                        if no_permitidos
                        else "FALTA ÍTEM VÁLIDO"
                    ),
                    "items_encontrados": ", ".join(
                        sorted(items_cont)
                    ),
                    "items_faltantes": ", ".join(
                        faltantes
                    ),
                    "items_no_permitidos": ", ".join(
                        no_permitidos
                    ),
                    "detalle": " | ".join(
                        detalle
                    ),
                })

        # ====================================================
        # ALEGA / ALEGN
        # Debe existir uno de C01-C04, en versión U o R
        # ====================================================

        elif actividad in {"ALEGA", "ALEGN"}:

            permitidos = {
                "C01U", "C01R",
                "C02U", "C02R",
                "C03U", "C03R",
                "C04U", "C04R",
            }

            items_validos = sorted(
                items_cont & permitidos
            )

            no_permitidos = sorted(
                items_cont - permitidos
            )

            faltantes = []

            if not items_validos:
                faltantes.append(
                    "C01U/C01R o C02U/C02R o "
                    "C03U/C03R o C04U/C04R"
                )

            if faltantes or no_permitidos:

                detalle = []

                if faltantes:
                    detalle.append(
                        f"Falta ítem válido para {actividad}"
                    )

                if no_permitidos:
                    detalle.append(
                        "ERROR EN DIGITACIÓN: "
                        + ", ".join(no_permitidos)
                    )

                resultados.append({
                    "pedido": pedido,
                    "subzona": subzona,
                    "actividad": actividad,
                    "tipo_alerta": (
                        "ERROR EN DIGITACIÓN"
                        if no_permitidos
                        else "FALTA ÍTEM VÁLIDO"
                    ),
                    "items_encontrados": ", ".join(
                        sorted(items_cont)
                    ),
                    "items_faltantes": ", ".join(
                        faltantes
                    ),
                    "items_no_permitidos": ", ".join(
                        no_permitidos
                    ),
                    "detalle": " | ".join(
                        detalle
                    ),
                })

        # ====================================================
        # AEJDO
        # ====================================================

        elif actividad == "AEJDO":

            # Cada grupo A acepta su variante urbana o rural.
            # Solo se considera faltante cuando no aparece
            # ninguna de las dos alternativas del grupo.
            requisitos = [
                ("CALE1F", {"CALE1F"}),
                ("A12U/A12R", {"A12U", "A12R"}),
                ("A18U/A18R", {"A18U", "A18R"}),
                ("A19U/A19R", {"A19U", "A19R"}),
            ]

            faltantes = []
            encontrados = []

            for etiqueta, alternativas in requisitos:

                presentes = sorted(
                    items_res & alternativas
                )

                if presentes:
                    encontrados.extend(
                        presentes
                    )
                else:
                    faltantes.append(
                        etiqueta
                    )

            if faltantes:

                resultados.append({
                    "pedido": pedido,
                    "subzona": subzona,
                    "actividad": actividad,
                    "tipo_alerta": "REGLA_AEJDO",
                    "items_encontrados": ", ".join(
                        encontrados
                    ),
                    "items_faltantes": ", ".join(
                        faltantes
                    ),
                    "items_no_permitidos": "",
                    "detalle": (
                        "AEJDO no tiene todos los ítems obligatorios. "
                        "Faltan: "
                        + ", ".join(faltantes)
                    ),
                })

    if not resultados:
        return pd.DataFrame(
            columns=columnas_salida
        )

    return pd.DataFrame(
        resultados,
        columns=columnas_salida
    )


df_alerta_actividades = (
    validar_reglas_actividades(
        df_export
    )
)

print(
    "🚨 Alertas por actividad encontradas: "
    f"{len(df_alerta_actividades)}"
)

# ============================================================
# HOJA NUEVA: LEGALIZACION_NO_COBRO
#
# RESPONSABILIDAD EXCLUSIVA:
# Identificar cobros al cliente que no están permitidos para
# determinados suministros de actividades de legalización.
#
# Regla:
# - actividad = ACAMN, ALECA, ALEGA o ALEGN
# - tipo = SUM
# - item_res = 215887A o 219404A
# - vlr_cliente diferente de 0 -> ALERTA
#
# Esta alerta es independiente de las demás validaciones.
# ============================================================

def validar_legalizacion_no_cobro(df_export_in):

    columnas_salida = [
        "pedido",
        "subzona",
        "actividad",
        "item_res",
        "cantidad",
        "vlr_cliente",
        "tipo_alerta",
        "detalle",
    ]

    columnas_requeridas = {
        "pedido",
        "subz",
        "actividad",
        "tipo",
        "item_res",
        "cantidad",
        "vlr_cliente",
    }

    columnas_faltantes = (
        columnas_requeridas
        - set(df_export_in.columns)
    )

    if columnas_faltantes:
        print(
            "⚠️ No se pudo ejecutar LEGALIZACION_NO_COBRO. "
            f"Faltan columnas: {sorted(columnas_faltantes)}"
        )

        return pd.DataFrame(
            columns=columnas_salida
        )

    df = df_export_in.copy()

    for columna in [
        "pedido",
        "subz",
        "actividad",
        "tipo",
        "item_res",
    ]:
        df[columna] = (
            df[columna]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
        )

    def convertir_valor_cliente(valor):
        if pd.isna(valor):
            return 0.0

        texto = (
            str(valor)
            .strip()
            .replace("$", "")
            .replace(" ", "")
        )

        if texto.upper() in {"", "NAN", "NONE"}:
            return 0.0

        if "," in texto and "." in texto:
            if texto.rfind(",") > texto.rfind("."):
                texto = texto.replace(".", "").replace(",", ".")
            else:
                texto = texto.replace(",", "")
        elif "," in texto:
            texto = texto.replace(",", ".")

        try:
            return float(texto)
        except ValueError:
            return 0.0

    df["VLR_CLIENTE_NUM"] = df["vlr_cliente"].apply(
        convertir_valor_cliente
    )

    actividades_controladas = {
        "ACAMN",
        "ALECA",
        "ALEGA",
        "ALEGN",
    }

    suministros_sin_cobro = {
        "215887A",
        "219404A",
    }

    df_alerta = df[
        df["actividad"].isin(actividades_controladas)
        & df["tipo"].eq("SUM")
        & df["item_res"].isin(suministros_sin_cobro)
        & df["VLR_CLIENTE_NUM"].ne(0)
    ].copy()

    if df_alerta.empty:
        return pd.DataFrame(
            columns=columnas_salida
        )

    df_alerta["vlr_cliente"] = df_alerta["VLR_CLIENTE_NUM"]
    df_alerta["tipo_alerta"] = "COBRO_NO_PERMITIDO"

    df_alerta["detalle"] = df_alerta.apply(
        lambda r: (
            f"El suministro {r['item_res']} de la actividad "
            f"{r['actividad']} no debe llevar cobro al cliente. "
            f"Se encontró vlr_cliente={r['VLR_CLIENTE_NUM']:g}."
        ),
        axis=1
    )

    df_alerta = (
        df_alerta
        .rename(columns={"subz": "subzona"})
        .sort_values(
            by=[
                "subzona",
                "pedido",
                "actividad",
                "item_res",
            ],
            kind="stable"
        )
        .reset_index(drop=True)
    )

    return df_alerta[
        columnas_salida
    ]


df_legalizacion_no_cobro = (
    validar_legalizacion_no_cobro(
        df_export
    )
)

print(
    "🚨 Alertas de legalización con cobro encontradas: "
    f"{len(df_legalizacion_no_cobro)}"
)

# ============================================================
# HOJA NUEVA: ALERTA_CANTIDADES_MO
#
# RESPONSABILIDAD EXCLUSIVA:
# Identificar cantidades mayores a 1 en manos de obra.
#
# Regla:
# - tipo = CON
# - item_cont comienza por A o C
# - o corresponde a D01-D04, en versión U o R
# - o corresponde a F01U o F01R
# - cantidad > 1 -> ALERTA
#
# La alerta requiere revisión del analista y no significa
# automáticamente que exista un error.
# ============================================================

def validar_alerta_cantidades_mo(df_export_in):

    columnas_salida = [
        "pedido",
        "subzona",
        "item_cont",
        "cantidad",
        "tipo_alerta",
        "detalle",
    ]

    columnas_requeridas = {
        "pedido",
        "subz",
        "tipo",
        "item_cont",
        "cantidad",
    }

    columnas_faltantes = (
        columnas_requeridas
        - set(df_export_in.columns)
    )

    if columnas_faltantes:
        print(
            "⚠️ No se pudo ejecutar ALERTA_CANTIDADES_MO. "
            f"Faltan columnas: {sorted(columnas_faltantes)}"
        )

        return pd.DataFrame(
            columns=columnas_salida
        )

    df = df_export_in.copy()

    df["pedido"] = (
        df["pedido"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["subz"] = (
        df["subz"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["tipo"] = (
        df["tipo"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["item_cont"] = (
        df["item_cont"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["CANT_NUM"] = pd.to_numeric(
        df["cantidad"]
        .fillna("")
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip(),
        errors="coerce"
    )

    # ========================================================
    # REGLA:
    # - Solo Mano de Obra: tipo = CON
    # - item_cont comienza por A o C
    # - o corresponde a D01-D04, en versión U o R
    # - o corresponde a F01U o F01R
    # - cantidad mayor a 1
    # ========================================================

    items_d_controlados = {
        "D01U", "D01R",
        "D02U", "D02R",
        "D03U", "D03R",
        "D04U", "D04R",
    }

    items_f_controlados = {"F01U", "F01R"}

    mask_mo_controlada = (
        df["item_cont"].str.startswith(("A", "C"))
        | df["item_cont"].isin(items_d_controlados)
        | df["item_cont"].isin(items_f_controlados)
    )

    df_alerta = df[
        df["tipo"].eq("CON")
        & mask_mo_controlada
        & (df["CANT_NUM"] > 1)
    ].copy()

    if df_alerta.empty:
        return pd.DataFrame(
            columns=columnas_salida
        )

    df_alerta["cantidad"] = df_alerta["CANT_NUM"]
    df_alerta["tipo_alerta"] = "CANTIDAD_MO>1"

    df_alerta["detalle"] = df_alerta.apply(
        lambda r: (
            f"La mano de obra {r['item_cont']} tiene cantidad "
            f"{r['CANT_NUM']:g}. Requiere revisión del analista."
        ),
        axis=1
    )

    df_alerta = (
        df_alerta
        .rename(columns={"subz": "subzona"})
        .sort_values(
            by=["subzona", "pedido", "item_cont"],
            kind="stable"
        )
        .reset_index(drop=True)
    )

    return df_alerta[
        columnas_salida
    ]


df_alerta_cantidades_mo = (
    validar_alerta_cantidades_mo(
        df_export
    )
)

print(
    "🚨 Alertas de cantidades de Mano de Obra encontradas: "
    f"{len(df_alerta_cantidades_mo)}"
)

# ============================================================
# HOJA NUEVA: MASIVAS
#
# RESPONSABILIDAD EXCLUSIVA:
# Validar que el item_cont corresponda a la cantidad de
# instalaciones agrupadas por pagina_base.
#
# Regla de negocio:
# - pagina_base = primeros 14 dígitos de pagina
# - 1 instalación: C01U o C01R
# - 2 a 12 instalaciones: C02U o C02R
# - 13 a 24 instalaciones: C03U o C03R
# - 25 instalaciones en adelante: C04U o C04R
# - U/R no cambia el rango correspondiente.
#
# Salida:
# pedido, subzona, pagina, pagina_base, cantidad_instalaciones,
# item_cont, items_encontrados, item_esperado, tipo_alerta, detalle
# ============================================================

def validar_masivas(df_export_in):

    columnas_salida = [
        "pedido",
        "subzona",
        "pagina",
        "pagina_base",
        "cantidad_instalaciones",
        "item_cont",
        "items_encontrados",
        "item_esperado",
        "tipo_alerta",
        "detalle",
    ]

    columnas_requeridas = {
        "pedido",
        "subz",
        "pagina",
        "item_cont",
    }

    columnas_faltantes = columnas_requeridas - set(df_export_in.columns)

    if columnas_faltantes:
        print(
            "⚠️ No se pudo ejecutar MASIVAS. "
            f"Faltan columnas: {sorted(columnas_faltantes)}"
        )
        return pd.DataFrame(columns=columnas_salida)

    df = df_export_in.copy()

    if "tipo" in df.columns:
        df["tipo"] = (
            df["tipo"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
        )
        df = df[df["tipo"].eq("CON")].copy()

    df["pedido"] = (
        df["pedido"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["subz"] = (
        df["subz"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["pagina"] = (
        df["pagina"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    df["item_cont"] = (
        df["item_cont"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    mask_pagina_valida = df["pagina"].str.match(r"^\d{14,}$", na=False)

    df = df[
        mask_pagina_valida
        & df["item_cont"].ne("")
    ].copy()

    if df.empty:
        return pd.DataFrame(columns=columnas_salida)

    # Extracción real de los primeros 14 dígitos
    df["pagina_base"] = df["pagina"].str[:14]

    items_controlados = {
        "C01U", "C01R",
        "C02U", "C02R",
        "C03U", "C03R",
        "C04U", "C04R",
    }

    claves_aplicables = set(
        df.loc[
            df["item_cont"].isin(items_controlados),
            ["subz", "pagina_base"]
        ].itertuples(index=False, name=None)
    )

    if not claves_aplicables:
        return pd.DataFrame(columns=columnas_salida)

    alertas_por_base = {}

    for (subzona, pagina_base), grupo in df.groupby(
        ["subz", "pagina_base"]
    ):
        clave = (subzona, pagina_base)

        if clave not in claves_aplicables:
            continue

        cantidad_instalaciones = int(
            grupo["pagina"].nunique()
        )

        if cantidad_instalaciones == 1:
            codigo_esperado = "C01"
        elif cantidad_instalaciones <= 12:
            codigo_esperado = "C02"
        elif cantidad_instalaciones <= 24:
            codigo_esperado = "C03"
        else:
            codigo_esperado = "C04"

        items_esperados = {
            f"{codigo_esperado}U",
            f"{codigo_esperado}R",
        }

        items_encontrados = {
            item
            for item in grupo["item_cont"]
            if item in items_controlados
        }

        items_no_corresponden = (
            items_encontrados - items_esperados
        )

        tiene_item_esperado = bool(
            items_encontrados & items_esperados
        )

        if items_no_corresponden or not tiene_item_esperado:
            alertas_por_base[clave] = {
                "cantidad_instalaciones": cantidad_instalaciones,
                "items_encontrados": ", ".join(
                    sorted(items_encontrados)
                ),
                "item_esperado": (
                    f"{codigo_esperado}U o {codigo_esperado}R"
                ),
            }

    if not alertas_por_base:
        return pd.DataFrame(columns=columnas_salida)

    mask_alerta = df.apply(
        lambda r: (
            r["subz"],
            r["pagina_base"]
        ) in alertas_por_base,
        axis=1
    )

    df_alerta = df[
        mask_alerta
        & df["item_cont"].isin(items_controlados)
    ].copy()

    def obtener_dato_alerta(fila, campo):
        return alertas_por_base[
            (fila["subz"], fila["pagina_base"])
        ][campo]

    df_alerta["cantidad_instalaciones"] = df_alerta.apply(
        lambda r: obtener_dato_alerta(
            r,
            "cantidad_instalaciones"
        ),
        axis=1
    )

    df_alerta["items_encontrados"] = df_alerta.apply(
        lambda r: obtener_dato_alerta(
            r,
            "items_encontrados"
        ),
        axis=1
    )

    df_alerta["item_esperado"] = df_alerta.apply(
        lambda r: obtener_dato_alerta(
            r,
            "item_esperado"
        ),
        axis=1
    )

    df_alerta["tipo_alerta"] = (
        "ITEM_CONT_NO_CORRESPONDE_CANTIDAD"
    )

    df_alerta["detalle"] = df_alerta.apply(
        lambda r: (
            f"La página base {r['pagina_base']} agrupa "
            f"{r['cantidad_instalaciones']} instalación(es). "
            f"Se encontró {r['items_encontrados']} y corresponde "
            f"usar {r['item_esperado']}, independientemente "
            "de que sea urbano o rural."
        ),
        axis=1
    )

    df_alerta = (
        df_alerta
        .rename(columns={"subz": "subzona"})
        .sort_values(
            by=[
                "subzona",
                "pagina_base",
                "pagina",
                "pedido",
                "item_cont",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )

    return df_alerta[columnas_salida]


df_masivas = validar_masivas(df_export)

print(
    "🚨 Alertas MASIVAS encontradas: "
    f"{len(df_masivas)}"
)


# ============================================================
# EXPORTAR RESULTADO
# ============================================================

ruta_salida = BASE_DIR / "outputs"
ruta_salida.mkdir(exist_ok=True)

archivo = ruta_salida / f"validacion_mo_materiales_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
with pd.ExcelWriter(
    archivo,
    engine="openpyxl"
) as writer:

    df_resultado.to_excel(
        writer,
        sheet_name="VALIDACION",
        index=False
    )

    df_mo_duplicadas.to_excel(
        writer,
        sheet_name="MO_DUPLICADAS",
        index=False
    )

    df_material_cantidad.to_excel(
        writer,
        sheet_name="ALERTA_CANTIDADES",
        index=False
    )

    df_alerta_rural_urbano.to_excel(
        writer,
        sheet_name="ALERTA_RURAL_URBANO",
        index=False
    )

    df_alerta_actividades.to_excel(
        writer,
        sheet_name="ALERTA_ACTIVIDADES",
        index=False
        )

    df_legalizacion_no_cobro.to_excel(
        writer,
        sheet_name="LEGALIZACION_NO_COBRO",
        index=False
    )

    df_alerta_cantidades_mo.to_excel(
        writer,
        sheet_name="ALERTA_CANTIDADES_MO",
        index=False
    )

    df_masivas.to_excel(
        writer,
        sheet_name="MASIVAS",
        index=False
    )
# ============================================================
# FORMATO PROFESIONAL DEL EXCEL (NO TOCA LÓGICA)
# ============================================================

wb = load_workbook(archivo)

if "MO_DUPLICADAS" in wb.sheetnames:
    wb["MO_DUPLICADAS"].sheet_properties.tabColor = "C00000"

if "ALERTA_CANTIDADES" in wb.sheetnames:
    wb["ALERTA_CANTIDADES"].sheet_properties.tabColor = "FFC000"

if "ALERTA_RURAL_URBANO" in wb.sheetnames:
    wb[
        "ALERTA_RURAL_URBANO"
    ].sheet_properties.tabColor = "7030A0"

if "ALERTA_ACTIVIDADES" in wb.sheetnames:
    wb[
        "ALERTA_ACTIVIDADES"
    ].sheet_properties.tabColor = "0070C0"

if "LEGALIZACION_NO_COBRO" in wb.sheetnames:
    wb[
        "LEGALIZACION_NO_COBRO"
    ].sheet_properties.tabColor = "595959"

if "ALERTA_CANTIDADES_MO" in wb.sheetnames:
    wb[
        "ALERTA_CANTIDADES_MO"
    ].sheet_properties.tabColor = "00B050"

if "MASIVAS" in wb.sheetnames:
    wb[
        "MASIVAS"
    ].sheet_properties.tabColor = "5B9BD5"

ws = wb["VALIDACION"]

ws.freeze_panes = "A2"
ws.auto_filter.ref = ws.dimensions

header_fill = PatternFill("solid", fgColor="1E8449")
header_font = Font(color="FFFFFF", bold=True)  # 👈 más pro
header_align = Alignment(horizontal="center", vertical="center")

for cell in ws[1]:
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = header_align

headers = {cell.value: idx + 1 for idx, cell in enumerate(ws[1])}

# --- Pintar en rojo detalle_cantidad_C cuando haya alerta_cantidad_C
col_alerta_c = headers.get("alerta_cantidad_C")
col_detalle_c = headers.get("detalle_cantidad_C")

if col_alerta_c and col_detalle_c:
    fill_rojo = PatternFill("solid", fgColor="FF0000")
    font_blanco = Font(color="FFFFFF", bold=True)

    for r in range(2, ws.max_row + 1):
        v_alerta = ws.cell(row=r, column=col_alerta_c).value
        if str(v_alerta).strip().upper() == "CANTIDAD>1":
            c = ws.cell(row=r, column=col_detalle_c)
            c.fill = fill_rojo
            c.font = font_blanco

# --- Pintar en rojo detalle_duplicado_MO cuando haya MO_DUPLICADA
col_alerta_dup = headers.get("alerta_duplicado_MO")
col_detalle_dup = headers.get("detalle_duplicado_MO")

if col_alerta_dup and col_detalle_dup:
    fill_rojo = PatternFill("solid", fgColor="FF0000")
    font_blanco = Font(color="FFFFFF", bold=True)

    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=col_alerta_dup).value
        if str(v).strip().upper() == "MO_DUPLICADA":
            c = ws.cell(row=r, column=col_detalle_dup)
            c.fill = fill_rojo
            c.font = font_blanco

# --- Pintar en rojo detalle_cantidad_A cuando haya CANTIDAD_A>1
col_alerta_a = headers.get("alerta_cantidad_A")
col_detalle_a = headers.get("detalle_cantidad_A")

if col_alerta_a and col_detalle_a:
    fill_rojo = PatternFill("solid", fgColor="FF0000")
    font_blanco = Font(color="FFFFFF", bold=True)

    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=col_alerta_a).value
        if str(v).strip().upper() == "CANTIDAD_A>1":
            c = ws.cell(row=r, column=col_detalle_a)
            c.fill = fill_rojo
            c.font = font_blanco

# --- Pintar en rojo detalle_cantidad_D cuando haya CANTIDAD_D>1
col_alerta_d = headers.get("alerta_cantidad_D")
col_detalle_d = headers.get("detalle_cantidad_D")

if col_alerta_d and col_detalle_d:
    fill_rojo = PatternFill("solid", fgColor="FF0000")
    font_blanco = Font(color="FFFFFF", bold=True)

    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=col_alerta_d).value
        if str(v).strip().upper() == "CANTIDAD_D>1":
            c = ws.cell(row=r, column=col_detalle_d)
            c.fill = fill_rojo
            c.font = font_blanco

# --- Pintar en rojo detalle_cantidad_F cuando haya CANTIDAD_F>1
col_alerta_f = headers.get("alerta_cantidad_F")
col_detalle_f = headers.get("detalle_cantidad_F")

if col_alerta_f and col_detalle_f:
    fill_rojo = PatternFill("solid", fgColor="FF0000")
    font_blanco = Font(color="FFFFFF", bold=True)

    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=col_alerta_f).value
        if str(v).strip().upper() == "CANTIDAD_F>1":
            c = ws.cell(row=r, column=col_detalle_f)
            c.fill = fill_rojo
            c.font = font_blanco

# --- Pintar en rojo TODA LA FILA cuando haya CONFLICTO_A31
col_estado_codigo = headers.get("estado_codigo")

if col_estado_codigo:
    fill_rojo = PatternFill("solid", fgColor="FF0000")
    font_blanco = Font(color="FFFFFF", bold=True)

    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=col_estado_codigo).value
        if str(v).strip().upper() == "REVISAR_A31":
            for c in range(1, ws.max_column + 1):
                cell = ws.cell(row=r, column=c)
                cell.fill = fill_rojo
                cell.font = font_blanco

for col in ws.columns:
    max_length = 0
    col_letter = get_column_letter(col[0].column)

    for cell in col:
        if cell.value:
            max_length = max(max_length, len(str(cell.value)))

    ws.column_dimensions[col_letter].width = min(max_length + 3, 45)

for row in ws.iter_rows(min_row=2):
    row[0].alignment = Alignment(horizontal="center")
    row[1].alignment = Alignment(horizontal="center")
    row[2].alignment = Alignment(horizontal="left")
    row[3].alignment = Alignment(horizontal="left")
    row[4].alignment = Alignment(wrap_text=True)
    row[5].alignment = Alignment(wrap_text=True)
# ============================================================
# FORMATO HOJA MO_DUPLICADAS
# ============================================================

if "MO_DUPLICADAS" in wb.sheetnames:

    ws_dup = wb["MO_DUPLICADAS"]

    # Congelar encabezado
    ws_dup.freeze_panes = "A2"

    # Filtro
    ws_dup.auto_filter.ref = ws_dup.dimensions

    # Encabezado rojo
    fill_rojo = PatternFill(
        "solid",
        fgColor="C00000"
    )

    font_blanco = Font(
        color="FFFFFF",
        bold=True
    )

    align_center = Alignment(
        horizontal="center",
        vertical="center"
    )

    for cell in ws_dup[1]:
        cell.fill = fill_rojo
        cell.font = font_blanco
        cell.alignment = align_center

    # Pintar filas de alerta
    fill_alerta = PatternFill(
        "solid",
        fgColor="FDE9E7"
    )

    for fila in ws_dup.iter_rows(
        min_row=2,
        max_row=ws_dup.max_row,
        min_col=1,
        max_col=ws_dup.max_column
    ):
        for celda in fila:
            celda.fill = fill_alerta

    # Ajustar ancho columnas
    for col in ws_dup.columns:

        max_length = 0

        letra = get_column_letter(
            col[0].column
        )

        for cell in col:
            if cell.value:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        ws_dup.column_dimensions[
            letra
        ].width = min(
            max_length + 5,
            40
        )
# ============================================================
# FORMATO HOJA MATERIAL_CANTIDAD
# ============================================================

if "ALERTA_CANTIDADES" in wb.sheetnames:

    ws_mat = wb["ALERTA_CANTIDADES"]

    ws_mat.freeze_panes = "A2"
    ws_mat.auto_filter.ref = ws_mat.dimensions

    fill_naranja = PatternFill(
        "solid",
        fgColor="FFC000"
    )

    font_negro = Font(
        color="000000",
        bold=True
    )

    align_center = Alignment(
        horizontal="center",
        vertical="center"
    )

    for cell in ws_mat[1]:
        cell.fill = fill_naranja
        cell.font = font_negro
        cell.alignment = align_center

    fill_alerta_mat = PatternFill(
        "solid",
        fgColor="FFF2CC"
    )

    for fila in ws_mat.iter_rows(
        min_row=2,
        max_row=ws_mat.max_row,
        min_col=1,
        max_col=ws_mat.max_column
    ):
        for celda in fila:
            celda.fill = fill_alerta_mat

    for col in ws_mat.columns:

        max_length = 0
        letra = get_column_letter(col[0].column)

        for cell in col:
            if cell.value:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        ws_mat.column_dimensions[letra].width = min(
            max_length + 5,
            40
        )
        # ==========================
        # BARRAS DE DATOS
        # ==========================

        encabezados = {
            cell.value: idx + 1
            for idx, cell in enumerate(ws_mat[1])
        }

        col_cantidad = encabezados.get("cantidad")

        if col_cantidad:

            letra = get_column_letter(col_cantidad)

            regla = DataBarRule(
                start_type="min",
                end_type="max",
                color="FF6B6B",
                showValue=True
            )

            ws_mat.conditional_formatting.add(
                f"{letra}2:{letra}{ws_mat.max_row}",
                regla
            )

# ============================================================
# FORMATO HOJA ALERTA_RURAL_URBANO
# ============================================================

if "ALERTA_RURAL_URBANO" in wb.sheetnames:

    ws_ru = wb["ALERTA_RURAL_URBANO"]

    ws_ru.freeze_panes = "A2"
    ws_ru.auto_filter.ref = ws_ru.dimensions

    fill_morado = PatternFill(
        "solid",
        fgColor="7030A0"
    )

    font_blanco = Font(
        color="FFFFFF",
        bold=True
    )

    align_center = Alignment(
        horizontal="center",
        vertical="center"
    )

    for cell in ws_ru[1]:
        cell.fill = fill_morado
        cell.font = font_blanco
        cell.alignment = align_center

    fill_alerta_ru = PatternFill(
        "solid",
        fgColor="E4DFEC"
    )

    for fila in ws_ru.iter_rows(
        min_row=2,
        max_row=ws_ru.max_row,
        min_col=1,
        max_col=ws_ru.max_column
    ):
        for celda in fila:
            celda.fill = fill_alerta_ru

    # Resaltar específicamente el código inconsistente
    encabezados_ru = {
        cell.value: idx + 1
        for idx, cell in enumerate(ws_ru[1])
    }

    col_item_cont = encabezados_ru.get(
        "item_cont"
    )

    if col_item_cont:

        fill_rojo = PatternFill(
            "solid",
            fgColor="C00000"
        )

        for fila in range(
            2,
            ws_ru.max_row + 1
        ):
            celda = ws_ru.cell(
                row=fila,
                column=col_item_cont
            )

            celda.fill = fill_rojo
            celda.font = font_blanco

    # Ajustar anchos
    for columna in ws_ru.columns:

        max_length = 0
        letra = get_column_letter(
            columna[0].column
        )

        for cell in columna:
            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        ws_ru.column_dimensions[
            letra
        ].width = min(
            max_length + 5,
            70
        )

    # Ajustes de alineación
    for fila in ws_ru.iter_rows(
        min_row=2
    ):
        fila[0].alignment = align_center
        fila[1].alignment = align_center
        fila[2].alignment = align_center
        fila[3].alignment = align_center
        fila[4].alignment = align_center

        if len(fila) > 6:
            fila[6].alignment = Alignment(
                vertical="center",
                wrap_text=True
            )

# ============================================================
# FORMATO HOJA ALERTA_ACTIVIDADES
# ============================================================

if "ALERTA_ACTIVIDADES" in wb.sheetnames:

    ws_act = wb["ALERTA_ACTIVIDADES"]

    ws_act.freeze_panes = "A2"
    ws_act.auto_filter.ref = ws_act.dimensions

    fill_azul = PatternFill(
        "solid",
        fgColor="0070C0"
    )

    font_blanco = Font(
        color="FFFFFF",
        bold=True
    )

    fill_alerta = PatternFill(
        "solid",
        fgColor="D9EAF7"
    )

    align_center = Alignment(
        horizontal="center",
        vertical="center"
    )

    for cell in ws_act[1]:
        cell.fill = fill_azul
        cell.font = font_blanco
        cell.alignment = align_center

    for fila in ws_act.iter_rows(
        min_row=2,
        max_row=ws_act.max_row,
        min_col=1,
        max_col=ws_act.max_column
    ):
        for celda in fila:
            celda.fill = fill_alerta

    encabezados_act = {
        cell.value: idx + 1
        for idx, cell in enumerate(ws_act[1])
    }

    col_no_permitidos = encabezados_act.get(
        "items_no_permitidos"
    )

    if col_no_permitidos:

        fill_rojo = PatternFill(
            "solid",
            fgColor="C00000"
        )

        for fila in range(
            2,
            ws_act.max_row + 1
        ):
            celda = ws_act.cell(
                row=fila,
                column=col_no_permitidos
            )

            if celda.value:
                celda.fill = fill_rojo
                celda.font = font_blanco

    for columna in ws_act.columns:

        max_length = 0
        letra = get_column_letter(
            columna[0].column
        )

        for cell in columna:
            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        ws_act.column_dimensions[
            letra
        ].width = min(
            max_length + 5,
            70
        )

    for fila in ws_act.iter_rows(
        min_row=2
    ):
        for celda in fila:
            celda.alignment = Alignment(
                vertical="center",
                wrap_text=True
            )


# ============================================================
# FORMATO HOJA LEGALIZACION_NO_COBRO
# ============================================================

if "LEGALIZACION_NO_COBRO" in wb.sheetnames:

    ws_cobro = wb["LEGALIZACION_NO_COBRO"]

    ws_cobro.freeze_panes = "A2"
    ws_cobro.auto_filter.ref = ws_cobro.dimensions

    fill_gris_oscuro = PatternFill(
        "solid",
        fgColor="595959"
    )

    font_blanco = Font(
        color="FFFFFF",
        bold=True
    )

    fill_gris_claro = PatternFill(
        "solid",
        fgColor="E7E6E6"
    )

    align_center = Alignment(
        horizontal="center",
        vertical="center"
    )

    for cell in ws_cobro[1]:
        cell.fill = fill_gris_oscuro
        cell.font = font_blanco
        cell.alignment = align_center

    for fila in ws_cobro.iter_rows(
        min_row=2,
        max_row=ws_cobro.max_row,
        min_col=1,
        max_col=ws_cobro.max_column
    ):
        for celda in fila:
            celda.fill = fill_gris_claro

    encabezados_cobro = {
        cell.value: idx + 1
        for idx, cell in enumerate(ws_cobro[1])
    }

    col_vlr_cliente = encabezados_cobro.get(
        "vlr_cliente"
    )

    if col_vlr_cliente:

        fill_rojo = PatternFill(
            "solid",
            fgColor="C00000"
        )

        for fila in range(
            2,
            ws_cobro.max_row + 1
        ):
            celda = ws_cobro.cell(
                row=fila,
                column=col_vlr_cliente
            )

            celda.fill = fill_rojo
            celda.font = font_blanco
            celda.number_format = '#,##0.00'

    for columna in ws_cobro.columns:

        max_length = 0
        letra = get_column_letter(
            columna[0].column
        )

        for cell in columna:
            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        ws_cobro.column_dimensions[
            letra
        ].width = min(
            max_length + 5,
            75
        )

    for fila in ws_cobro.iter_rows(
        min_row=2
    ):
        for celda in fila:
            celda.alignment = Alignment(
                vertical="center",
                wrap_text=True
            )


# ============================================================
# FORMATO HOJA ALERTA_CANTIDADES_MO
# ============================================================

if "ALERTA_CANTIDADES_MO" in wb.sheetnames:

    ws_leg = wb["ALERTA_CANTIDADES_MO"]

    ws_leg.freeze_panes = "A2"
    ws_leg.auto_filter.ref = ws_leg.dimensions

    fill_verde = PatternFill(
        "solid",
        fgColor="00B050"
    )

    font_blanco = Font(
        color="FFFFFF",
        bold=True
    )

    fill_alerta_leg = PatternFill(
        "solid",
        fgColor="E2F0D9"
    )

    align_center = Alignment(
        horizontal="center",
        vertical="center"
    )

    for cell in ws_leg[1]:
        cell.fill = fill_verde
        cell.font = font_blanco
        cell.alignment = align_center

    for fila in ws_leg.iter_rows(
        min_row=2,
        max_row=ws_leg.max_row,
        min_col=1,
        max_col=ws_leg.max_column
    ):
        for celda in fila:
            celda.fill = fill_alerta_leg

    encabezados_leg = {
        cell.value: idx + 1
        for idx, cell in enumerate(ws_leg[1])
    }

    col_cantidad_leg = encabezados_leg.get(
        "cantidad"
    )

    if col_cantidad_leg:

        fill_rojo = PatternFill(
            "solid",
            fgColor="C00000"
        )

        for fila in range(
            2,
            ws_leg.max_row + 1
        ):
            celda = ws_leg.cell(
                row=fila,
                column=col_cantidad_leg
            )

            celda.fill = fill_rojo
            celda.font = font_blanco

    for columna in ws_leg.columns:

        max_length = 0
        letra = get_column_letter(
            columna[0].column
        )

        for cell in columna:
            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        ws_leg.column_dimensions[
            letra
        ].width = min(
            max_length + 5,
            70
        )

    for fila in ws_leg.iter_rows(
        min_row=2
    ):
        for celda in fila:
            celda.alignment = Alignment(
                vertical="center",
                wrap_text=True
            )



# ============================================================
# FORMATO HOJA MASIVAS
# ============================================================

if "MASIVAS" in wb.sheetnames:

    ws_mas = wb["MASIVAS"]

    ws_mas.freeze_panes = "A2"
    ws_mas.auto_filter.ref = ws_mas.dimensions

    fill_azul_mas = PatternFill(
        "solid",
        fgColor="5B9BD5"
    )

    font_blanco = Font(
        color="FFFFFF",
        bold=True
    )

    fill_alerta_mas = PatternFill(
        "solid",
        fgColor="DDEBF7"
    )

    align_center = Alignment(
        horizontal="center",
        vertical="center"
    )

    for cell in ws_mas[1]:
        cell.fill = fill_azul_mas
        cell.font = font_blanco
        cell.alignment = align_center

    for fila in ws_mas.iter_rows(
        min_row=2,
        max_row=ws_mas.max_row,
        min_col=1,
        max_col=ws_mas.max_column
    ):
        for celda in fila:
            celda.fill = fill_alerta_mas

    encabezados_mas = {
        cell.value: idx + 1
        for idx, cell in enumerate(ws_mas[1])
    }

    col_item_mas = encabezados_mas.get("item_cont")
    col_cantidad_mas = encabezados_mas.get(
        "cantidad_instalaciones"
    )
    col_esperado_mas = encabezados_mas.get(
        "item_esperado"
    )

    if col_item_mas:
        fill_rojo = PatternFill(
            "solid",
            fgColor="C00000"
        )

        for fila in range(2, ws_mas.max_row + 1):
            celda = ws_mas.cell(
                row=fila,
                column=col_item_mas
            )
            celda.fill = fill_rojo
            celda.font = font_blanco

    if col_cantidad_mas:
        fill_amarillo = PatternFill(
            "solid",
            fgColor="FFF2CC"
        )

        for fila in range(2, ws_mas.max_row + 1):
            celda = ws_mas.cell(
                row=fila,
                column=col_cantidad_mas
            )
            celda.fill = fill_amarillo
            celda.font = Font(
                color="000000",
                bold=True
            )

    if col_esperado_mas:
        fill_verde_claro = PatternFill(
            "solid",
            fgColor="E2F0D9"
        )

        for fila in range(2, ws_mas.max_row + 1):
            celda = ws_mas.cell(
                row=fila,
                column=col_esperado_mas
            )
            celda.fill = fill_verde_claro
            celda.font = Font(
                color="006100",
                bold=True
            )

    for columna in ws_mas.columns:

        max_length = 0
        letra = get_column_letter(columna[0].column)

        for cell in columna:
            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        ws_mas.column_dimensions[letra].width = min(
            max_length + 5,
            75
        )

    for fila in ws_mas.iter_rows(min_row=2):
        for celda in fila:
            celda.alignment = Alignment(
                vertical="center",
                wrap_text=True
            )


wb.save(archivo)

print(f"📁 Archivo generado: {archivo}")
