import os
import hashlib

def listar_pdfs(ruta_base):
    archivos = []
    for root, _, files in os.walk(ruta_base):
        for f in files:
            if f.lower().endswith((".pdf", ".zip")):
                archivos.append(os.path.join(root, f))
    return archivos

def calcular_hash_archivo(ruta_archivo):
    sha256 = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            sha256.update(bloque)
    return sha256.hexdigest()
