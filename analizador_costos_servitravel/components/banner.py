import base64
from datetime import datetime
from pathlib import Path

import streamlit as st


# ==========================================================
# BANNER CORPORATIVO ELITE
# ==========================================================

def render_banner(
    titulo: str,
    subtitulo: str,
    icono: str = "📊",
    estado: str = "Sistema Activo",
):

    # ------------------------------------------------------
    # FECHA
    # ------------------------------------------------------

    ahora = datetime.now()

    fecha = ahora.strftime("%d/%m/%Y")

    hora = ahora.strftime("%I:%M %p")

    # ------------------------------------------------------
    # LOGO
    # ------------------------------------------------------

    logo_html = ""

    logo = (
        Path(__file__).parent.parent
        / "assets"
        / "logo_analizador.png"
    )

    if logo.exists():

        with open(logo, "rb") as f:

            img = base64.b64encode(
                f.read()
            ).decode()

        logo_html = f"""
            <img
                src="data:image/png;base64,{img}"
                style="
                    height:58px;
                    margin-right:18px;
                    filter:drop-shadow(
                        0 0 8px rgba(255,255,255,.25)
                    );
                "
            >
        """

    else:

        logo_html = f"""
            <div
                style="
                    font-size:46px;
                    margin-right:18px;
                "
            >
                {icono}
            </div>
        """

    # ------------------------------------------------------
    # HTML
    # ------------------------------------------------------

    st.markdown(

        f"""

<div class="banner">

    <div class="banner-left">

        <div class="banner-title">

            {logo_html}

            {titulo}

        </div>

        <div class="banner-sub">

            {subtitulo}

        </div>

    </div>

    <div
        style="
            display:flex;
            flex-direction:column;
            align-items:flex-end;
            gap:10px;
        "
    >

        <div class="banner-badge">

            🟢 {estado}

        </div>

        <div
            style="
                color:white;
                font-size:14px;
                opacity:.95;
                text-align:right;
            "
        >

            {fecha}<br>

            {hora}

        </div>

    </div>

</div>

        """,

        unsafe_allow_html=True,

    )