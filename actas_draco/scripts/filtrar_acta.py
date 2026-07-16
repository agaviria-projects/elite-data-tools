from scripts.config import CARPETA_SALIDA

# ==========================================
# 🎯 FILTRAR ACTA
# ==========================================

def filtrar_acta(df, acta):

    # ======================================
    # EXTRAER NUMERO ACTA
    # EJEMPLO:
    # ACTA 8 → 8
    # ======================================

    numero_acta = (

        acta
        .replace("ACTA", "")
        .strip()

    )

    # ======================================
    # FILTRAR POR COLUMNA REAL DRACO
    # ======================================

    df_filtrado = df[

        df["Acta"].astype(str).str.strip()

        == numero_acta

    ]

    # ======================================
    # VALIDAR RESULTADOS
    # ======================================

    if df_filtrado.empty:

        raise ValueError(
            f"❌ No existe información para {acta}"
        )

    # ======================================
    # NOMBRE ARCHIVO
    # ======================================

    nombre_archivo = (

        acta
        .replace(" ", "_")

    )

    # ======================================
    # RUTA SALIDA
    # ======================================

    ruta_salida = (

        CARPETA_SALIDA /

        f"DRACO_{nombre_archivo}.xlsx"

    )

    # ======================================
    # EXPORTAR
    # ======================================

    df_filtrado.to_excel(

        ruta_salida,

        index=False

    )

    # ======================================
    # MENSAJES
    # ======================================

    print("=" * 50)
    print(f"✅ Archivo generado: {acta}")
    print(f"📁 Ruta: {ruta_salida}")

    return df_filtrado