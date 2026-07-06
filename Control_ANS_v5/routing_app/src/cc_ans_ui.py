from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


PLOTLY_CFG = {"displayModeBar": False, "responsive": True}


def _asegurar_css_cc_ans():
    st.markdown("""
    <style>
    :root{
        --cc-bg-page: #F3F6FA;
        --cc-card: #FFFFFF;
        --cc-card-2: #F8FAFC;
        --cc-border: #E2E8F0;
        --cc-shadow: 0 10px 28px rgba(15,23,42,.06);

        --cc-text: #0F172A;
        --cc-text-soft: #475569;
        --cc-text-muted: #64748B;

        --cc-navy: #0F172A;
        --cc-navy-2: #132238;

        --cc-slate: #64748B;
        --cc-emerald: #059669;
        --cc-amber: #D97706;
        --cc-sky: #0284C7;
        --cc-rose: #DC2626;
    }

    .block-container{
        padding-top: 1.2rem !important;
        padding-bottom: 1.2rem !important;
    }

    .cc-header-card{
        background: linear-gradient(90deg, var(--cc-navy) 0%, var(--cc-navy-2) 100%);
        border: 1px solid rgba(148,163,184,.14);
        border-radius: 18px;
        padding: 18px 20px 16px 20px;
        box-shadow: 0 12px 28px rgba(2,6,23,.14);
        margin-bottom: 14px;
    }

    .cc-header-title{
        font-size: 18px;
        font-weight: 800;
        color: #F8FAFC;
        margin: 0 0 4px 0;
        letter-spacing: .2px;
    }

    .cc-header-sub{
        font-size: 12px;
        color: rgba(226,232,240,.78);
        margin: 0;
        line-height: 1.45;
    }

    .cc-chip{
        display:inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: 800;
        margin-top: 10px;
        background: rgba(255,255,255,.08);
        color: #E2E8F0;
        border: 1px solid rgba(255,255,255,.12);
        letter-spacing: .2px;
    }

    .cc-kpi-card{
        background: var(--cc-card);
        border: 1px solid var(--cc-border);
        border-radius: 16px;
        padding: 14px 14px 12px 14px;
        box-shadow: var(--cc-shadow);
        position: relative;
        overflow: hidden;
        min-height: 104px;
        height: 100%;
    }

    .cc-kpi-topbar{
        height: 3px;
        border-radius: 999px;
        width: 100%;
        margin: 0 0 12px 0;
        opacity: .95;
    }

    .cc-kpi-title{
        font-size: 11px;
        font-weight: 800;
        color: var(--cc-text-muted);
        margin: 0;
        line-height: 1.2;
        letter-spacing: .15px;
    }

    .cc-kpi-value{
        font-size: 30px;
        font-weight: 800;
        color: var(--cc-text);
        line-height: 1.02;
        margin-top: 8px;
    }

    .cc-kpi-sub{
        font-size: 10px;
        color: #94A3B8;
        margin-top: 7px;
        line-height: 1.35;
    }

    .cc-block{
        background: var(--cc-card);
        border: 1px solid var(--cc-border);
        border-radius: 18px;
        padding: 16px 16px 14px 16px;
        box-shadow: var(--cc-shadow);
        margin-bottom: 14px;
    }

    .cc-block-title{
        font-size: 14px;
        font-weight: 800;
        color: var(--cc-text);
        margin: 0 0 4px 0;
        letter-spacing: .15px;
    }

    .cc-block-sub{
        font-size: 11px;
        color: var(--cc-text-muted);
        margin: 0 0 12px 0;
        line-height: 1.45;
    }

    .cc-footer{
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #EEF2F7;
        font-size: 11px;
        color: #64748B;
        line-height: 1.45;
    }

    .cc-cob-wrap{
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 18px 18px 16px 18px;
    }

    .cc-cob-label{
        font-size: 12px;
        font-weight: 700;
        color: var(--cc-text-soft);
        margin-bottom: 2px;
    }

    .cc-cob-big{
        font-size: 42px;
        font-weight: 800;
        color: var(--cc-text);
        line-height: 1;
        margin: 6px 0 8px 0;
    }

    .cc-cob-meta{
        font-size: 11px;
        color: var(--cc-text-muted);
        line-height: 1.45;
        margin-top: 6px;
    }

    .cc-progress{
        width: 100%;
        height: 10px;
        background: #E9EEF5;
        border-radius: 999px;
        overflow: hidden;
        margin-top: 14px;
        margin-bottom: 12px;
    }

    .cc-progress-bar{
        height: 100%;
        border-radius: 999px;
        transition: width .35s ease;
    }

    .cc-status{
        display: inline-block;
        margin-top: 6px;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .1px;
    }

    div[data-testid="stDataFrame"]{
        border-radius: 14px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 8px 22px rgba(15,23,42,.05) !important;
        overflow: hidden !important;
    }

    div[data-testid="stDataFrame"] [role="columnheader"]{
        background: #F8FAFC !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border-bottom: 1px solid #E2E8F0 !important;
        justify-content: center !important;
        text-align: center !important;
    }

    div[data-testid="stDataFrame"] [role="gridcell"]{
        background: #FFFFFF !important;
        color: #0F172A !important;
        justify-content: center !important;
        text-align: center !important;
        align-items: center !important;
        border-top: 1px solid #F1F5F9 !important;
    }

    div[data-testid="stDataFrame"] [role="gridcell"] > div,
    div[data-testid="stDataFrame"] [role="columnheader"] > div{
        width: 100% !important;
        justify-content: center !important;
        text-align: center !important;
    }

    div[data-testid="stPlotlyChart"]{
        border-radius: 14px;
    }
    </style>
    """, unsafe_allow_html=True)


def _render_block_header(titulo: str, subtitulo: str):
    st.markdown(
        f"""
        <div class="cc-block-title">{titulo}</div>
        <div class="cc-block-sub">{subtitulo}</div>
        """,
        unsafe_allow_html=True
    )


def render_kpis_centro_control(resumen: dict):
    total_plan = int(resumen.get("total_plan", 0) or 0)
    reportados = int(resumen.get("reportados", 0) or 0)
    sin_reporte = int(resumen.get("sin_reporte", 0) or 0)
    pct_reporte = float(resumen.get("pct_reporte", 0.0) or 0.0)
    criticos = int(resumen.get("criticos", 0) or 0)

    data = [
        ("#94A3B8", "Plan base", f"{total_plan:,}", "Pedidos programados del día"),
        ("#059669", "Reportados", f"{reportados:,}", "Pedidos con reporte técnico"),
        ("#D97706", "Sin reporte", f"{sin_reporte:,}", "Pedidos pendientes de reporte"),
        ("#0284C7", "Cobertura", f"{pct_reporte:.1f}%", "Cobertura sobre el plan base"),
        ("#DC2626", "Riesgo crítico", f"{criticos:,}", "Pedidos en riesgo de vencer"),
    ]

    cols = st.columns(5, gap="small")

    for col, (color, title, value, sub) in zip(cols, data):
        with col:
            st.markdown(
                f"""
                <div class="cc-kpi-card">
                    <div class="cc-kpi-topbar" style="background:{color};"></div>
                    <div class="cc-kpi-title">{title}</div>
                    <div class="cc-kpi-value">{value}</div>
                    <div class="cc-kpi-sub">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_cobertura_ejecutiva(resumen: dict):
    total_plan = int(resumen.get("total_plan", 0) or 0)
    reportados = int(resumen.get("reportados", 0) or 0)
    pct_reporte = max(0.0, min(float(resumen.get("pct_reporte", 0.0) or 0.0), 100.0))
    meta = 85.0

    if pct_reporte >= 85:
        color = "#059669"
        estado = "Cobertura saludable"
        estado_bg = "rgba(5,150,105,.10)"
        estado_fg = "#047857"
        estado_bd = "rgba(5,150,105,.18)"
    elif pct_reporte >= 60:
        color = "#D97706"
        estado = "Cobertura en seguimiento"
        estado_bg = "rgba(217,119,6,.10)"
        estado_fg = "#B45309"
        estado_bd = "rgba(217,119,6,.18)"
    else:
        color = "#DC2626"
        estado = "Cobertura baja"
        estado_bg = "rgba(220,38,38,.10)"
        estado_fg = "#B91C1C"
        estado_bd = "rgba(220,38,38,.18)"

    st.markdown(
        f"""
        <div class="cc-cob-wrap">
            <div class="cc-cob-label">Cobertura del plan reportado</div>
            <div class="cc-cob-big">{pct_reporte:.1f}%</div>
            <div class="cc-cob-meta">
                {reportados:,} de {total_plan:,} pedidos del plan base ya cuentan con reporte técnico.
            </div>
            <div class="cc-progress">
                <div class="cc-progress-bar" style="width:{pct_reporte:.1f}%; background:{color};"></div>
            </div>
            <div class="cc-cob-meta">Meta operativa: {meta:.0f}%</div>
            <div class="cc-status" style="background:{estado_bg}; color:{estado_fg}; border:1px solid {estado_bd};">
                {estado}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def _resumen_por_zona_geo(df_seguimiento: pd.DataFrame) -> pd.DataFrame:
    if df_seguimiento is None or df_seguimiento.empty:
        return pd.DataFrame(columns=["zona_geo", "reportados", "sin_reporte", "criticos"])

    df = df_seguimiento.copy()
    df["zona_geo"] = df["zona_actual"].fillna("").astype(str).str.strip()
    df["zona_geo"] = df["zona_geo"].replace("", "SIN ZONA")

    out = (
        df.groupby("zona_geo", dropna=False)
        .agg(
            reportados=("reportado_tecnico", "sum"),
            sin_reporte=("reportado_tecnico", lambda x: int((1 - x).sum())),
            criticos=("nivel_riesgo", lambda x: int((x == "CRITICO").sum()))
        )
        .reset_index()
    )

    out = out.sort_values(["sin_reporte", "criticos", "reportados"], ascending=[False, False, False])
    return out


def render_barras_zona_geo(df_seguimiento: pd.DataFrame):
    df_z = _resumen_por_zona_geo(df_seguimiento)

    if df_z.empty:
        st.info("No hay datos de seguimiento para mostrar por zona geográfica.")
        return

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Sin reporte",
        y=df_z["zona_geo"],
        x=df_z["sin_reporte"],
        orientation="h",
        marker=dict(color="#D97706"),
        hovertemplate="<b>%{y}</b><br>Sin reporte: %{x}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        name="Reportados",
        y=df_z["zona_geo"],
        x=df_z["reportados"],
        orientation="h",
        marker=dict(color="#CBD5E1"),
        hovertemplate="<b>%{y}</b><br>Reportados: %{x}<extra></extra>"
    ))

    fig.update_layout(
        barmode="stack",
        height=max(260, 80 + len(df_z) * 42),
        margin=dict(l=8, r=8, t=10, b=8),
        xaxis_title=None,
        yaxis_title=None,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="left",
            x=0,
            title=None,
            font=dict(size=10, color="#475569")
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#334155"},
        bargap=0.32,
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,.15)",
        zeroline=False,
        showline=False,
        tickfont=dict(size=10, color="#64748B")
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(size=10, color="#334155"),
        categoryorder="total ascending"
    )

    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG)


def render_riesgo_zona_geo(df_seguimiento: pd.DataFrame):
    df_z = _resumen_por_zona_geo(df_seguimiento)

    if df_z.empty:
        st.info("No hay datos de riesgo por zona geográfica.")
        return

    df_plot = df_z.sort_values("criticos", ascending=True)

    fig = px.bar(
        df_plot,
        x="criticos",
        y="zona_geo",
        orientation="h",
        text="criticos"
    )

    fig.update_traces(
        marker_color="#DC2626",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Riesgo crítico: %{x}<extra></extra>"
    )

    fig.update_layout(
        height=max(280, 80 + len(df_plot) * 42),
        margin=dict(l=8, r=18, t=10, b=8),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#334155"},
        bargap=0.40,
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,.15)",
        zeroline=False,
        tickfont=dict(size=10, color="#64748B")
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(size=10, color="#334155")
    )

    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG)


def render_tabla_seguimiento(df_seguimiento: pd.DataFrame):
    if df_seguimiento is None or df_seguimiento.empty:
        st.info("No hay seguimiento para mostrar.")
        return

    df = df_seguimiento.copy()

    if "reportado_tecnico" in df.columns:
        df["reportado_tecnico"] = df["reportado_tecnico"].map({1: "Sí", 0: "No"}).fillna("No")

    cols = [
        "id_pedido",
        "zona_actual",
        "reportado_tecnico",
        "estado_actual_campo",
        "nombre_tecnico",
        "marca_temporal",
        "actividad_campo",
        "nivel_riesgo",
    ]
    cols = [c for c in cols if c in df.columns]

    st.dataframe(df[cols], use_container_width=True, height=420, hide_index=True)


def render_centro_control_ans(df_seguimiento: pd.DataFrame, resumen: dict):
    _asegurar_css_cc_ans()

    st.markdown("""
    <div class="cc-header-card">
        <div class="cc-header-title">Centro de Control ANS</div>
        <div class="cc-header-sub">
            Monitoreo ejecutivo del plan base, avance de reporte técnico y focos de riesgo operativo.
        </div>
        <div class="cc-chip">Vista ejecutiva</div>
    </div>
    """, unsafe_allow_html=True)

    render_kpis_centro_control(resumen)

    c1, c2 = st.columns([1.05, 1], gap="medium")

    with c1:
        with st.container():
            st.markdown('<div class="cc-block">', unsafe_allow_html=True)
            _render_block_header(
                "Cobertura del plan",
                "Porcentaje del plan base que ya cuenta con reporte del equipo técnico."
            )
            render_cobertura_ejecutiva(resumen)
            st.markdown(
                '<div class="cc-footer">Indicador principal para seguimiento diario del cumplimiento del plan.</div></div>',
                unsafe_allow_html=True
            )

    with c2:
        with st.container():
            st.markdown('<div class="cc-block">', unsafe_allow_html=True)
            _render_block_header(
                "Cobertura por zona geográfica",
                "Comparativo entre pedidos reportados y pendientes por zona."
            )
            render_barras_zona_geo(df_seguimiento)
            st.markdown(
                '<div class="cc-footer">Permite ubicar rezagos territoriales y priorizar seguimiento operativo.</div></div>',
                unsafe_allow_html=True
            )

    with st.container():
        st.markdown('<div class="cc-block">', unsafe_allow_html=True)
        _render_block_header(
            "Riesgo crítico por zona geográfica",
            "Zonas con mayor volumen de pedidos clasificados en estado crítico."
        )
        render_riesgo_zona_geo(df_seguimiento)
        st.markdown(
            '<div class="cc-footer">Útil para priorizar acciones tácticas y redistribución de carga.</div></div>',
            unsafe_allow_html=True
        )

    with st.container():
        st.markdown('<div class="cc-block">', unsafe_allow_html=True)
        _render_block_header(
            "Seguimiento operativo del plan",
            "Detalle por pedido para validación diaria, trazabilidad y soporte de control."
        )
        render_tabla_seguimiento(df_seguimiento)
        st.markdown(
            '<div class="cc-footer">Vista operativa para revisión de reporte técnico, estado y nivel de riesgo.</div></div>',
            unsafe_allow_html=True
        )