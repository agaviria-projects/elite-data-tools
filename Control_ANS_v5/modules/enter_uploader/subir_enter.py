import os
from datetime import datetime

from modules.enter_uploader.utils import listar_pdfs, calcular_hash_archivo
from modules.enter_uploader.control_subidas import (
    inicializar_control,
    cargar_hashes_existentes,
    registrar_evento
)

# 🔴 AJUSTA A TU RUTA REAL DE ONEDRIVE
BASE_EVIDENCIAS = r"C:\Users\hector.gaviria\OneDrive - Elite Ingenieros SAS\Evidencias_PDF"

def obtener_ultima_fecha_con_evidencias(base_evidencias):
    """
    Equivalente a 'Marca Temporal':
    detecta la última fecha REAL con evidencias cargadas
    """
    fechas_validas = []

    for responsable in os.listdir(base_evidencias):
        ruta_resp = os.path.join(base_evidencias, responsable)
        if not os.path.isdir(ruta_resp):
            continue

        for fecha in os.listdir(ruta_resp):
            try:
                fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                continue

            # Ignora hoy y fechas futuras
            if fecha_dt.date() >= datetime.now().date():
                continue

            ruta_fecha = os.path.join(ruta_resp, fecha)
            if not os.path.isdir(ruta_fecha):
                continue

            for actividad in os.listdir(ruta_fecha):
                ruta_act = os.path.join(ruta_fecha, actividad)
                if not os.path.isdir(ruta_act):
                    continue

                if listar_pdfs(ruta_act):
                    fechas_validas.append(fecha_dt)
                    break

    if not fechas_validas:
        return None

    return max(fechas_validas).strftime("%Y-%m-%d")

def ejecutar_subida_simulada():
    print("=== INICIO SUBIDA SIMULADA ENTER ===")

    inicializar_control()
    hashes_procesados = cargar_hashes_existentes()

    fecha_objetivo = obtener_ultima_fecha_con_evidencias(BASE_EVIDENCIAS)

    if not fecha_objetivo:
        print("[INFO] No se encontraron evidencias pendientes para procesar")
        print("=== FIN SUBIDA SIMULADA ===")
        return

    print(f"[INFO] Fecha real detectada (Marca Temporal): {fecha_objetivo}")

    for responsable in os.listdir(BASE_EVIDENCIAS):
        ruta_resp = os.path.join(BASE_EVIDENCIAS, responsable)
        if not os.path.isdir(ruta_resp):
            continue

        ruta_fecha = os.path.join(ruta_resp, fecha_objetivo)
        if not os.path.isdir(ruta_fecha):
            continue

        print(f"\nResponsable: {responsable}")

        for actividad in os.listdir(ruta_fecha):
            ruta_act = os.path.join(ruta_fecha, actividad)
            if not os.path.isdir(ruta_act):
                continue

            print(f"  Actividad: {actividad}")

            archivos = listar_pdfs(ruta_act)
            if not archivos:
                print("    [SIN ARCHIVOS]")
                continue

            for ruta_archivo in archivos:
                nombre = os.path.basename(ruta_archivo)
                hash_archivo = calcular_hash_archivo(ruta_archivo)

                if hash_archivo in hashes_procesados:
                    print(f"    [IGNORADO] {nombre}")
                    continue

                print(f"    [SUBIENDO SIMULADO] {nombre}")

                registrar_evento(
                    archivo=nombre,
                    hash_archivo=hash_archivo,
                    estado="LISTO_PARA_ENTER",
                    detalle=f"{responsable} | {fecha_objetivo} | {actividad}"
                )

    print("\n=== FIN SUBIDA SIMULADA ===")

if __name__ == "__main__":
    ejecutar_subida_simulada()
