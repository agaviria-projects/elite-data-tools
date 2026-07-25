from src.validador import validar_archivo_fenix
from src.lector_excel import leer_excel
from src.agrupador import construir_informes


# ==========================================================
# MAIN
# ==========================================================

def main():

    print("=" * 60)
    print("        SEGUIMIENTO INTELIGENTE ANS")
    print("=" * 60)

    # ------------------------------------------------------
    # VALIDAR ARCHIVO
    # ------------------------------------------------------

    print("\n📄 Validando archivo...")

    validar_archivo_fenix()

    print("✅ Archivo válido.")

    # ------------------------------------------------------
    # LEER EXCEL
    # ------------------------------------------------------

    print("\n📖 Leyendo información...")

    df = leer_excel()

    print(f"✅ Registros cargados : {len(df):,}")

    # ------------------------------------------------------
    # CONSTRUIR INFORMES
    # ------------------------------------------------------

    print("\n📊 Construyendo informes...\n")

    informes = construir_informes(df)

    # ------------------------------------------------------
    # MOSTRAR RESULTADOS
    # ------------------------------------------------------

    for nombre_grupo, bloques in informes.items():

        print("=" * 60)
        print(f"📧 {nombre_grupo}")
        print("=" * 60)

        for bloque in bloques:

            print(
                f"\nProducto : {', '.join(bloque['productos'])}"
            )

            for actividad, df_actividad in bloque["actividades"].items():

                print(
                    f"   • {actividad:<10} "
                    f"{len(df_actividad):>6} pedidos"
                )

    print("\n")
    print("=" * 60)
    print("✅ PROCESO FINALIZADO")
    print("=" * 60)


# ==========================================================
# EJECUCIÓN
# ==========================================================

if __name__ == "__main__":

    main()