"""
==========================================================
SERVITRAVEL
CONSOLIDADOR AUTOMÁTICO
==========================================================

Autor  : Héctor Alejandro Gaviria
Versión: 1.0
"""

from config import (
    ARCHIVO_CONSOLIDADO,
    CARPETA_BACKUP
)

from excel_utils import (
    crear_backup,
    abrir_excel,
    cerrar_excel
)

from consolidador import (
    consolidar_anio,
    consolidar_viaticos,
    consolidar_parqueaderos,
    consolidar_peajes
)

from facturacion import (
    actualizar_facturacion
)

from dashboard_analytics import (
    actualizar_dashboard
)


# ==========================================================
# MAIN
# ==========================================================

def main():

    print("\n")
    print("=" * 60)
    print("SERVITRAVEL")
    print("CONSOLIDADOR AUTOMÁTICO")
    print("=" * 60)

    # ------------------------------------------------------
    # BACKUP
    # ------------------------------------------------------

    print("\nCreando Backup...")

    crear_backup(
        ARCHIVO_CONSOLIDADO,
        CARPETA_BACKUP
    )

    # ------------------------------------------------------
    # ABRIR LIBRO
    # ------------------------------------------------------

    print("\nAbriendo archivo consolidado...")

    app, libro = abrir_excel(
        ARCHIVO_CONSOLIDADO
    )

    proceso_correcto = False

    try:

        # ==================================================
        # CONSOLIDACIONES
        # ==================================================

        consolidar_anio(libro)

        consolidar_viaticos(libro)

        consolidar_parqueaderos(libro)

        consolidar_peajes(libro)

        # ==================================================
        # ACTUALIZAR FACTURACION
        # ==================================================

        actualizar_facturacion(
            libro
        )

        # ==================================================
        # ACTUALIZAR MODELO DEL DASHBOARD
        # ==================================================

        print("\nActualizando análisis del Dashboard...")

        actualizar_dashboard(
            libro
        )

        proceso_correcto = True

    except Exception as e:

        print("\n" + "=" * 60)
        print("ERROR DURANTE EL PROCESO")
        print("=" * 60)

        print(f"\n{e}")

    finally:

        # --------------------------------------------------
        # GUARDAR Y CERRAR
        # --------------------------------------------------

        print("\nGuardando archivo...")

        cerrar_excel(
            app,
            libro
        )

    # ======================================================
    # RESULTADO FINAL
    # ======================================================

    print("\n")
    print("=" * 60)

    if proceso_correcto:

        print("PROCESO FINALIZADO CORRECTAMENTE")

    else:

        print("PROCESO FINALIZADO CON ERRORES")

    print("=" * 60)


# ==========================================================
# EJECUTAR
# ==========================================================

if __name__ == "__main__":

    main()