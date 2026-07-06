import folium
import pandas as pd
from collections import defaultdict
from folium.plugins import MarkerCluster
from folium.features import DivIcon
import json
import colorsys


def _color_for(cid) -> str:
    try:
        cid_int = int(float(cid))
    except Exception:
        cid_int = abs(hash(str(cid))) % 10_000

    h = (cid_int * 0.618033988749895) % 1.0
    s = 0.75
    v = 0.95

    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def _jitter(i: int, base: float = 0.00006) -> float:
    # 0, +, -, ++, -- ...
    if i == 0:
        return 0.0
    k = (i + 1) // 2
    sign = 1 if i % 2 == 1 else -1
    return sign * k * base


def _inject_global_toast(m: folium.Map) -> None:
    # ✅ UID estable del mapa (Folium/Leaflet)
    uid = str(getattr(m, "get_name", lambda: f"m{abs(id(m))}")())

    # ✅ Bounds calculados en Python (si existen)
    bounds = getattr(m, "_streamlit_bounds", None)
    bounds_js = json.dumps(bounds) if bounds else "null"

    html = f"""
    <style>
      /* ✅ FIX ALTURA REAL DEL MAPA EN IFRAME */
      html, body {{
        height: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
      }}
      #{uid} {{
        width: 100% !important;
        height: 100% !important;
        min-height: 620px !important;
      }}

      #{uid}_toast_whatsapp {{
        position: fixed;
        left: 50%;
        bottom: 28px;
        transform: translateX(-50%);
        background: #25D366;
        color: #ffffff;
        padding: 10px 14px;
        border-radius: 999px;
        font-weight: 600;
        font-size: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.20);
        display: none;
        z-index: 999999;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
        letter-spacing: 0.2px;
      }}
    </style>

    <div id="{uid}_toast_whatsapp">✅ Datos copiados. Listos para pegar en WhatsApp</div>
        <script>
      // ✅ Guardar bounds (si vienen desde Python)
      window["{uid}_bounds"] = {bounds_js};

      // ✅ Bandera: si el usuario hace zoom/drag, NO volvemos a refit bounds
      //    PERO: si cambian los bounds (otro mapa/ruta), reseteamos esta bandera.
      window["{uid}_userInteracted"] = false;

      // ✅ Firma simple de bounds para detectar cambio de mapa/ruta
      function {uid}_boundsKey(b){{
        try {{
          if(!b || !Array.isArray(b)) return "";
          return b.map(function(p){{
            return [Number(p[0]).toFixed(6), Number(p[1]).toFixed(6)].join(",");
          }}).join("|");
        }} catch(e) {{
          return "";
        }}
      }}

      // ✅ guardamos key inicial
      window["{uid}_boundsKeyPrev"] = window["{uid}_boundsKeyPrev"] || {uid}_boundsKey(window["{uid}_bounds"]);

      // ✅ Toast scoped
      window["{uid}_showToastWA"] = function(msg){{
        var t = document.getElementById("{uid}_toast_whatsapp");
        if(!t) return;
        t.textContent = msg || '✅ Datos copiados. Listos para pegar en WhatsApp';
        t.style.display = 'block';
        t.style.opacity = '1';
        setTimeout(function(){{
          t.style.transition = 'opacity 0.35s ease';
          t.style.opacity = '0';
          setTimeout(function(){{
            t.style.display = 'none';
            t.style.transition = '';
            t.style.opacity = '1';
          }}, 380);
        }}, 1400);
      }}

      window["{uid}_fallbackCopy"] = function(text){{
        try{{
          var ta = document.createElement('textarea');
          ta.value = text;
          ta.style.position = 'fixed';
          ta.style.left = '-9999px';
          document.body.appendChild(ta);
          ta.focus();
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          window["{uid}_showToastWA"]('✅ Datos copiados. Listos para pegar en WhatsApp');
        }}catch(e){{
          window["{uid}_showToastWA"]('⚠️ No se pudo copiar automático. Copia manualmente.');
        }}
      }}

      window["{uid}_copyToClipboardWA"] = function(text){{
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(text).then(function(){{
            window["{uid}_showToastWA"]('✅ Datos copiados. Listos para pegar en WhatsApp');
          }}).catch(function(){{
            window["{uid}_fallbackCopy"](text);
          }});
        }} else {{
          window["{uid}_fallbackCopy"](text);
        }}
      }}

      // ✅ Leaflet map (scoped)
      function {uid}_findMap(){{
        try {{
          var mp = window["{uid}"];
          if (mp && typeof mp.invalidateSize === "function") return mp;
        }} catch(e) {{}}
        return null;
      }}

      function {uid}_wireUserEvents(mp){{
        try {{
          if (!mp || mp.__wired_user_events) return;
          mp.__wired_user_events = true;

          // ✅ si el usuario interactúa, bloqueamos el auto-refit
          mp.on("zoomstart", function(){{ window["{uid}_userInteracted"] = true; }});
          mp.on("dragstart", function(){{ window["{uid}_userInteracted"] = true; }});
          mp.on("movestart", function(){{ window["{uid}_userInteracted"] = true; }});
        }} catch(e) {{}}
      }}

      function {uid}_refit_bounds(mp){{
        try {{
          var b = window["{uid}_bounds"];
          if (!b || !mp || typeof mp.fitBounds !== "function") return;

          // ✅ Si cambian los bounds (otro mapa/ruta), volvemos a permitir auto-fit
          var keyNow = {uid}_boundsKey(b);
          var keyPrev = window["{uid}_boundsKeyPrev"] || "";

          if (keyNow && keyNow !== keyPrev) {{
            window["{uid}_userInteracted"] = false;
            window["{uid}_boundsKeyPrev"] = keyNow;
          }}

          // ✅ NO refit si el usuario ya interactuó en ESTE mismo mapa
          if (window["{uid}_userInteracted"]) return;

          mp.fitBounds(b, {{ padding: [40, 40] }});

          // ✅ Evita zoom exagerado (cap)
          try {{
            if (mp.getZoom && mp.setZoom) {{
              var z = mp.getZoom();
              if (z > 16) mp.setZoom(16, {{animate:false}});
            }}
          }} catch(e) {{}}

        }} catch(e) {{}}
      }}

      function {uid}_fix(){{
        try {{
          var mp = {uid}_findMap();
          if (!mp) return;

          {uid}_wireUserEvents(mp);

          // ✅ asegurar zoom con rueda dentro de iframe
          try {{
            if (mp.scrollWheelZoom && !mp.scrollWheelZoom.enabled()) mp.scrollWheelZoom.enable();
          }} catch(e) {{}}

          // 1) reflow
          window.dispatchEvent(new Event("resize"));

          // 2) tamaño
          mp.invalidateSize(true);

          // 3) refit inteligente (solo si bounds cambiaron o no hay interacción)
          {uid}_refit_bounds(mp);

          // 4) NO fuerces setZoom (esto suele causar “snapback” en tabs/iframes)
          //    (lo dejamos desactivado para estabilidad)
        }} catch(e) {{}}
      }}

      // Disparos iniciales
      setTimeout({uid}_fix, 180);
      setTimeout({uid}_fix, 420);
      setTimeout({uid}_fix, 900);
      setTimeout({uid}_fix, 1500);
      setTimeout({uid}_fix, 2400);

      document.addEventListener("visibilitychange", function(){{
        if (!document.hidden) {{
          setTimeout({uid}_fix, 120);
          setTimeout({uid}_fix, 380);
          setTimeout({uid}_fix, 900);
        }}
      }});

      try {{
        var obs = new IntersectionObserver(function(entries){{
          entries.forEach(function(en){{
            if (en.isIntersecting) {{
              setTimeout({uid}_fix, 80);
              setTimeout({uid}_fix, 260);
              setTimeout({uid}_fix, 900);
            }}
          }});
        }}, {{ threshold: 0.15 }});
        setTimeout(function(){{
          var root = document.getElementById("{uid}");
          if (root) obs.observe(root);
        }}, 350);
      }} catch(e) {{}}

      window.addEventListener("resize", function(){{
        setTimeout({uid}_fix, 120);
      }});
    </script>
    """
    m.get_root().html.add_child(folium.Element(html))

def _norm_estado(v) -> str:
    if v is None:
        return ""
    s = str(v).strip().upper()
    s = s.replace("DÍAS", "DIAS")
    return s


def _color_estado(estado: str) -> str:
    """
    Reglas solicitadas:
    - ALERTA      = amarillo
    - ALERTA_0    = naranja
    """
    e = _norm_estado(estado)

    if e == "VENCIDO":
        return "#E11D48"   # rojo
    if e in ("ALERTA_0", "ALERTA_0 DIAS", "ALERTA 0 DIAS"):
        return "#F97316"   # naranja (ALERTA_0)
    if e == "ALERTA":
        return "#FACC15"   # amarillo (ALERTA)
    if ("A TIEMPO" in e) or ("ATIEMPO" in e):
        return "#15803D"   # verde oscuro

    return "#15803D"       # gris


def _ordenar_ruta_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    ✅ Orden real de la ruta:
    - prioriza route_order
    - si no existe, usa ORDEN_VISITA
    - si nada existe, deja igual
    """
    if df is None or len(df) == 0:
        return df

    d = df.copy()
    if "route_order" in d.columns:
        d["route_order"] = pd.to_numeric(d["route_order"], errors="coerce")
        d = d.sort_values("route_order", ascending=True, na_position="last")
        return d

    if "ORDEN_VISITA" in d.columns:
        d["ORDEN_VISITA"] = pd.to_numeric(d["ORDEN_VISITA"], errors="coerce")
        d = d.sort_values("ORDEN_VISITA", ascending=True, na_position="last")
        return d

    return d


def construir_mapa_rutas(
    rutas: dict,
    bodega_lat: float,
    bodega_lng: float,
    color_mode: str = "cuadrilla",
    tile_mode: str = "calles",     # ✅ "calles" | "satelital"
    force_cluster: bool = False    # ✅ FIX: fuerza cluster (especial para “Todas”)
) -> folium.Map:

    # ✅ Base map sin tiles, para controlar capas
    m = folium.Map(location=[bodega_lat, bodega_lng], zoom_start=12, control_scale=True, tiles=None)

    # ✅ Capas base (Calles / Satelital)
    tile_mode_norm = str(tile_mode or "").strip().lower()
    want_sat = tile_mode_norm in ("satelital", "satellite", "imagery")

    osm = folium.TileLayer(
        tiles="OpenStreetMap",
        name="🗺️ Calles - Carreras",
        overlay=False,
        control=True,
        show=not want_sat,
    )

    sat = folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="🛰️ Satelital",
        overlay=False,
        control=True,
        show=want_sat,
    )

    labels = folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="🏘️ Barrios / Lugares",
        overlay=True,
        control=True,
        show=False,
        opacity=0.9,
    )

    osm.add_to(m)
    sat.add_to(m)
    labels.add_to(m)

    folium.Marker(
        [bodega_lat, bodega_lng],
        tooltip="BODEGA (Inicio/Fin)",
        popup=f"<b>BODEGA</b><br>Lat: {bodega_lat:.6f}<br>Lng: {bodega_lng:.6f}",
        icon=folium.Icon(color="black", icon="home", prefix="fa"),
    ).add_to(m)

    coord_count = defaultdict(int)

    for cid, df in rutas.items():
        if df is None or len(df) == 0:
            continue

        df = _ordenar_ruta_df(df)
        base_color = _color_for(cid)

        if "lat" not in df.columns or "lng" not in df.columns:
            continue

        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
        df = df.dropna(subset=["lat", "lng"]).copy().reset_index(drop=True)

        if df.empty:
            continue

        use_cluster = bool(force_cluster) or (len(df) > 25)

        if use_cluster:
            cluster = MarkerCluster(disableClusteringAtZoom=14, control=False)
            cluster.add_to(m)
            layer_target = cluster
        else:
            layer_target = m

        pts = [[bodega_lat, bodega_lng]]
        tmp_latlng = []

        for _, r in df.iterrows():
            lat = float(r["lat"])
            lng = float(r["lng"])

            key = (round(lat, 6), round(lng, 6))
            idx = coord_count[key]
            coord_count[key] += 1

            lat_j = lat + _jitter(idx)
            lng_j = lng + _jitter(idx)

            tmp_latlng.append((lat, lng, lat_j, lng_j))

        pts += [[lat_j, lng_j] for (_, _, lat_j, lng_j) in tmp_latlng]

        folium.PolyLine(
            pts,
            color=base_color,
            weight=6,
            opacity=0.9,
            tooltip=f"Cuadrilla {cid}"
        ).add_to(m)

        for i, ((lat, lng, lat_j, lng_j), (_, r)) in enumerate(zip(tmp_latlng, df.iterrows()), start=1):
            orden = i
            orden_raw = r.get("route_order", r.get("ORDEN_VISITA", None))

            pedido = r.get("pedido", r.get("PEDIDO", ""))
            cliente = r.get("cliente", "")
            direccion = r.get("direccion", "")
            actividad = r.get("ACTIVIDAD", r.get("actividad", "SIN DATO"))

            zona_geo = r.get("zona_geo", "")
            zona_oper = r.get("zona", "")

            celular = r.get("celular", "")
            if not celular:
                celular = r.get("celular_contacto", "")
            if not celular:
                celular = "SIN DATOS"

            def _safe(v, default="-"):
                if v is None:
                    return default
                try:
                    if pd.isna(v):
                        return default
                except Exception:
                    pass
                s = str(v).strip()
                return s if s else default

            pedido_txt = _safe(pedido)
            cliente_txt = _safe(cliente)
            direccion_txt = _safe(direccion)
            actividad_txt = _safe(actividad)
            zona_oper_txt = _safe(zona_oper)
            zona_geo_txt = _safe(zona_geo)
            celular_txt = _safe(celular)

            lat_txt = _safe(lat)
            lng_txt = _safe(lng)

            popup_html = f"""
            <div style="min-width:330px; max-width:520px; font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial;">
              <div style="padding:12px; border:1px solid #e5e7eb; border-radius:14px; background:#fff; box-shadow:0 10px 25px rgba(0,0,0,0.10);">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:10px;">
                  <div style="font-weight:800; font-size:14px;">Pedido: {pedido_txt}</div>
                  <div style="font-size:11px; padding:4px 8px; border-radius:999px; background:{base_color}; color:#fff; font-weight:800;">
                    #{orden} | C{cid}
                  </div>
                </div>

                <div style="margin-top:8px; font-size:12px; line-height:1.35;">
                  <div><b>Cliente:</b> {cliente_txt}</div>
                  <div><b>Dirección:</b> {direccion_txt}</div>
                  <div><b>Actividad:</b> {actividad_txt}</div>
                  <div><b>Zona operativa:</b> {zona_oper_txt}</div>
                  <div><b>Zona geo (por coordenadas):</b> {zona_geo_txt}</div>
                  <div><b>Celular:</b> {celular_txt}</div>
                  <div><b>Coords:</b> {lat_txt}, {lng_txt}</div>
                  <div style="margin-top:6px; font-size:11px; color:#6b7280;">
                    <b>Orden real:</b> {_safe(orden_raw, '-') }
                  </div>
                </div>

                <div style="display:flex; gap:10px; margin-top:10px;">
                  <button
                    onclick="window.open('https://www.google.com/maps?q={lat_j},{lng_j}','_blank');"
                    style="flex:1; background:#f3f4f6; color:#111827; border:1px solid #e5e7eb; padding:9px 10px; border-radius:10px; font-weight:600; cursor:pointer;"
                  >📍 Ver mapa</button>
                </div>
              </div>
            </div>
            """

            estado_val = r.get("estado_ans", r.get("estado", ""))
            estado_txt = _safe(estado_val)

            tooltip = f"#{orden} | C{cid} | {estado_txt} | {actividad_txt} | Pedido {pedido_txt} | Oper: {zona_oper_txt} | Geo: {zona_geo_txt}"

            if "estado" in str(color_mode).lower():
                color_marker = _color_estado(estado_val)
            else:
                color_marker = _color_for(cid)

            # ✅ Mostrar números también al "expandir" clusters (spiderfy)
            # ✅ Mantiene protección de rendimiento para casos MUY grandes
            usar_numero_en_cluster = (not bool(force_cluster)) or (len(df) <= 220)

            if usar_numero_en_cluster:
                folium.Marker(
                    [lat_j, lng_j],
                    tooltip=tooltip,
                    popup=folium.Popup(popup_html, max_width=560),
                    icon=folium.DivIcon(
                         html=f"""
                        <div style="
                            position: relative;
                            width: 34px;
                            height: 46px;
                        ">
                            <div style="
                                position: absolute;
                                top: 0;
                                left: 50%;
                                width: 30px;
                                height: 30px;
                                background: {color_marker};
                                border-radius: 50% 50% 50% 0;
                                transform: translateX(-50%) rotate(-45deg);
                                border: 2px solid #ffffff;
                                box-shadow: 0 4px 10px rgba(0,0,0,0.30);
                            "></div>

                            <div style="
                                position: absolute;
                                top: 5px;
                                left: 50%;
                                width: 14px;
                                height: 14px;
                                background: rgba(255,255,255,0.20);
                                border-radius: 50%;
                                transform: translateX(-50%);
                                z-index: 2;
                            "></div>

                            <div style="
                                position: absolute;
                                top: 2px;
                                left: 50%;
                                width: 30px;
                                height: 30px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transform: translateX(-50%);
                                color: #ffffff;
                                font-weight: 900;
                                font-size: 13px;
                                font-family: Arial, sans-serif;
                                z-index: 5;
                                text-shadow: 0 1px 3px rgba(0,0,0,0.65);
                            ">{orden}</div>
                        </div>
                        """
                    ),
                ).add_to(layer_target)
            else:
                # 🔒 Fallback para "Todas" con muchos puntos: más liviano
                folium.CircleMarker(
                    location=[lat_j, lng_j],
                    radius=5,
                    color=color_marker,
                    fill=True,
                    fill_color=color_marker,
                    fill_opacity=0.95,
                    tooltip=tooltip,
                    popup=folium.Popup(popup_html, max_width=560),
                ).add_to(layer_target)       
    folium.LayerControl(collapsed=True).add_to(m)

    # ✅ Bounds (Python) + guardado para JS (para re-fit cuando Streamlit rerun rompe Leaflet)
    try:
        bounds = [[bodega_lat, bodega_lng]]
        for _, dfb in rutas.items():
            if dfb is None or len(dfb) == 0:
                continue
            if "lat" in dfb.columns and "lng" in dfb.columns:
                latv = pd.to_numeric(dfb["lat"], errors="coerce")
                lngv = pd.to_numeric(dfb["lng"], errors="coerce")
                ok = latv.notna() & lngv.notna()
                bounds += [[float(a), float(b)] for a, b in zip(latv[ok], lngv[ok])]

        if len(bounds) >= 2:
            m._streamlit_bounds = bounds
            m.fit_bounds(bounds)
        else:
            m._streamlit_bounds = None
    except Exception:
        m._streamlit_bounds = None

    # ✅ Inyecta JS + CSS al final (con bounds ya disponibles)
    _inject_global_toast(m)

    return m