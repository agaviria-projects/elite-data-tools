"""
==========================================================
SERVITRAVEL
CONSOLIDADOR AUTOMÁTICO
==========================================================

Autor : Héctor Alejandro Gaviria

Versión : 1.0
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
    consolidar_parqueaderos
)

from consolidador import (
    consolidar_anio,
    consolidar_viaticos,
    consolidar_parqueaderos,
    consolidar_peajes
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

    print("Abriendo archivo consolidado...")

    app, libro = abrir_excel(
        ARCHIVO_CONSOLIDADO
    )

    try:

        consolidar_anio(libro)

        consolidar_viaticos(libro)

        consolidar_parqueaderos(libro)

        consolidar_peajes(libro)

    except Exception as e:

        print("\nERROR\n")

        print(e)

    finally:

        # --------------------------------------------------
        # GUARDAR Y CERRAR
        # --------------------------------------------------

        print("\nGuardando archivo...")

        cerrar_excel(
            app,
            libro
        )

    print("\n")
    print("=" * 60)
    print("PROCESO FINALIZADO CORRECTAMENTE")
    print("=" * 60)


# ==========================================================
# EJECUTAR
# ==========================================================

if __name__ == "__main__":

    main()