# ==========================================================
# MODO DE DESTINATARIOS
# ==========================================================

# True:
# Usa DESTINATARIOS_PRUEBA y COPIA_PRUEBA en Pruebas.
#
# False:
# Usa DESTINATARIOS y COPIAS según cada grupo en Producción.
#
# IMPORTANTE:
# Esta variable controla únicamente los destinatarios.
# DataSuite controla si Outlook abre o envía el correo.

MODO_PRUEBA = False


# ==========================================================
# DESTINATARIOS DE PRUEBA
# ==========================================================

DESTINATARIOS_PRUEBA = [

    "d.leon@eliteingenieros.com.co",

]

COPIA_PRUEBA = [
    "h.gaviria@eliteingenieros.com.co"
]


# ==========================================================
# DESTINATARIOS PRODUCCIÓN
# ==========================================================

DESTINATARIOS = {

    "PUNTOS DE CONEXIÓN": [
        "c.oliveros@eliteingenieros.com.co",
        "g.gaviria@eliteingenieros.com.co",
        "j.arroyave@eliteingenieros.com.co",
        "y.sepulveda@eliteingenieros.com.co",
        "juan.ramirez@eliteingenieros.com.co",
    ],

    "PREPAGO_HV_ARTER": [
        "l.perez@eliteingenieros.com.co",
        "a.villegas@eliteingenieros.com.co",
        ""
    ],

    "MOVIMIENTO DE REDES": [
        "dairo.gil@eliteingenieros.com.co",
        "a.castano@eliteingenieros.com.co",
        "c.oliveros@eliteingenieros.com.co",
    ],

    "PARTICULARES": [
        "f.marin@eliteingenieros.com.co",
        "l.toro@eliteingenieros.com.co",
    ],

}


# ==========================================================
# COPIA PRODUCCIÓN
# ==========================================================

COPIAS = {

    "PUNTOS DE CONEXIÓN": [
        "j.barbosa@eliteingenieros.com.co",
        "d.leon@eliteingenieros.com.co",
    ],

    "PREPAGO_HV_ARTER": [
        "c.oliveros@eliteingenieros.com.co",
        "j.barbosa@eliteingenieros.com.co",
        "d.leon@eliteingenieros.com.co",
    ],

    "MOVIMIENTO DE REDES": [
        "j.barbosa@eliteingenieros.com.co",
        "f.marin@eliteingenieros.com.co",
        "r.bedoya@eliteingenieros.com.co",
        "d.leon@eliteingenieros.com.co",
    ],

    "PARTICULARES": [
        "c.oliveros@eliteingenieros.com.co",
        "j.barbosa@eliteingenieros.com.co",
        "d.leon@eliteingenieros.com.co",
    ],

}


# ==========================================================
# COPIA OCULTA
# ==========================================================

COPIA_OCULTA = [

]


# ==========================================================
# PRIORIDAD DEL CORREO
# ==========================================================

# 0 = Baja
# 1 = Normal
# 2 = Alta

IMPORTANCIA = 2


# ==========================================================
# CONFIGURACIÓN OUTLOOK
# ==========================================================

MOSTRAR_CORREO = True

ENVIAR_AUTOMATICAMENTE = False