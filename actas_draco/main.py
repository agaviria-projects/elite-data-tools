from scripts.unificar_draco import unificar_draco

from scripts.filtrar_acta import filtrar_acta

# ==========================================
# 🚀 MAIN
# ==========================================

def main():

    print("=" * 50)
    print("🚀 INICIANDO PROCESO DRACO")
    print("=" * 50)

    # ======================================
    # UNIFICAR ARCHIVOS
    # ======================================

    df_final = unificar_draco()

    # ======================================
    # SOLICITAR ACTA
    # ======================================

    acta = input(
        "\n📌 Ingrese el número de acta (Ej: ACTA 8): "
    ).upper().strip()

    # ======================================
    # FILTRAR ACTA
    # ======================================

    filtrar_acta(

        df_final,

        acta

    )

    print("=" * 50)
    print("✅ PROCESO FINALIZADO")
    print("=" * 50)

# ==========================================
# ▶ EJECUTAR
# ==========================================

if __name__ == "__main__":

    main()