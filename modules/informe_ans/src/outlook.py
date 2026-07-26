import win32com.client as win32

from ..config.correos import (
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
    enviar_automaticamente=False,
):
    """
    Abre el correo para revisión o lo envía automáticamente.
    """

    if enviar_automaticamente:

        mail.Send()

    else:

        mail.Display()


# ==========================================================
# ABRIR CORREO
# ==========================================================

def abrir_correo_outlook(
    correo,
    html,
    enviar_automaticamente=False,

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
        mail,
        enviar_automaticamente=enviar_automaticamente,
    )