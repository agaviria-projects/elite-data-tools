# ==========================================================
# CONFIGURACIÓN DE ZONAS - SEGUIMIENTO ANS
# ==========================================================
#
# revision=True:
#   Puede probarse en Modo revisión (Outlook abre, no envía).
#
# envio=True:
#   Puede utilizarse también en Envío automático.
#
# ORIENTE y NORDESTE quedan preparados para revisión,
# pero bloqueados para envío hasta autorización.
# ==========================================================

ZONAS = {
    "METROPOLITANA": {
        "revision": True,
        "envio": True,
        "correos_estimados": 4,
    },
    "SUROESTE": {
        "revision": True,
        "envio": True,
        "correos_estimados": 1,
    },
    "OCCIDENTE": {
        "revision": True,
        "envio": True,
        "correos_estimados": 1,
    },
    "ORIENTE": {
        "revision": True,
        "envio": False,
        "correos_estimados": 1,
    },
    "NORDESTE": {
        "revision": True,
        "envio": False,
        "correos_estimados": 1,
    },
}


def zona_habilitada_revision(zona: str) -> bool:
    cfg = ZONAS.get(
        str(zona).strip().upper(),
        {},
    )
    return bool(
        cfg.get("revision", False)
    )


def zona_habilitada_envio(zona: str) -> bool:
    cfg = ZONAS.get(
        str(zona).strip().upper(),
        {},
    )
    return bool(
        cfg.get("envio", False)
    )


def zonas_autorizadas_envio() -> tuple[str, ...]:
    return tuple(
        zona
        for zona, cfg in ZONAS.items()
        if cfg.get("envio", False)
    )
