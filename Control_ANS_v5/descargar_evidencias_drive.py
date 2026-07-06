# -*- coding: utf-8 -*-
# MOVER EVIDENCIAS A PAPELERA_API (SIN DESCARGAR)
# ------------------------------------------------------------
import time
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# CONFIGURACIÓN
# ============================================================
CRED_PATH = "control-ans-evidencias-1ef0b1b8d1a8.json"
FOLDER_ID_FORMULARIO = "1cgtia-u95riQzBiqIV4IOw6STXix39Ibry2wGIAWAiyiawdkyTL3Eoln33i82SNyB4dYt9ss"
FOLDER_ID_PAPELERA = "1t8yIQGQJ_Qi0c4ejDUMcr6H8Qz09-O9b"

# ============================================================
# AUTENTICACIÓN
# ============================================================
def crear_servicio():
    creds = service_account.Credentials.from_service_account_file(
        CRED_PATH,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

# ============================================================
# MOVER ARCHIVOS A PAPELERA_API
# ============================================================
def mover_a_papelera(service):
    print("\n🚀 Iniciando limpieza total de evidencias en Drive...\n")

    query = f"'{FOLDER_ID_FORMULARIO}' in parents and trashed = false"
    page_token = None
    movidos = 0

    while True:
        results = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, parents)",
            pageToken=page_token
        ).execute()

        files = results.get("files", [])

        if not files:
            break

        for file in files:
            file_id = file["id"]
            file_name = file["name"]
            padres = ",".join(file.get("parents", []))

            try:
                service.files().update(
                    fileId=file_id,
                    addParents=FOLDER_ID_PAPELERA,
                    removeParents=padres
                ).execute()

                movidos += 1
                print(f"🗑️ Movido → {file_name}")
                time.sleep(0.1)

            except Exception as e:
                print(f"❌ Error moviendo {file_name}: {e}")

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    print(f"\n✅ Total de archivos movidos a PAPELERA_API: {movidos}")
    print("🧹 Carpeta 'Sube aquí la evidencia' completamente vacía.")
# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    service = crear_servicio()
    mover_a_papelera(service)
