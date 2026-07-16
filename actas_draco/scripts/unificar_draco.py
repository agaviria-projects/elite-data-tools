import pandas as pd

from scripts.config import (
    CARPETA_DRACO,
    CARPETA_SALIDA
)

from scripts.limpiar_codigos import limpiar_codigos

# ==========================================
# 🔗 UNIFICAR ARCHIVOS DRACO
# ==========================================

def unificar_draco():

    # ======================================
    # 📦 LISTA DATAFRAMES
    # ======================================

    lista_df = []

    # ======================================
    # 📂 RECORRER ARCHIVOS
    # ======================================

    archivos = CARPETA_DRACO.glob("*.xlsx")

    for archivo in archivos:

        print("=" * 50)
        print(f"📄 Procesando: {archivo.name}")

        # ==================================
        # 📖 LEER EXCEL
        # ==================================

        df = pd.read_excel(archivo)

        # ==================================
        # 🔍 MOSTRAR COLUMNAS
        # ==================================

        print(df.columns.tolist())

        # ==================================
        # 🧾 TRAZABILIDAD
        # ==================================

        df["archivo_origen"] = archivo.name

        # ==================================
        # 🧹 LIMPIAR CODIGOS
        # ==================================

        df = limpiar_codigos(df)

        # ==================================
        # 📊 MOSTRAR REGISTROS
        # ==================================

        print(f"✅ Registros: {len(df)}")

        # ==================================
        # 📦 AGREGAR A LISTA
        # ==================================

        lista_df.append(df)

    # ======================================
    # 🚫 VALIDAR ARCHIVOS
    # ======================================

    if not lista_df:

        raise ValueError(
            "❌ No se encontraron archivos DRACO."
        )

    # ======================================
    # 🔗 CONCATENAR
    # ======================================

    df_final = pd.concat(

        lista_df,

        ignore_index=True

    )

    # ======================================
    # 💾 EXPORTAR UNIFICADO
    # ======================================

    ruta_salida = (

        CARPETA_SALIDA /

        "DRACO_UNIFICADO.xlsx"

    )

    df_final.to_excel(

        ruta_salida,

        index=False

    )

    # ======================================
    # ✅ FINAL
    # ======================================

    print("=" * 50)
    print("✅ DRACO UNIFICADO GENERADO")
    print(f"📁 Ruta: {ruta_salida}")

    return df_final