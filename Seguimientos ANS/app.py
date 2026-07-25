from src.validador import validar_archivo_fenix
from src.lector_excel import leer_excel
from src.agrupador import construir_informes
from src.generador_correo import construir_correos
from src.outlook import abrir_correo_outlook

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

    print("\n📊 Construyendo informes...")

    informes = construir_informes(df)

    # ------------------------------------------------------
    # CONSTRUIR MODELO DE CORREOS
    # ------------------------------------------------------

    print("📧 Construyendo modelo de correos...\n")

    correos = construir_correos(informes)

    from src.generador_html import generar_html
    from config.parametros import CARPETA_HTML

    # ------------------------------------------------------
    # MOSTRAR MODELO DE CORREO
    # ------------------------------------------------------

    for correo in correos[:1]:

        print("=" * 60)
        print(f"📧 {correo['grupo']}")
        print("=" * 60)

        print(f"Asunto      : {correo['asunto']}")
        print(f"Subzona     : {correo['subzona']}")
        print(f"Fecha Corte : {correo['fecha_corte']}")
        print(f"Total       : {correo['total_pedidos']} pedidos")

        for bloque in correo["bloques"]:

            print(
                f"\nProducto : {', '.join(bloque['productos'])}"
            )

            print(
                f"Total Producto : "
                f"{bloque['total_pedidos']} pedidos"
            )

            for actividad in bloque["actividades"]:

                print(
                    f"   • {actividad['nombre']:<10}"
                    f"{actividad['total']:>6} pedidos"
                )

        # ==================================================
        # GENERAR HTML
        # ==================================================

        html = generar_html(correo)

        # ==================================================
        # ABRIR OUTLOOK
        # ==================================================

        abrir_correo_outlook(
            correo,
            html,
        )

        # --------------------------------------------------
        # GENERAR HTML
        # --------------------------------------------------

        html = generar_html(correo)

        archivo_html = (
            CARPETA_HTML
            / f"{correo['grupo'].replace(' ', '_')}.html"
        )

        with open(
            archivo_html,
            "w",
            encoding="utf-8",
        ) as archivo:

            archivo.write(html)

        print(f"\n✅ HTML generado: {archivo_html.name}\n")

    print("=" * 60)
    print("✅ PROCESO FINALIZADO")
    print("=" * 60)

    
# ==========================================================
# EJECUCIÓN
# ==========================================================

if __name__ == "__main__":

    main()