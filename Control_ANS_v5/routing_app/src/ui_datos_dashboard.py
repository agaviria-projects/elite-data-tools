# src/ui_datos_dashboard.py
import pandas as pd
import streamlit as st
import plotly.express as px

from src.ui_palette import estado_colors, canon_estado


def _pick_col(df_: pd.DataFrame, candidates: list[str]) -> str | None:
    if df_ is None or df_.empty:
        return None
    cols = list(df_.columns)
    up_map = {str(c).strip().upper(): c for c in cols}
    for cand in candidates:
        k = str(cand).strip().upper()
        if k in up_map:
            return up_map[k]
    return None


def render_datos_dashboard(df_in: pd.DataFrame, height_each: int = 260) -> pd.DataFrame:
    """
    Panel compacto a la izquierda:
    - Filtros locales: Zona + Estado
    - Barras horizontales con % y colores por estado
    - Devuelve df_filtrado_local para alimentar la tabla
    """
    if df_in is None or df_in.empty:
        st.info("No hay datos para el dashboard.")
        return df_in

    df = df_in.copy()

    col_zona = _pick_col(df, ["ZONA", "zona"])
    col_estado = _pick_col(df, ["ESTADO", "estado"])

    # Normaliza estado para colores/orden
    if col_estado:
        df["_estado_canon"] = df[col_estado].apply(canon_estado)
    else:
        df["_estado_canon"] = "SIN FECHA"

    # -------------------------
    # Filtros locales (solo TAB DATOS)
    # -------------------------
    st.markdown("### 📊 Dashboard (Datos)")
    st.caption("Filtros locales para explorar sin afectar el resto de tabs.")

    zonas_opts = sorted(df[col_zona].dropna().astype(str).unique().tolist()) if col_zona else []
    estados_order = ["VENCIDO", "ALERTA_0", "ALERTA", "A TIEMPO", "SIN FECHA"]

    f1, f2 = st.columns(2)
    with f1:
        zona_sel = st.multiselect(
            "ZONA (local)",
            zonas_opts,
            default=[],
            key="dash_zona_local"
        )
    with f2:
        estado_sel = st.multiselect(
            "ESTADO (local)",
            estados_order,
            default=[],
            key="dash_estado_local"
        )

    df_local = df.copy()
    if zona_sel and col_zona:
        df_local = df_local[df_local[col_zona].astype(str).isin(zona_sel)].copy()

    if estado_sel:
        df_local = df_local[df_local["_estado_canon"].isin(estado_sel)].copy()

    total_local = len(df_local)

    # -------------------------
    # KPI mini
    # -------------------------
    c1, c2 = st.columns(2)
    c1.metric("Pedidos (vista)", f"{total_local:,}")
    c2.metric("Zonas", f"{df_local[col_zona].nunique() if col_zona else 0:,}")

    st.markdown("---")

    # -------------------------
    # Chart 1: Pedidos por ZONA (horizontal, compacto)
    # -------------------------
    if col_zona:
        z = (
            df_local[col_zona]
            .fillna("SIN ZONA")
            .astype(str)
            .value_counts()
            .reset_index()
        )
        z.columns = ["zona", "pedidos"]
        z["%"] = (z["pedidos"] / max(1, total_local) * 100).round(1)
        z = z.sort_values("pedidos", ascending=True)

        fig_z = px.bar(
            z,
            x="pedidos",
            y="zona",
            orientation="h",
            text=z["%"].astype(str) + "%",
        )
        fig_z.update_traces(textposition="inside", insidetextanchor="middle")
        fig_z.update_layout(
            height=height_each,
            margin=dict(l=10, r=10, t=35, b=10),
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
        )
        fig_z.update_xaxes(showgrid=False, visible=False)
        fig_z.update_yaxes(tickfont=dict(size=12))
        st.markdown("#### 🧭 Pedidos por zona")
        st.plotly_chart(fig_z, use_container_width=True)
    else:
        st.warning("No encontré columna ZONA para el gráfico por zona.")

    st.markdown("---")

    # -------------------------
    # Chart 2: Pedidos por ESTADO (horizontal, colores por estado + %)
    # -------------------------
    colors = estado_colors()

    e = (
        df_local["_estado_canon"]
        .fillna("SIN FECHA")
        .astype(str)
        .value_counts()
        .reindex(["VENCIDO", "ALERTA_0", "ALERTA", "A TIEMPO", "SIN FECHA"], fill_value=0)
        .reset_index()
    )
    e.columns = ["estado", "pedidos"]
    e["%"] = (e["pedidos"] / max(1, total_local) * 100).round(1)

    # Para que quede bien en horizontal (arriba VENCIDO, abajo SIN FECHA)
    e = e.sort_values("pedidos", ascending=True)

    fig_e = px.bar(
        e,
        x="pedidos",
        y="estado",
        orientation="h",
        text=e["%"].astype(str) + "%",
        color="estado",
        color_discrete_map={
            "VENCIDO": colors["VENCIDO"],
            "ALERTA_0": colors["ALERTA_0"],
            "ALERTA": colors["ALERTA"],
            "A TIEMPO": colors["A TIEMPO"],
            "SIN FECHA": colors["SIN FECHA"],
        },
    )
    fig_e.update_traces(textposition="inside", insidetextanchor="middle")
    fig_e.update_layout(
        height=height_each,
        margin=dict(l=10, r=10, t=35, b=10),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
    )
    fig_e.update_xaxes(showgrid=False, visible=False)
    fig_e.update_yaxes(tickfont=dict(size=12))
    st.markdown("#### 🚦 Pedidos por estado (colores ANS)")
    st.plotly_chart(fig_e, use_container_width=True)

    # Limpieza columna interna
    df_local = df_local.drop(columns=["_estado_canon"], errors="ignore")

    return df_local