# src/constants.py

CONCEPTOS_RUTEO = {"PROG", "PPRG"}

COLS_MIN = [
    "pedido",
    "concepto",
    "actividad",
    "zona",
    "estado",
    "lat",
    "lng",
    "direccion",
    "cliente",
    "celular",
]

ALIASES = {
    "area_operativa": "zona",
    "subzona": "subzona",
    "municipio": "municipio",

    "coordenadax": "lng",
    "coordenaday": "lat",

    "direccion": "direccion",
    "dirección": "direccion",
    "direc": "direccion",

    "nombre_cliente": "cliente",

    "celularcontacto": "celular_contacto",
    "telefonocontacto": "telefono_contacto",


    # ✅ NO MEZCLAR: mantener columnas separadas
    "celular_contacto": "celular_contacto",

    # ✅ unificar teléfonos en una sola columna
    "telefono_contacto": "telefono_contacto",
    "telefono": "telefono_contacto",
    "tel": "telefono_contacto",

    "coordenada_x": "lng",
    "coordenada_y": "lat",
    "long": "lng",
    "lon": "lng",
}
