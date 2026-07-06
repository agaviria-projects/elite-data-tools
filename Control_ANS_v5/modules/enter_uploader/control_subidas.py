import csv
import os
from datetime import datetime

CONTROL_FILE = "data_master/control_enter_subidas.csv"

CAMPOS = [
    "archivo",
    "hash",
    "fecha_proceso",
    "estado",
    "detalle"
]

def inicializar_control():
    os.makedirs(os.path.dirname(CONTROL_FILE), exist_ok=True)

    if not os.path.exists(CONTROL_FILE):
        with open(CONTROL_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CAMPOS)
            writer.writeheader()

def cargar_hashes_existentes():
    if not os.path.exists(CONTROL_FILE):
        return set()

    with open(CONTROL_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return set(row["hash"] for row in reader if row.get("hash"))

def registrar_evento(archivo, hash_archivo, estado, detalle=""):
    with open(CONTROL_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writerow({
            "archivo": archivo,
            "hash": hash_archivo,
            "fecha_proceso": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estado": estado,
            "detalle": detalle
        })
