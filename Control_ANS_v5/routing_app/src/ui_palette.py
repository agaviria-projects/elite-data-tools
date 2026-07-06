# src/ui_palette.py

def estado_colors():
    """
    Colores suaves (no chillones) para estados ANS.
    Ajustados para verse elegantes sobre fondos claros.
    """
    return {
        "VENCIDO": "#D92D20",        # rojo elegante
        "ALERTA_0": "#F79009",       # naranja
        "ALERTA": "#EAAA08",         # amarillo (más sobrio)
        "A TIEMPO": "#12B76A",       # verde
        "SIN FECHA": "#2E90FA",      # azul
        "OTRO": "#667085",           # gris fallback
    }


def canon_estado(x: str) -> str:
    s = str(x or "").strip().upper()

    if s == "VENCIDO":
        return "VENCIDO"

    if s in ("ALERTA_0", "ALERTA_0 DIAS", "ALERTA 0 DIAS", "ALERTA_0 DÍAS", "ALERTA 0 DÍAS"):
        return "ALERTA_0"

    if s == "ALERTA":
        return "ALERTA"

    if s in ("A TIEMPO", "ATIEMPO"):
        return "A TIEMPO"

    return "SIN FECHA"