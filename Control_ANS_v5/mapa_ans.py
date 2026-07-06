
"""
MAPA ANS PROFESIONAL – v8.3 (BLINDADO + AGRUPACIÓN + TOOLTIP PRO)
Google Maps + Panel ANS + Filtros + Actividad + Tooltip Multi-Estado
Héctor + IA – 2025
"""

import pandas as pd
import folium
from branca.element import Template, MacroElement
from pathlib import Path
import re
import sys
import json

# ============================================================
# 0. FIX UTF-8
# ============================================================
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ============================================================
# 1. RUTAS BASE
# ============================================================
script_path = Path(__file__).resolve()
base_path = script_path.parent

ruta_fenix = base_path / "data_clean" / "FENIX_ANS.xlsx"

ruta_salida_onedrive = Path(
    r"C:/Users/hector.gaviria/OneDrive - Elite Ingenieros SAS/Control_ANS/mapa_ans.html"
)
ruta_salida_proyecto = base_path / "data_output" / "mapa_ans.html"
ruta_log_errores = base_path / "data_output" / "errores_geolocalizacion.txt"

ruta_salida_onedrive.parent.mkdir(exist_ok=True)
ruta_salida_proyecto.parent.mkdir(exist_ok=True)

# ============================================================
# 2. CARGAR FENIX_ANS
# ============================================================
df = pd.read_excel(ruta_fenix, sheet_name="FENIX_ANS", dtype=str)
df.columns = df.columns.str.upper().str.strip()

# 🔒 Normalización ultra segura
df["ESTADO"] = df["ESTADO"].astype(str).str.normalize("NFKC")

print(f"[INFO] Registros cargados desde FENIX_ANS.xlsx: {len(df)}")

# ============================================================
# 2.1 NORMALIZAR ESTADO (BLINDADO)
# ============================================================
def normalizar_estado(e):
    if not isinstance(e, str):
        return "SIN FECHA"

    e = re.sub(r"[\u200B-\u200D\uFEFF\u00A0]", "", e)
    e = " ".join(e.split())

    e = (
        e.upper()
         .replace("Á","A").replace("É","E")
         .replace("Í","I").replace("Ó","O")
         .replace("Ú","U")
    )

    if re.search(r"\bALERTA\s*0\b", e):
        return "ALERTA_0 DIAS"

    EST = ["A TIEMPO", "ALERTA", "ALERTA_0 DIAS", "VENCIDO", "SIN FECHA"]
    if e in EST:
        return e

    if "A TIEMPO" in e:
        return "A TIEMPO"
    if "ALERTA" in e:
        return "ALERTA"
    if "VENCID" in e:
        return "VENCIDO"

    return "SIN FECHA"


df["ESTADO"] = df["ESTADO"].apply(normalizar_estado)

# ============================================================
# 2.2 VALIDACIÓN COORDENADAS + LOG
# ============================================================
errores = []

def validar_coord(x, y, pedido):
    try:
        x = float(str(x).replace(",", "."))
        y = float(str(y).replace(",", "."))
    except:
        errores.append(f"{pedido}: coordenada no numérica → X={x}, Y={y}")
        return None, None

    if not (5 <= y <= 8) or not (-78 <= x <= -73):
        errores.append(f"{pedido}: fuera de rango → X={x}, Y={y}")
        return None, None

    return x, y

df["COORD_X"], df["COORD_Y"] = zip(*[
    validar_coord(row["COORDENADAX"], row["COORDENADAY"], row["PEDIDO"])
    for _, row in df.iterrows()
])

# ============================================================
# 2.3 AGRUPAR POR PEDIDO Y RESOLVER ESTADOS
# ============================================================
prioridad = {
    "VENCIDO": 4,
    "ALERTA_0 DIAS": 3,
    "ALERTA": 2,
    "A TIEMPO": 1,
    "SIN FECHA": 0
}

grupo = df.groupby("PEDIDO").agg({
    "ESTADO": list,
    "COORD_X": "first",
    "COORD_Y": "first",
    "ACTIVIDAD": "first"
}).reset_index()

def estado_final(lista_estados):
    return sorted(lista_estados, key=lambda x: prioridad.get(x, 0), reverse=True)[0]

grupo["ESTADO_FINAL"] = grupo["ESTADO"].apply(estado_final)

df_mapa = grupo.copy()

df_mapa = grupo.copy()

# ✅ Quitar pedidos sin coordenadas válidas (evita nan/None en JS)
df_mapa = df_mapa.dropna(subset=["COORD_X", "COORD_Y"])

# ✅ ACTIVIDAD sin NaN (evita 'nan is not defined' en listaActividades)
df_mapa["ACTIVIDAD"] = df_mapa["ACTIVIDAD"].fillna("SIN ACTIVIDAD").astype(str)

# ✅ Para el selector
actividades_unicas = sorted(df_mapa["ACTIVIDAD"].unique().tolist())
actividades_js = json.dumps(actividades_unicas, ensure_ascii=False)

print(f"[INFO] Pedidos con coordenadas válidas para mapa: {len(df_mapa)}")



# ============================================================
# 4. MAPA BASE
# ============================================================
mapa = folium.Map(
    location=[6.24, -75.57],
    zoom_start=13,
    tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    attr="Google"
)

mapa_id = mapa.get_name()

# ============================================================
# 5. VARIABLES JS BASE
# ============================================================
mapa.get_root().html.add_child(folium.Element(f"""
<script>
document.addEventListener("DOMContentLoaded", function() {{
    window.mapa = {mapa_id};
    window.marcadores = {{}};
    window.estadoMarcadores = {{
        "A TIEMPO": [],
        "ALERTA": [],
        "ALERTA_0 DIAS": [],
        "VENCIDO": [],
        "SIN FECHA": []
    }};
    window.actividadMarcadores = {{}};
    window.listaActividades = {actividades_js};
}});
</script>
"""))

# ============================================================
# 6. COLORES
# ============================================================
ICON_SIZE = [20, 33]
colores = {
    "A TIEMPO": "green",
    "ALERTA": "yellow",
    "ALERTA_0 DIAS": "orange",
    "VENCIDO": "red",
    "SIN FECHA": "violet"
}

# ============================================================
# 7. MARCADORES CON TOOLTIP MULTI-ESTADO
# ============================================================
markers_js = "<script>\ndocument.addEventListener('DOMContentLoaded', function() {\n"

for _, row in df_mapa.iterrows():
    pedido = row["PEDIDO"]
    lat = row["COORD_Y"]
    lon = row["COORD_X"]
    actividad = row["ACTIVIDAD"]

    lista_estados = row["ESTADO"]
    estado_final = row["ESTADO_FINAL"]

    # Contar estados
    conteo = {}
    for est in lista_estados:
        conteo[est] = conteo.get(est, 0) + 1

    # Construir tooltip
    tooltip_html = f"<b>PEDIDO: {pedido}</b><br><br>"
    tooltip_html += "<b>ESTADOS DETECTADOS:</b><br>"

    for est, cant in conteo.items():
        tooltip_html += f"- {est} ({cant})<br>"

    tooltip_html += f"<br><b>Estado final usado:</b> {estado_final}<br>"

    color = colores.get(estado_final, "red")

    markers_js += f"""
var mk_{pedido} = L.marker([{lat}, {lon}], {{
    icon: L.icon({{
        iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-{color}.png",
        shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
        iconSize: [{ICON_SIZE[0]}, {ICON_SIZE[1]}],
        iconAnchor: [10, 33],
        popupAnchor: [0, -28]
    }})
}}).bindTooltip(`{tooltip_html}`).addTo(window.mapa);

window.marcadores["{pedido}"] = mk_{pedido};
window.estadoMarcadores["{estado_final}"].push("{pedido}");

if (!window.actividadMarcadores["{actividad}"]) {{
    window.actividadMarcadores["{actividad}"] = [];
}}
window.actividadMarcadores["{actividad}"].push("{pedido}");
"""

markers_js += "});\n</script>"
mapa.get_root().html.add_child(folium.Element(markers_js))
# ============================================================
# 8. PANEL COMPLETO (TU PANEL ORIGINAL SIN CAMBIOS)
# ============================================================
panel_html = Template("""
{% macro html(this, kwargs) %}

<style>
#panelANS{
    position: fixed;
    right:20px; top:20px;
    width:240px;
    background:white;
    padding:15px;
    border-radius:12px;
    box-shadow:0 0 12px rgba(0,0,0,0.3);
    z-index:999999;
    font-family:Arial;
}
.filtroBtn{
    width:100%; padding:8px;
    border-radius:6px;
    margin-top:6px;
    cursor:pointer;
    font-weight:bold;
    text-align:center;
}
.subtitulo{
    font-size:14px; margin-top:12px;
    font-weight:bold;
}
</style>

<div id="panelANS">

<b style="font-size:18px;">📊 Control ANS</b><br><br>

<b>Buscar pedido:</b><br>
<input id="buscarPedido" style="width:100%;padding:6px;"><br>
<button onclick="buscarPedido()" class="filtroBtn" style="background:#e0e0e0;">Buscar</button>
<button onclick="limpiarBusqueda()" class="filtroBtn" style="background:#cccccc;">Limpiar</button>

<hr>

<b class="subtitulo">Filtros por Estado:</b>
<div onclick="filtrarEstado('A TIEMPO')" class="filtroBtn" style="background:#00C853;color:white;">A TIEMPO</div>
<div onclick="filtrarEstado('ALERTA')" class="filtroBtn" style="background:#FFD600;">ALERTA</div>
<div onclick="filtrarEstado('ALERTA_0 DIAS')" class="filtroBtn" style="background:#FF8F00;">ALERTA 0 DÍAS</div>
<div onclick="filtrarEstado('VENCIDO')" class="filtroBtn" style="background:#D50000;color:white;">VENCIDO</div>
<div onclick="filtrarEstado('SIN FECHA')" class="filtroBtn" style="background:#6a1b9a;color:white;">SIN FECHA</div>
<div onclick="mostrarTodos()" class="filtroBtn" style="background:#bbdefb;">MOSTRAR TODOS</div>

<hr>

<b class="subtitulo">Filtro por Actividad:</b>
<select id="selectActividad" class="filtroBtn" style="padding:6px;width:100%;">
    <option value="">-- Seleccione actividad --</option>
</select>

<div onclick="filtrarActividad()" class="filtroBtn" style="background:#90caf9;">FILTRAR ACTIVIDAD</div>
<div onclick="limpiarActividad()" class="filtroBtn" style="background:#bdbdbd;">LIMPIAR ACTIVIDAD</div>

<div id="resultadoActividad"
     style="margin-top:6px;padding:8px;background:#eeeeee;
            border-radius:6px;text-align:center;font-weight:bold;">
    Resultados: 0 pedidos
</div>

<hr>

<b class="subtitulo">🗺️ Capas del Mapa</b>
<div onclick="setCapa('sat')" class="filtroBtn" style="background:#c5e1a5;">Satélite</div>
<div onclick="setCapa('calles')" class="filtroBtn" style="background:#aed581;">Vista Urbana</div>

</div>

<script>

document.addEventListener("DOMContentLoaded", function() {
    let sel = document.getElementById("selectActividad");
    if (window.listaActividades) {
        window.listaActividades.forEach(act => {
            let opt = document.createElement("option");
            opt.value = act;
            opt.textContent = act;
            sel.appendChild(opt);
        });
    }
});

const capas = {
    sat: "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    calles: "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
};

window.currentLayer = null;

window.setCapa = function(tipo){
    if(window.currentLayer){ window.mapa.removeLayer(window.currentLayer); }
    window.currentLayer = L.tileLayer(capas[tipo], {maxZoom: 20}).addTo(window.mapa);
    window.mapa.invalidateSize(true);
};

function refrescar(){ 
    setTimeout(()=> window.mapa.invalidateSize(true), 50); 
}

window.ocultarTodos = ()=>{ 
    Object.values(window.marcadores).forEach(m=>m.setOpacity(0)); 
    refrescar();
};

window.mostrarTodos = ()=>{ 
    Object.values(window.marcadores).forEach(m=>m.setOpacity(1)); 
    window.mapa.setView([6.24, -75.57], 13);
    refrescar();
};

window.filtrarEstado = estado => {
    window.ocultarTodos();
    window.estadoMarcadores[estado].forEach(p=> window.marcadores[p].setOpacity(1));
    refrescar();
};

window.filtrarActividad = ()=> {
    let act = document.getElementById("selectActividad").value;
    let div = document.getElementById("resultadoActividad");

    if(!act){
        div.innerHTML = "Seleccione una actividad";
        return;
    }

    let lista = window.actividadMarcadores[act];

    if(!lista){
        div.innerHTML = "Resultados: 0 pedidos";
        return;
    }

    window.ocultarTodos();
    lista.forEach(p => window.marcadores[p]?.setOpacity(1));

    div.innerHTML = "Resultados: " + lista.length + " pedidos";
    window.mapa.setView([6.24, -75.57], 13);
    refrescar();
};

window.limpiarActividad = ()=> {
    document.getElementById("selectActividad").value = "";
    document.getElementById("resultadoActividad").innerHTML = "Resultados: 0 pedidos";
    window.mostrarTodos();
};

window.buscarPedido = ()=> {
    let p = document.getElementById("buscarPedido").value.trim();
    if(!p) return;

    let mk = window.marcadores[p];

    if(mk){
        window.ocultarTodos();
        mk.setOpacity(1);
        window.mapa.setView(mk.getLatLng(), 18);
        mk.openTooltip();
        refrescar();
    } else {
        alert("Pedido no encontrado");
    }
};

window.limpiarBusqueda = ()=> {
    document.getElementById("buscarPedido").value = "";
    window.mostrarTodos();
};

</script>

{% endmacro %}
""")

panel = MacroElement()
panel._template = panel_html
mapa.get_root().add_child(panel)

# ============================================================
# 9. GUARDAR MAPA
# ============================================================
mapa.save(ruta_salida_onedrive)
mapa.save(ruta_salida_proyecto)

print("🟢 Mapa ANS v8.3 guardado correctamente.")
