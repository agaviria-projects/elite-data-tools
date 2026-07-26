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
    Configura los destinatarios principales y las copias.

    MODO_PRUEBA determina únicamente a quién se dirige
    el mensaje. No controla si el correo se abre o se envía.
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
    Configura asunto, importancia y cuerpo HTML.
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
    Abre el correo para revisión o lo envía directamente.

    enviar_automaticamente=False:
        Abre el mensaje en Outlook mediante Display().

    enviar_automaticamente=True:
        Envía el mensaje directamente mediante Send().
    """

    if enviar_automaticamente:

        mail.Send()

    else:

        mail.Display()


# ==========================================================
# PROCESAR CORREO OUTLOOK
# ==========================================================

def abrir_correo_outlook(
    correo,
    html,
    enviar_automaticamente=False,
):
    """
    Construye completamente el correo de Outlook.

    El parámetro enviar_automaticamente permite utilizar
    la misma función para los dos modos de DataSuite.
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