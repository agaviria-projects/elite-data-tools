import pandas as pd
from pathlib import Path
import re
import time
import argparse

# from openpyxl import load_workbook
# from openpyxl.worksheet.table import Table, TableStyleInfo
# from openpyxl.utils import get_column_letter

# ==============================
# RUTAS DEL PROYECTO
# ==============================

BASE_DIR = Path(__file__).resolve().parent

CARPETA_RAW = BASE_DIR / "ACTAS_RAW"
CARPETA_SALIDA = BASE_DIR / "UNIFICADAS"
ARCHIVO_SALIDA = CARPETA_SALIDA / "ACTAS_UNIFICADAS.xlsx"
CARPETA_CONFIG = BASE_DIR / "CONFIG"
ARCHIVO_CORRECCIONES = CARPETA_CONFIG / "correcciones_pedidos.xlsx"

HOJA_OBJETIVO = "Extracción Acta"


# ==============================
# FUNCIONES AUXILIARES
# ==============================

def extraer_numero_acta(nombre_carpeta):
    """
    Extrae el número de ACTA desde carpetas como:
    ACTA 5, ACTA 8, ACTA 9
    """
    match = re.search(r"ACTA\s*(\d+)", nombre_carpeta.upper())
    return int(match.group(1)) if match else None


def limpiar_nombre_columna(columna):
    """
    Normaliza nombres de columnas:
    - quita espacios extremos
    - convierte a minúsculas
    - reemplaza espacios por _
    """
    return (
        str(columna)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace(".", "")
    )

def seleccionar_modo():

    while True:

        print("\n" + "=" * 60)
        print("             PROYECTO ACTAS")
        print("      Sistema de Consolidación de Actas")
        print("                 Versión 1.0")
        print("-" * 60)
        print("=" * 60)

        print("\nSeleccione el modo de ejecución:\n")

        print("[1] RECONSTRUIR")
        print("    • Procesa TODAS las actas.")
        print("    • Reemplaza completamente el histórico.")
        print("    • Genera nuevamente ACTAS_UNIFICADAS.xlsx.")
        print("    • Recomendado cuando cambien reglas de negocio.\n")

        print("[2] ANEXAR")
        print("    • Conserva el histórico existente.")
        print("    • Solo agrega ACTAS + ZONAS nuevas.")
        print("    • Omite automáticamente las ya consolidadas.")
        print("    • Recomendado para la operación diaria.\n")

        print("[0] Cancelar\n")

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":

            confirmar = input(
                "\n⚠️ Se reconstruirá completamente el histórico.\n"
                "¿Desea continuar? (S/N): "
            ).strip().upper()

            if confirmar == "S":

                print("\n" + "=" * 60)
                print("Modo seleccionado : RECONSTRUIR")
                print("=" * 60)
                print("Se reconstruirá completamente el histórico.\n")

                input("Presione ENTER para iniciar el proceso...")

                return "RECONSTRUIR"

            print("\nOperación cancelada.\n")

        elif opcion == "2":

            print("\n" + "=" * 60)
            print("Modo seleccionado : ANEXAR")
            print("=" * 60)
            print("Se conservará el histórico existente.")
            print("Solo se agregarán ACTAS + ZONAS nuevas.\n")

            input("Presione ENTER para iniciar el proceso...")

            return "ANEXAR"

        elif opcion == "0":

            print("\nProceso cancelado por el usuario.")
            raise SystemExit

        else:

            print("\n❌ Opción inválida.\n")


def obtener_archivos_actas():
    """
    Busca todos los archivos Excel dentro de ACTAS_RAW,
    excluyendo archivos temporales de Excel.
    """
    archivos = [
        archivo
        for archivo in CARPETA_RAW.rglob("*.xlsx")
        if not archivo.name.startswith("~$")
    ]

    return sorted(archivos)

def obtener_actas_existentes():
    """
    Devuelve un conjunto con las combinaciones
    (ACTA, ZONA) que ya existen en el histórico.
    """

    if (
        MODO_EJECUCION != "ANEXAR"
        or not ARCHIVO_SALIDA.exists()
    ):
        return set()

    df = pd.read_excel(
        ARCHIVO_SALIDA,
        sheet_name="ACTAS_UNIFICADAS",
        usecols=["acta", "zona"],
        dtype=str
    )

    df = df.fillna("")

    return set(
        zip(
            df["acta"].astype(str).str.strip(),
            df["zona"].astype(str).str.upper().str.strip()
        )
    )
# ==============================
# ARGUMENTOS
# ==============================
import sys

def obtener_modo():

    print("=" * 60)
    print("ARGUMENTOS RECIBIDOS")
    print(sys.argv)
    print("=" * 60)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--modo",
        choices=["reconstruir", "anexar"],
        help="Modo de ejecución"
    )

    args = parser.parse_args()

    if args.modo:
        return args.modo.upper()

    return seleccionar_modo()

# ==============================
# PROCESO PRINCIPAL
# ==============================

def consolidar_actas():

    global MODO_EJECUCION

    MODO_EJECUCION = obtener_modo()

    inicio_total = time.perf_counter()

    print("=" * 60)
    print("INFORMACIÓN DEL PROCESO")
    print("=" * 60)

    print(f"Carpeta origen  : {CARPETA_RAW.name}")
    print(f"Carpeta salida  : {CARPETA_SALIDA.name}")
    print(f"Archivo destino : {ARCHIVO_SALIDA.name}")
    print(f"Modo            : {MODO_EJECUCION}")

    print("\n" + "=" * 60)
    print("Iniciando proceso...")
    print("=" * 60 + "\n")

    registros = []

    actas_existentes = obtener_actas_existentes()

    archivos_excel = obtener_archivos_actas()

    # =========================================================
    # CARGAR TABLA DE CORRECCIONES UNA SOLA VEZ
    # =========================================================

    df_correcciones = None

    if ARCHIVO_CORRECCIONES.exists():

        df_correcciones = pd.read_excel(
            ARCHIVO_CORRECCIONES,
            sheet_name="correcciones",
            dtype=str
        )

        df_correcciones["pedido_key"] = (
            df_correcciones["pedido"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
        )

    if not archivos_excel:
        print("❌ No se encontraron archivos Excel en ACTAS_RAW.")
        return

    for archivo in archivos_excel:

        try:
            partes = archivo.parts

            # Buscar carpeta ACTA
            carpeta_acta = None
            for parte in partes:
                if "ACTA " in parte.upper():
                    carpeta_acta = parte
                    break

            numero_acta = extraer_numero_acta(carpeta_acta) if carpeta_acta else None

            # Zona proveniente de la estructura de carpetas
            zona = archivo.parent.name.upper().strip()

            # Zona proveniente de la estructura de carpetas
            zona = archivo.parent.name.upper().strip()

            print(f"Procesando: ACTA {numero_acta} | {zona} | {archivo.name}")

            df = pd.read_excel(
                archivo,
                sheet_name=HOJA_OBJETIVO,
                dtype={
                    "pagina": str,
                    "Pagina": str,
                    "PAGINA": str,
                    "página": str,
                    "Página": str
                }
            )

            print(f"Procesando: ACTA {numero_acta} | {zona} | {archivo.name}")

            df = pd.read_excel(
                archivo,
                sheet_name=HOJA_OBJETIVO,
                dtype={
                    "pagina": str,
                    "Pagina": str,
                    "PAGINA": str,
                    "página": str,
                    "Página": str
                }
            )

            # Limpiar nombres de columnas
            df.columns = [limpiar_nombre_columna(col) for col in df.columns]

            # =========================================================
            # OBTENER ZONA CUANDO EL ARCHIVO ESTÁ DIRECTAMENTE EN ACTAS_RAW
            # =========================================================
            if zona == "ACTAS_RAW" and "subz" in df.columns:

                mapa_zonas = {
                    "MET": "METROPOLITANO",
                    "NDC": "NORDESTE",
                    "OCC": "OCCIDENTE",
                    "ORI": "ORIENTE",
                    "SOE": "SUROESTE"
                }

                codigo_subzona = (
                    df["subz"]
                    .dropna()
                    .astype(str)
                    .str.upper()
                    .str.strip()
                    .iloc[0]
                )

                zona = mapa_zonas.get(
                    codigo_subzona,
                    codigo_subzona
                )

            columnas_eliminar = [
                "unnamed:_29",
                "validación1",
                "validación2",
                "validacion1",
                "validacion2"
            ]

            df = df.drop(
                columns=[col for col in columnas_eliminar if col in df.columns],
                errors="ignore"
            )

            # Convertir pagina a texto para evitar notación científica
            if "pagina" in df.columns:
                df["pagina"] = (
                    df["pagina"]
                    .astype(str)
                    .str.replace(r"\.0$", "", regex=True)
                    .str.strip()
                )

            # Eliminar filas basura del final del archivo
            # Conserva solo registros que tengan pedido válido
            if "pedido" in df.columns:
                df = df[df["pedido"].notna()]
                df = df[df["pedido"].astype(str).str.strip() != ""]
                df = df[df["pedido"].astype(str).str.upper() != "PEDIDO"]
            # =========================================================
            # NORMALIZAR Y VALIDAR PEDIDOS
            # =========================================================

            if "pedido" in df.columns:

                print("\n🔍 NORMALIZANDO PEDIDOS...")

                df["pedido"] = (
                    df["pedido"]
                    .astype(str)
                    .str.replace(r"\.0$", "", regex=True)
                    .str.strip()
                    .str.replace(" ", "", regex=False)
                    .str.replace("\n", "", regex=False)
                    .str.replace("\r", "", regex=False)
                    .str.upper()
                )

                # Reemplazar valores basura
                df["pedido"] = df["pedido"].replace(
                    ["", "NAN", "NONE"],
                    pd.NA
                )

                print("✅ Tipo dato pedido:", df["pedido"].dtype)

                print("✅ Pedidos únicos archivo:",
                    df["pedido"].nunique())

                print("\n📌 TOP PEDIDOS REPETIDOS:")

                print(
                    df["pedido"]
                    .value_counts()
                    .head(10)
                )

                print("\n📌 LONGITUD PEDIDOS:")

                print(
                    df["pedido"]
                    .dropna()
                    .astype(str)
                    .str.len()
                    .value_counts()
                )
            if "actividad" in df.columns:
                df = df[df["actividad"].notna()]
                df = df[df["actividad"].astype(str).str.strip() != ""]    

                        
            # Agregar columnas de trazabilidad

            if numero_acta is not None:
                df["acta"] = numero_acta
            elif "acta" in df.columns:
                df["acta"] = (
                    pd.to_numeric(df["acta"], errors="coerce")
                    .astype("Int64")
                )

            df["zona"] = zona

            # Aplicar correcciones por pedido desde archivo externo
            if ARCHIVO_CORRECCIONES.exists() and "pedido" in df.columns:


                df["pedido_key"] = (
                    df["pedido"]
                    .astype(str)
                    .str.replace(r"\.0$", "", regex=True)
                    .str.strip()
                )

                df = df.merge(
                    df_correcciones[["pedido_key", "contrato", "zona"]],
                    on="pedido_key",
                    how="left",
                    suffixes=("", "_corregida")
                )

                corregidos = df["zona_corregida"].notna().sum()
                print(f"✅ Pedidos corregidos por tabla externa: {corregidos}")

                df["contrato"] = df["contrato_corregida"].combine_first(df["contrato"])
                df["zona"] = df["zona_corregida"].combine_first(df["zona"])

                df = df.drop(
                    columns=[
                        "pedido_key",
                        "contrato_corregida",
                        "zona_corregida"
                    ],
                    errors="ignore"
                )

            else:
                print("⚠️ No se encontró archivo de correcciones o no existe columna pedido.")
            # =========================================================
            # VALIDAR ACTA + ZONA EN MODO ANEXAR
            # Conserva únicamente combinaciones nuevas
            # =========================================================

            if MODO_EJECUCION == "ANEXAR":

                acta_normalizada = (
                    df["acta"]
                    .astype(str)
                    .str.replace(r"\.0$", "", regex=True)
                    .str.strip()
                )

                zona_normalizada = (
                    df["zona"]
                    .astype(str)
                    .str.upper()
                    .str.strip()
                )

                combinaciones_archivo = list(
                    zip(
                        acta_normalizada,
                        zona_normalizada
                    )
                )

                mascara_acta_zona_nueva = pd.Series(
                    [
                        combinacion not in actas_existentes
                        for combinacion in combinaciones_archivo
                    ],
                    index=df.index
                )

                cantidad_omitida = int(
                    (~mascara_acta_zona_nueva).sum()
                )

                cantidad_nueva = int(
                    mascara_acta_zona_nueva.sum()
                )

                if cantidad_omitida > 0:
                    print(
                        "⏭️ Registros omitidos porque ACTA + ZONA "
                        f"ya existen: {cantidad_omitida}"
                    )

                if cantidad_nueva == 0:
                    print(
                        "⏭️ El archivo no contiene combinaciones "
                        "ACTA + ZONA nuevas. Se omite."
                    )
                    continue

                df = df.loc[
                    mascara_acta_zona_nueva
                ].copy()

                print(
                    "✅ Registros nuevos para anexar: "
                    f"{cantidad_nueva}"
                )
            # Crear columna agrupado por actividad
            if "actividad" in df.columns:
                df["agrupado_por_actividad"] = (
                    df["actividad"]
                    .astype(str)
                    .str.strip()
                    .str.upper()
                )

                df["agrupado_por_actividad"] = df["agrupado_por_actividad"].replace({
                    "ACVIS": "TECNÓLOGO AGPE",
                    "ALEGA": "LEGALIZACIÓN",
                    "ALECA": "LEGALIZACIÓN",
                    "ACAMN": "LEGALIZACIÓN",
                    "ALEGN": "LEGALIZACIÓN",
                    "LEGME": "LEGALIZACIÓN",
                    "VITEC": "MOVILIDAD ELÉCTRICA",
                    "ACREV": "PUNTOS DE CONEXIÓN",
                    "ACRED": "MOVIMIENTO DE REDES",
                    "AMRTR": "MOVIMIENTO DE REDES",
                    "AEJDO": "HV"
                })

            # Crear columna agrupado actividad región
            df["agrupado_actividad_region"] = "NO APLICA"

            actividad_norm = df["actividad"].astype(str).str.strip().str.upper() if "actividad" in df.columns else ""
            zona_norm = df["zona"].astype(str).str.strip().str.upper() if "zona" in df.columns else ""
            item_cont_norm = df["item_cont"].astype(str).str.strip().str.upper() if "item_cont" in df.columns else ""

            # Regla especial para AEJDO
            condicion_hv_prepago = (
                (actividad_norm == "AEJDO")
                &
                (zona_norm.isin([
                    "NORDESTE",
                    "OCCIDENTE",
                    "ORIENTE",
                    "SUROESTE"
                ]))
            )

            df.loc[condicion_hv_prepago, "agrupado_actividad_region"] = "HV-PREPAGO"

            # Regla especial para AORDI:
            # primero dejamos vacíos todos los AORDI
            condicion_aordi = (actividad_norm == "AORDI")

            df.loc[condicion_aordi, "agrupado_por_actividad"] = ""
            df.loc[condicion_aordi, "agrupado_actividad_region"] = ""

            # AORDI + E04U / E06U / E07U / E04R / E06R / E07R
            condicion_tecnicos_gps = (
                condicion_aordi
                &
                (item_cont_norm.isin([
                    "E03U",
                    "E04U",
                    "E06U",
                    "E07U",
                    "E08U",
                    "E04R",
                    "E06R",
                    "E07R"
                ]))
            )

            df.loc[
                condicion_tecnicos_gps,
                "agrupado_por_actividad"
            ] = "TECNICOS GPS"

            df.loc[
                condicion_tecnicos_gps,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # AORDI + E01U / E02U / E01R / E02R
            condicion_tecnologo_alquiler = (
                condicion_aordi
                &
                (item_cont_norm.isin([
                    "E01U",
                    "E02U",
                    "E01R",
                    "E02R"
                ]))
            )

            df.loc[
                condicion_tecnologo_alquiler,
                "agrupado_por_actividad"
            ] = "TECNOLOGO ALQUILER INFRAESTRUCTURA"

            df.loc[
                condicion_tecnologo_alquiler,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # AORDI + E05U
            condicion_delineante = (
                condicion_aordi
                &
                (item_cont_norm == "E05U")
            )

            df.loc[
                condicion_delineante,
                "agrupado_por_actividad"
            ] = "DELINEANTES DE ARQUITECTURA"

            df.loc[
                condicion_delineante,
                "agrupado_actividad_region"
            ] = "NO APLICA"


            # =========================================================
            # MOVILIDAD ELÉCTRICA
            # Solo para códigos y actividades comprobadas
            # =========================================================

            codigos_movilidad = [
                "F01U",
                "F01R",
                "F02U",
                "F03U",
                "F04U",
                "F07U",
                "F08U",
                "F10U",
                "F13U",
                "F14U",
                "F17U",
                "F18U",
                "F19U",
                "F20U",
                "F21U",
                "F22U",
                "F23U",
                "F24U",
                "H05U",
                "H05UA"
            ]

            actividades_movilidad = [
                "AORDI",
                "ALECA",
                "ALEGA",
                "VITEC"
            ]

            condicion_movilidad_electrica = (
                item_cont_norm.isin(codigos_movilidad)
                &
                actividad_norm.isin(actividades_movilidad)
            )

            df.loc[
                condicion_movilidad_electrica,
                "agrupado_por_actividad"
            ] = "MOVILIDAD ELÉCTRICA"

            df.loc[
                condicion_movilidad_electrica,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # =========================================================
            # AORDI + REPLANTEADORES
            # =========================================================

            condicion_replanteadores = (
                condicion_aordi
                &
                item_cont_norm.isin([
                    "G04U",
                    "G04R"
                ])
            )

            df.loc[
                condicion_replanteadores,
                "agrupado_por_actividad"
            ] = "REPLANTEADORES"

            df.loc[
                condicion_replanteadores,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # =========================================================
            # AORDI + COMPRA MATERIALES
            # =========================================================

            condicion_compra_materiales = (
                condicion_aordi
                &
                item_cont_norm.isin([
                    "M01U",
                    "M01R"
                ])
            )

            df.loc[
                condicion_compra_materiales,
                "agrupado_por_actividad"
            ] = "COMPRA MATERIALES"

            df.loc[
                condicion_compra_materiales,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # =========================================================
            # AORDI + PERSONAL ESPECIAL
            # =========================================================

            # G01 -> INGENIERO DE DISEÑOS
            condicion_ingeniero = (
                condicion_aordi
                &
                item_cont_norm.isin([
                    "G01U",
                    "G01R"
                ])
            )
            df.loc[
                condicion_ingeniero,
                "agrupado_por_actividad"
            ] = "INGENIERO DE DISEÑOS"

            df.loc[
                condicion_ingeniero,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # G07 -> TECNOLOGO AUTOMATIZACION
            condicion_automatizacion = (
                condicion_aordi
                &
                item_cont_norm.isin([
                    "G07U",
                    "G07R"
                ])
            )

            df.loc[
                condicion_automatizacion,
                "agrupado_por_actividad"
            ] = "TECNOLOGO AUTOMATIZACION"

            df.loc[
                condicion_automatizacion,
                "agrupado_actividad_region"
            ] = "NO APLICA"


            # G02 -> TECNOLOGO OPERATIVO
            condicion_operativo = (
                condicion_aordi
                &
                item_cont_norm.isin([
                    "G02U",
                    "G02R"
                ])
            )

            df.loc[
                condicion_operativo,
                "agrupado_por_actividad"
            ] = "TECNOLOGO OPERATIVO"

            df.loc[
                condicion_operativo,
                "agrupado_actividad_region"
            ] = "NO APLICA"
            
            # =========================================================
            # G03U / G03R -> HV + ZONA
            # =========================================================

            condicion_hv_g03 = (
                condicion_aordi
                &
                item_cont_norm.isin([
                    "G03U",
                    "G03R"
                ])
            )

            df.loc[
                condicion_hv_g03,
                "agrupado_por_actividad"
            ] = (
                "HV "
                + zona_norm.loc[condicion_hv_g03]
            )

            df.loc[
                condicion_hv_g03,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # =========================================================
            # AORDI SIN REGLA DE NEGOCIO
            # METROPOLITANO -> HV METROPOLITANO
            # OTRAS ZONAS   -> NO APLICA
            # =========================================================

            condicion_aordi_sin_regla = (
                condicion_aordi
                &
                (
                    df["agrupado_por_actividad"]
                    .astype(str)
                    .str.strip()
                    .eq("")
                )
            )

            # ---------------------------------------------------------
            # AORDI sin regla de METROPOLITANO
            # Se integran dentro de HV METROPOLITANO
            # ---------------------------------------------------------

            condicion_aordi_sin_regla_met = (
                condicion_aordi_sin_regla
                &
                (zona_norm == "METROPOLITANO")
            )

            cantidad_aordi_sin_regla_met = int(
                condicion_aordi_sin_regla_met.sum()
            )

            if cantidad_aordi_sin_regla_met > 0:
                print(
                    "✅ AORDI sin regla integrados en HV METROPOLITANO: "
                    f"{cantidad_aordi_sin_regla_met}"
                )

            df.loc[
                condicion_aordi_sin_regla_met,
                "agrupado_por_actividad"
            ] = "HV METROPOLITANO"

            df.loc[
                condicion_aordi_sin_regla_met,
                "agrupado_actividad_region"
            ] = "NO APLICA"


            # ---------------------------------------------------------
            # AORDI sin regla de otras zonas
            # Se conservan como NO APLICA
            # ---------------------------------------------------------

            condicion_aordi_sin_regla_otras_zonas = (
                condicion_aordi_sin_regla
                &
                (zona_norm != "METROPOLITANO")
            )

            cantidad_aordi_sin_regla_otras_zonas = int(
                condicion_aordi_sin_regla_otras_zonas.sum()
            )

            if cantidad_aordi_sin_regla_otras_zonas > 0:
                print(
                    "⚠️ AORDI sin regla de otras zonas marcados "
                    "como NO APLICA: "
                    f"{cantidad_aordi_sin_regla_otras_zonas}"
                )

            df.loc[
                condicion_aordi_sin_regla_otras_zonas,
                "agrupado_por_actividad"
            ] = "NO APLICA"

            df.loc[
                condicion_aordi_sin_regla_otras_zonas,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # =========================================================
            # C08 / C09 -> TECNÓLOGO AGPE
            # Regla prioritaria independiente de la actividad
            # =========================================================

            condicion_tecnologo_agpe = item_cont_norm.isin([
                "C07R",
                "C07U",
                "C08R",
                "C08U",
                "C09R",
                "C09U"
            ])

            df.loc[
                condicion_tecnologo_agpe,
                "agrupado_por_actividad"
            ] = "TECNÓLOGO AGPE"

            df.loc[
                condicion_tecnologo_agpe,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # =========================================================
            # COMPLETAR TECNÓLOGO AGPE PARA REGISTROS NO APLICA
            #
            # Si el mismo PEDIDO + ZONA contiene un registro AGPE,
            # sus registros NO APLICA también pertenecen a AGPE.
            # No modifica LEGALIZACIÓN, PREPAGO, HV, etc.
            # =========================================================

            pedido_norm = (
                df["pedido"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            agrupado_norm = (
                df["agrupado_por_actividad"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            # Clave PEDIDO + ZONA para evitar mezclar zonas
            clave_pedido_zona = (
                pedido_norm
                + "|"
                + zona_norm
            )

            # Pedidos/Zonas que ya contienen TECNÓLOGO AGPE
            claves_con_agpe = set(
                clave_pedido_zona[
                    agrupado_norm.eq("TECNÓLOGO AGPE")
                ]
            )

            # ÚNICAMENTE registros actualmente NO APLICA
            condicion_no_aplica_agpe = (
                agrupado_norm.eq("NO APLICA")
                &
                clave_pedido_zona.isin(claves_con_agpe)
            )

            cantidad_no_aplica_agpe = int(
                condicion_no_aplica_agpe.sum()
            )

            if cantidad_no_aplica_agpe > 0:
                print(
                    "✅ Registros NO APLICA integrados a TECNÓLOGO AGPE: "
                    f"{cantidad_no_aplica_agpe}"
                )
            # =========================================================
            # AUDITORÍA TEMPORAL NO APLICA -> TECNÓLOGO AGPE
            # =========================================================

            columnas_auditoria = [
                "pedido",
                "actividad",
                "item_cont",
                "item_res",
                "zona",
                "contrato",
                "valor_cd",
                "reajuste_-_valor_cd"
            ]

            columnas_auditoria = [
                col for col in columnas_auditoria
                if col in df.columns
            ]

            auditoria_no_aplica_agpe = df.loc[
                condicion_no_aplica_agpe,
                columnas_auditoria
            ].copy()

            if not auditoria_no_aplica_agpe.empty:

                auditoria_no_aplica_agpe["total_cd_reajuste"] = (
                    pd.to_numeric(
                        auditoria_no_aplica_agpe.get("valor_cd", 0),
                        errors="coerce"
                    ).fillna(0)
                    +
                    pd.to_numeric(
                        auditoria_no_aplica_agpe.get("reajuste_-_valor_cd", 0),
                        errors="coerce"
                    ).fillna(0)
                )

                print("\n🔎 AUDITORÍA NO APLICA -> TECNÓLOGO AGPE")

                print(
                    auditoria_no_aplica_agpe[
                        [
                            col for col in [
                                "pedido",
                                "actividad",
                                "item_cont",
                                "item_res",
                                "zona",
                                "total_cd_reajuste"
                            ]
                            if col in auditoria_no_aplica_agpe.columns
                        ]
                    ].to_string(index=False)
                )
            df.loc[
                condicion_no_aplica_agpe,
                "agrupado_por_actividad"
            ] = "TECNÓLOGO AGPE"

            df.loc[
                condicion_no_aplica_agpe,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # =========================================================
            # COMPLETAR TECNÓLOGO AGPE POR PEDIDO
            #
            # REGLA:
            # Si un PEDIDO + ZONA contiene alguno de estos ITEM_CONT:
            # C07R/C07U/C08R/C08U/C09R/C09U,
            # entonces todos sus registros AORDI que estén como
            # HV METROPOLITANO o NO APLICA pertenecen a TECNÓLOGO AGPE.
            #
            # No modifica otras agrupaciones.
            # =========================================================

            pedido_norm = (
                df["pedido"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            agrupado_norm = (
                df["agrupado_por_actividad"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            codigos_base_agpe = [
                "C07R",
                "C07U",
                "C08R",
                "C08U",
                "C09R",
                "C09U"
            ]

            # Clave PEDIDO + ZONA
            clave_pedido_zona = (
                pedido_norm
                + "|"
                + zona_norm
            )

            # Pedidos que contienen un código que identifica TECNÓLOGO AGPE
            claves_pedido_agpe = set(
                clave_pedido_zona[
                    item_cont_norm.isin(codigos_base_agpe)
                ]
            )

            # =========================================================
            # CORREGIR LEGALIZACIÓN -> TECNÓLOGO AGPE POR PEDIDO
            #
            # Si PEDIDO + ZONA contiene C07/C08/C09,
            # solo las filas que actualmente quedaron como
            # LEGALIZACIÓN + ZONA pasan a TECNÓLOGO AGPE.
            # =========================================================

            condicion_pedido_agpe = (
                clave_pedido_zona.isin(claves_pedido_agpe)
                &
                agrupado_norm.str.startswith(
                    "LEGALIZACIÓN",
                    na=False
                )
            )

            cantidad_pedido_agpe = int(
                condicion_pedido_agpe.sum()
            )

            if cantidad_pedido_agpe > 0:
                print(
                    "✅ Registros AORDI integrados a TECNÓLOGO AGPE "
                    "por pedido con C07/C08/C09: "
                    f"{cantidad_pedido_agpe}"
                )

            df.loc[
                condicion_pedido_agpe,
                "agrupado_por_actividad"
            ] = "TECNÓLOGO AGPE"

            df.loc[
                condicion_pedido_agpe,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # DIPRE / DSPRE / REEQU -> PREPAGO
            condicion_prepago = actividad_norm.isin(["DIPRE", "DSPRE", "REEQU"])

            df.loc[condicion_prepago, "agrupado_por_actividad"] = "PREPAGO"
            df.loc[condicion_prepago, "agrupado_actividad_region"] = "NO APLICA"


            # DIPRE / DSPRE en regiones -> HV-PREPAGO
            condicion_hv_prepago_prepago = (
                actividad_norm.isin(["DIPRE", "DSPRE"])
                &
                zona_norm.isin([
                    "NORDESTE",
                    "OCCIDENTE",
                    "ORIENTE",
                    "SUROESTE"
                ])
            )

            df.loc[condicion_hv_prepago_prepago, "agrupado_por_actividad"] = "PREPAGO"
            df.loc[condicion_hv_prepago_prepago, "agrupado_actividad_region"] = "HV-PREPAGO"

            # =========================================================
            # NORMALIZACIÓN FINAL DE HV Y LEGALIZACIÓN POR ZONA
            # =========================================================

            agrupado_norm = (
                df["agrupado_por_actividad"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            # ---------------------------------------------------------
            # HV DEBE QUEDAR COMO HV + ZONA
            # ---------------------------------------------------------

            condicion_hv_final = agrupado_norm.isin([
                "HV",
                "HV METROPOLITANO",
                "HV NORDESTE",
                "HV OCCIDENTE",
                "HV ORIENTE",
                "HV SUROESTE"
            ])

            df.loc[
                condicion_hv_final,
                "agrupado_por_actividad"
            ] = (
                "HV "
                + zona_norm.loc[condicion_hv_final]
            )

            # ---------------------------------------------------------
            # LEGALIZACIÓN DEBE QUEDAR COMO LEGALIZACIÓN + ZONA
            # ---------------------------------------------------------

            condicion_legalizacion_final = agrupado_norm.isin([
                "LEGALIZACIÓN",
                "LEGALIZACIÓN METROPOLITANO",
                "LEGALIZACIÓN NORDESTE",
                "LEGALIZACIÓN OCCIDENTE",
                "LEGALIZACIÓN ORIENTE",
                "LEGALIZACIÓN SUROESTE"
            ])

            df.loc[
                condicion_legalizacion_final,
                "agrupado_por_actividad"
            ] = (
                "LEGALIZACIÓN "
                + zona_norm.loc[condicion_legalizacion_final]
            )

            # =========================================================
            # ITEMS DE LEGALIZACIÓN NORDESTE QUE DEBEN SUMAR A HV NORDESTE
            # =========================================================

            items_hv_nordeste = [
                "B01R",
                "B04R",
                "B05R",
                "B07R",
                "B08R",
                "B09R"
            ]

            condicion_hv_nordeste_desde_legalizacion = (
                df["agrupado_por_actividad"]
                .astype(str)
                .str.strip()
                .str.upper()
                .eq("LEGALIZACIÓN NORDESTE")
                &
                item_cont_norm.isin(
                    items_hv_nordeste
                )
            )

            cantidad_hv_nordeste_desde_legalizacion = int(
                condicion_hv_nordeste_desde_legalizacion.sum()
            )

            if cantidad_hv_nordeste_desde_legalizacion > 0:
                print(
                    "✅ Registros reclasificados de LEGALIZACIÓN NORDESTE "
                    "a HV NORDESTE: "
                    f"{cantidad_hv_nordeste_desde_legalizacion}"
                )

            df.loc[
                condicion_hv_nordeste_desde_legalizacion,
                "agrupado_por_actividad"
            ] = "HV NORDESTE"

            df.loc[
                condicion_hv_nordeste_desde_legalizacion,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            # =========================================================
            # UNIFICAR HV METROPOLITANO
            # =========================================================

            agrupado_norm = (
                df["agrupado_por_actividad"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            condicion_hv_metropolitano = (
                (zona_norm == "METROPOLITANO")
                &
                agrupado_norm.isin([
                    "HV",
                    "HV METROPOLITANO"
                ])
            )

            df.loc[
                condicion_hv_metropolitano,
                "agrupado_por_actividad"
            ] = "HV METROPOLITANO"

            df.loc[
                condicion_hv_metropolitano,
                "agrupado_actividad_region"
            ] = "NO APLICA"
            
            
            # =========================================================
            # UNIFICAR HV + PREPAGO POR ZONA
            # Solo NORDESTE, OCCIDENTE, ORIENTE y SUROESTE.
            # METROPOLITANO se conserva separado:
            #   - HV METROPOLITANO
            #   - PREPAGO
            # =========================================================

            zonas_hv_prepago = [
                "NORDESTE",
                "OCCIDENTE",
                "ORIENTE",
                "SUROESTE"
            ]

            agrupado_norm = (
                df["agrupado_por_actividad"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            condicion_unificar_hv_prepago = (
                zona_norm.isin(zonas_hv_prepago)
                &
                (
                    agrupado_norm.eq("PREPAGO")
                    |
                    agrupado_norm.eq("HV " + zona_norm)
                )
            )

            cantidad_unificados_hv_prepago = int(
                condicion_unificar_hv_prepago.sum()
            )

            if cantidad_unificados_hv_prepago > 0:
                print(
                    "✅ Registros unificados como HV + PREPAGO por zona: "
                    f"{cantidad_unificados_hv_prepago}"
                )

            df.loc[
                condicion_unificar_hv_prepago,
                "agrupado_por_actividad"
            ] = (
                "HV + PREPAGO "
                + zona_norm.loc[condicion_unificar_hv_prepago]
            )
            # =========================================================
            # PRIORIDAD FINAL TECNÓLOGO AGPE
            #
            # Si PEDIDO + ZONA contiene C07/C08/C09,
            # ninguna regla posterior puede dejarlo en otra agrupación.
            # =========================================================

            pedido_norm = (
                df["pedido"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            zona_norm = (
                df["zona"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            item_cont_norm = (
                df["item_cont"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

            clave_pedido_zona = (
                pedido_norm
                + "|"
                + zona_norm
            )

            codigos_base_agpe = [
                "C07R",
                "C07U",
                "C08R",
                "C08U",
                "C09R",
                "C09U"
            ]

            claves_agpe_final = set(
                clave_pedido_zona[
                    item_cont_norm.isin(codigos_base_agpe)
                ]
            )

            agrupado_norm_final = (
                df["agrupado_por_actividad"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            condicion_agpe_final = (
                clave_pedido_zona.isin(claves_agpe_final)
                &
                agrupado_norm_final.str.startswith(
                    "LEGALIZACIÓN",
                    na=False
                )
            )

            cantidad_agpe_final = int(
                condicion_agpe_final.sum()
            )

            if cantidad_agpe_final > 0:
                print(
                    "✅ Prioridad final TECNÓLOGO AGPE aplicada: "
                    f"{cantidad_agpe_final}"
                )

            df.loc[
                condicion_agpe_final,
                "agrupado_por_actividad"
            ] = "TECNÓLOGO AGPE"

            df.loc[
                condicion_agpe_final,
                "agrupado_actividad_region"
            ] = "NO APLICA"

            registros.append(df)

        
        except Exception as e:
            print(f"⚠️ Error procesando archivo: {archivo.name}")
            print(f"   Motivo: {e}")

    if not registros:
        print("✅ No se encontraron actas nuevas para anexar.")
        return

    df_nuevo = pd.concat(registros, ignore_index=True)

    # =========================================================
    # CORRECCIÓN GLOBAL AGPE DESPUÉS DE UNIFICAR LOS ARCHIVOS
    #
    # Problema que resuelve:
    # Un mismo PEDIDO puede venir repartido entre varios Excel.
    #
    # Regla:
    # Si ACTA + ZONA + PEDIDO contiene C07/C08/C09,
    # las filas del mismo pedido que hayan quedado como
    # LEGALIZACIÓN + ZONA pasan a TECNÓLOGO AGPE.
    #
    # NO modifica otras agrupaciones.
    # =========================================================

    pedido_global = (
        df_nuevo["pedido"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    zona_global = (
        df_nuevo["zona"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    acta_global = (
        df_nuevo["acta"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    item_cont_global = (
        df_nuevo["item_cont"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    agrupado_global = (
        df_nuevo["agrupado_por_actividad"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    codigos_agpe_global = [
        "C07R",
        "C07U",
        "C08R",
        "C08U",
        "C09R",
        "C09U"
    ]

    # Clave completa para no mezclar actas ni zonas
    clave_global = (
        acta_global
        + "|"
        + zona_global
        + "|"
        + pedido_global
    )

    # Pedidos que realmente contienen código AGPE
    claves_con_agpe_global = set(
        clave_global[
            item_cont_global.isin(
                codigos_agpe_global
            )
        ]
    )

    # =========================================================
    # CORRECCIÓN GLOBAL AGPE - SOLO REGLA CONFIRMADA
    #
    # Si ACTA + ZONA + PEDIDO contiene C07/C08/C09,
    # únicamente las filas de LEGALIZACIÓN del mismo pedido
    # pasan a TECNÓLOGO AGPE.
    #
    # HV METROPOLITANO y NO APLICA NO se modifican aquí.
    # Se dejan para revisión con el ingeniero.
    # =========================================================

    condicion_agpe_global = (
        clave_global.isin(
            claves_con_agpe_global
        )
        &
        agrupado_global.str.startswith(
            "LEGALIZACIÓN",
            na=False
        )
    )
    
    cantidad_corregida_agpe_global = int(
        condicion_agpe_global.sum()
    )

    if cantidad_corregida_agpe_global > 0:
        print(
            "✅ Registros reclasificados globalmente "
            "a TECNÓLOGO AGPE: "
            f"{cantidad_corregida_agpe_global}"
        )

    df_nuevo.loc[
        condicion_agpe_global,
        "agrupado_por_actividad"
    ] = "TECNÓLOGO AGPE"

    df_nuevo.loc[
        condicion_agpe_global,
        "agrupado_actividad_region"
    ] = "NO APLICA"
    # =========================================================
    # QA - PEDIDOS PRESENTES EN MÁS DE UNA AGRUPACIÓN
    # SOLO AUDITORÍA: NO MODIFICA DATOS NI REGLAS DE NEGOCIO
    # =========================================================

    columnas_qa = [
        "acta",
        "zona",
        "pedido",
        "agrupado_por_actividad"
    ]

    if all(col in df_nuevo.columns for col in columnas_qa):

        qa_agrupaciones = (
            df_nuevo[columnas_qa]
            .drop_duplicates()
        )

        cantidad_agrupaciones = (
            qa_agrupaciones
            .groupby(
                ["acta", "zona", "pedido"]
            )["agrupado_por_actividad"]
            .nunique()
            .reset_index(name="cantidad_agrupaciones")
        )

        pedidos_multiples_agrupaciones = (
            cantidad_agrupaciones[
                cantidad_agrupaciones[
                    "cantidad_agrupaciones"
                ] > 1
            ]
            .copy()
        )

        detalle_conflictos = (
            qa_agrupaciones
            .merge(
                pedidos_multiples_agrupaciones[
                    [
                        "acta",
                        "zona",
                        "pedido",
                        "cantidad_agrupaciones"
                    ]
                ],
                on=["acta", "zona", "pedido"],
                how="inner"
            )
            .sort_values(
                by=[
                    "acta",
                    "zona",
                    "pedido",
                    "agrupado_por_actividad"
                ],
                kind="stable"
            )
            .reset_index(drop=True)
        )

        if detalle_conflictos.empty:
            print(
                "✅ QA AGRUPACIONES: "
                "ningún pedido aparece en más de una agrupación."
            )
        else:
            print(
                "\n⚠️ QA AGRUPACIONES: "
                f"{len(pedidos_multiples_agrupaciones)} "
                "pedidos aparecen en más de una agrupación."
            )

            print(
                detalle_conflictos
                .head(100)
                .to_string(index=False)
            )

    else:

        detalle_conflictos = pd.DataFrame(
            columns=[
                "acta",
                "zona",
                "pedido",
                "agrupado_por_actividad",
                "cantidad_agrupaciones"
            ]
        )

        print(
            "⚠️ QA AGRUPACIONES no ejecutado. "
            "Faltan columnas requeridas."
        )

    if MODO_EJECUCION == "ANEXAR":

        if not ARCHIVO_SALIDA.exists():

            print("❌ No existe el archivo ACTAS_UNIFICADAS.xlsx")
            print("Ejecute primero el modo RECONSTRUIR.")
            return

        print("\n========================================")
        print("PROYECTO ACTAS")
        print("MODO: ANEXAR")
        print("========================================")

        print("Leyendo archivo histórico...")

        df_historico = pd.read_excel(
            ARCHIVO_SALIDA,
            sheet_name="ACTAS_UNIFICADAS",
            dtype=str
        )

        df_historico = df_historico.fillna("")

        print(f"📄 Registros históricos : {len(df_historico):,}")
        print(f"📥 Registros nuevos     : {len(df_nuevo):,}")

        df_final = pd.concat(
            [df_historico, df_nuevo],
            ignore_index=True
        )

        print(f"📊 Total consolidado    : {len(df_final):,}")

    elif MODO_EJECUCION == "RECONSTRUIR":

        print("\n========================================")
        print("PROYECTO ACTAS")
        print("MODO: RECONSTRUIR")
        print("========================================")

        df_final = df_nuevo

        print(f"📊 Registros procesados : {len(df_final):,}")

    else:

        print("❌ MODO_EJECUCION no válido.")
        return

    
    # =========================================================
    # ORDENAR EL CONSOLIDADO
    # =========================================================

    df_final["acta"] = pd.to_numeric(
        df_final["acta"],
        errors="coerce"
    )

    df_final = df_final.sort_values(
        by=["acta", "zona", "pedido"],
        ascending=[True, True, True]
    ).reset_index(drop=True)

    # =========================================================
    # EVENTOS OPERATIVOS ÚNICOS POR ACTA
    # =========================================================

    df_eventos_operativos = (
        df_final[
            ["acta", "zona", "pedido"]
        ]
        .drop_duplicates()
        .sort_values(
            by=["acta", "zona", "pedido"]
        )
    )

    print(
        "✅ Eventos operativos únicos por acta:",
        len(df_eventos_operativos)
    )
    # =========================================================
    # PEDIDOS EMPRESARIALES ÚNICOS GLOBALES
    # =========================================================

    df_pedidos_globales = (
        df_final[
            ["zona", "pedido"]
        ]
        .drop_duplicates()
        .sort_values(
            by=["zona", "pedido"]
        )
    )

    print(
        "✅ Pedidos empresariales únicos:",
        len(df_pedidos_globales)
    )
    
    # =========================================================
    # PEDIDOS CON MÚLTIPLES ACTAS
    # =========================================================
    # Obtener únicamente los pedidos presentes en más de una acta
    pedidos_repetidos = (
        df_final
        .groupby("pedido")["acta"]
        .nunique()
    )

    pedidos_repetidos = pedidos_repetidos[
        pedidos_repetidos > 1
    ].index

    # Filtrar únicamente esos pedidos
    df_pedidos_repetidos = df_final[
        df_final["pedido"].isin(pedidos_repetidos)
    ]

    df_pedidos_repetidos = (
        df_pedidos_repetidos[
            [
                "pedido",
                "acta",
                "actividad",
                "zona",
                "contrato"
            ]
        ]
        .drop_duplicates()
        .sort_values(
            by=["pedido", "acta"]
        )
    )

    print(
        "✅ Pedidos con múltiples actas:",
        df_pedidos_repetidos["pedido"].nunique()
    )
    print(f"✅ Archivos consolidados: {len(registros)}")
    print(f"✅ Total filas consolidadas: {len(df_final)}")

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    columnas_decimales = [
        "vlr_cliente",
        "valor_costo",
        "valor_cd",
        "valor_cd+u",
        "valor_administración",
        "reajuste_-_valor_cd",
        "reajuste_-_valor_cd+u",
        "reajuste_-_valor_administración"
    ]

    for col in columnas_decimales:

        if col in df_final.columns:

            mascara = pd.to_numeric(
                df_final[col],
                errors="coerce"
            ).notna()

            df_final.loc[mascara, col] = (
                pd.to_numeric(df_final.loc[mascara, col])
                .round(2)
            )


    with pd.ExcelWriter(
        ARCHIVO_SALIDA,
        engine="xlsxwriter"
    )as writer:

        # Hoja principal detallada
        df_final.to_excel(
            writer,
            index=False,
            sheet_name="ACTAS_UNIFICADAS"
        )

        # Hoja eventos operativos
        df_eventos_operativos.to_excel(
            writer,
            index=False,
            sheet_name="PEDIDOS_POR_ACTA"
        )

        # Hoja pedidos empresariales únicos
        df_pedidos_globales.to_excel(
            writer,
            index=False,
            sheet_name="PEDIDOS_UNICOS"
        )

        # Hoja pedidos repetidos entre actas
        df_pedidos_repetidos.to_excel(
            writer,
            index=False,
            sheet_name="PEDIDOS_REPETIDOS"
        )

        # Hoja QA: pedidos presentes en más de una agrupación
        # Solo auditoría; no modifica el consolidado.
        detalle_conflictos.to_excel(
            writer,
            index=False,
            sheet_name="PEDIDOS_MULTIPLES_AGRUP"
        )

    print("\n==============================")
    print("RESUMEN EJECUTIVO")
    print("==============================")

    print(
        f"📌 Pedidos empresariales únicos: "
        f"{len(df_pedidos_globales)}"
    )

    print(
        f"📌 Eventos operativos por acta: "
        f"{len(df_eventos_operativos)}"
    )

    print(
        f"📌 Pedidos con múltiples actas: "
        f"{df_pedidos_repetidos['pedido'].nunique()}"
    )

    print(
        f"📌 Total registros operativos: "
        f"{len(df_final)}"
    )

    print("==============================\n")
    print("✅ Archivo Excel base creado.")
    print("✅ Archivo Excel generado (sin formateo).")
    print(f"📄 Archivo generado: {ARCHIVO_SALIDA}")

    fin_total = time.perf_counter()

    print(f"⏱ Tiempo total ejecución: {fin_total - inicio_total:.2f} segundos")
if __name__ == "__main__":
    consolidar_actas()