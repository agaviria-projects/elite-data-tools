from scripts.config import CODIGOS_EXCLUIR

# ==========================================
# 🧹 LIMPIAR CODIGOS
# ==========================================

def limpiar_codigos(df):

    # ======================================
    # VALIDAR COLUMNA ORIGINAL
    # ======================================

    if "Código" not in df.columns:

        raise ValueError(
            "❌ La columna 'Código' no existe."
        )

    # ======================================
    # LIMPIAR CODIGO
    # ======================================

    df["Código"] = (

        df["Código"]

        .astype(str)

        .str.strip()

        .str.upper()

    )

    # ======================================
    # NORMALIZAR CODIGOS
    # SOLO SI INICIA EN NUMERO
    # ======================================

    df["Código"] = df["Código"].str.replace(

        r'^([0-9]+)[A-Z]+$',

        r'\1',

        regex=True

    )

    # ======================================
    # EXCLUIR CODIGOS
    # ======================================

    df = df[
        ~df["Código"].isin(CODIGOS_EXCLUIR)
    ]

    # ======================================
    # LIMPIAR NULOS
    # ======================================

    df = df[
        df["Código"].notna()
    ]

    # ======================================
    # ELIMINAR VACIOS
    # ======================================

    df = df[
        df["Código"] != ""
    ]

    # ======================================
    # RESETEAR INDICE
    # ======================================

    df = df.reset_index(
        drop=True
    )

    return df