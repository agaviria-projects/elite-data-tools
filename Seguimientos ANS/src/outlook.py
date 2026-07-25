import win32com.client as win32

from config.correos import (
    MODO_PRUEBA,
    DESTINATARIOS_PRUEBA,
    COPIA_PRUEBA,
    DESTINATARIOS,
    COPIAS,
    IMPORTANCIA,
)


# ==========================================================
# CREAR OUTLOOK
# ==========================================================

def crear_outlook():
    """
    Crea una instancia de Outlook.
    """

    return win32.Dispatch(
        "Outlook.Application"
    )


# ==========================================================
# CREAR MENSAJE
# ==========================================================

def crear_mensaje(outlook):
    """
    Crea un nuevo correo.
    """

    return outlook.CreateItem(0)


# ==========================================================
# CONFIGURAR DESTINATARIOS
# ==========================================================

def configurar_destinatarios(
    mail,
    correo,
):
    """
    Configura TO y CC.
    """

    if MODO_PRUEBA:

        mail.To = ";".join(
            DESTINATARIOS_PRUEBA
        )

        mail.CC = ";".join(
            COPIA_PRUEBA
        )

    else:

        grupo = correo["grupo"]

        mail.To = ";".join(
            DESTINATARIOS.get(
                grupo,
                [],
            )
        )

        mail.CC = ";".join(
            COPIAS.get(
                grupo,
                [],
            )
        )


# ==========================================================
# CONFIGURAR MENSAJE
# ==========================================================

def configurar_mensaje(
    mail,
    correo,
    html,
):
    """
    Configura asunto,
    importancia y cuerpo HTML.
    """

    mail.Subject = correo["asunto"]

    mail.Importance = IMPORTANCIA

    mail.HTMLBody = html


# ==========================================================
# MOSTRAR O ENVIAR
# ==========================================================

def finalizar_envio(
    mail,
):
    """
    Muestra el correo en Outlook
    o lo envía automáticamente.
    """

    if MODO_PRUEBA:

        mail.Display()

    else:

        mail.Send()


# ==========================================================
# ABRIR CORREO
# ==========================================================

def abrir_correo_outlook(
    correo,
    html,
):
    """
    Construye completamente
    el correo de Outlook.
    """

    outlook = crear_outlook()

    mail = crear_mensaje(
        outlook
    )

    configurar_destinatarios(
        mail,
        correo,
    )

    configurar_mensaje(
        mail,
        correo,
        html,
    )

    finalizar_envio(
        mail
    )