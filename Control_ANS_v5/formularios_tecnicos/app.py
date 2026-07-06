from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
from pathlib import Path
import pandas as pd
import os

# ------------------------------------------------------------
# CONFIGURACIÓN BASE DE FLASK
# ------------------------------------------------------------
base_dir = Path(__file__).resolve().parent  # carpeta 'formularios_tecnicos'

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')

# Clave secreta para mensajes flash
app.secret_key = "clave_super_secreta_ans"

# Carpeta de cargas
app.config['UPLOAD_FOLDER'] = base_dir / "static" / "uploads"
app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# CARGA ARCHIVO FENIX
# ------------------------------------------------------------
ruta_fenix = base_dir.parent / "data_clean" / "FENIX_ANS.xlsx"
if ruta_fenix.exists():
    df_fenix = pd.read_excel(ruta_fenix)
    df_fenix.columns = df_fenix.columns.str.strip().str.upper()
else:
    df_fenix = pd.DataFrame()

# ------------------------------------------------------------
# FORMULARIO PRINCIPAL
# ------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def formulario():
    ruta_excel = base_dir / "registros_formulario.xlsx"
    df_registros = pd.read_excel(ruta_excel) if ruta_excel.exists() else pd.DataFrame()

    # Si es envío del formulario (POST)
    if request.method == "POST":
        pedido = str(request.form["pedido"]).strip()
        observacion = request.form["observacion"]
        estado = request.form["estado"]

        # 🔸 Validar duplicado
        if not df_registros.empty and pedido in df_registros["pedido"].astype(str).values:
            flash(f"⚠ El pedido {pedido} ya fue registrado anteriormente.", "warning")
            return redirect(url_for("formulario"))

        # 🔸 Validar existencia en FENIX
        df_fenix["PEDIDO"] = df_fenix["PEDIDO"].astype(str).str.strip()
        resultado = df_fenix[df_fenix["PEDIDO"] == pedido]

        if resultado.empty:
            flash(f"❌ Pedido {pedido} no existe en FENIX_ANS. Verifique nuevamente.", "danger")
            return redirect(url_for("formulario"))

        # 🔸 Procesar archivos combinados (PDF e imágenes)
        archivos = request.files.getlist("archivos_evidencia")
        nombres_pdf, nombres_imagenes = [], []

        for i, archivo in enumerate(archivos, start=1):
            if archivo and archivo.filename:
                ext = archivo.filename.split(".")[-1].lower()
                nombre_archivo = f"{pedido}_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                archivo.save(app.config['UPLOAD_FOLDER'] / nombre_archivo)

                if ext == "pdf":
                    nombres_pdf.append(nombre_archivo)
                elif ext in ["jpg", "jpeg", "png"]:
                    nombres_imagenes.append(nombre_archivo)

        # 🔸 Registrar si se subieron archivos o no
        pdf_guardado = ", ".join(nombres_pdf) if nombres_pdf else "Sin archivo"
        imagenes_guardadas = ", ".join(nombres_imagenes) if nombres_imagenes else "Sin imágenes"


              # 🔸 Registrar fila
        fila = resultado.iloc[0]
        registro = {
            "fecha_envio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pedido": pedido,
            "observacion": observacion,
            "estado": estado,  # ✅ valor seleccionado por el técnico
            "pdf": pdf_guardado,
            "imagenes": imagenes_guardadas,
            "cliente": fila.get("NOMBRE_CLIENTE", ""),
            "direccion": fila.get("DIRECCION", ""),
            "estado_fenix": fila.get("ESTADO", ""),
            "clienteid": fila.get("CLIENTEID", ""),
            "metodo_envio": request.form.get("metodo_envio", "")
        }

        # 🔸 Crear DataFrame ordenado con columnas estándar
        columnas = [
            "fecha_envio", "pedido", "observacion", "estado",
            "pdf", "imagenes", "cliente", "direccion",
            "estado_fenix", "clienteid", "metodo_envio"
        ]

        # Si el archivo ya existe, asegúrate de mantener el orden
        if not df_registros.empty:
            df_registros = df_registros.reindex(columns=columnas, fill_value="")

        # 🔸 Guardar registro
        df_final = pd.concat([df_registros, pd.DataFrame([registro])], ignore_index=True)
        df_final.to_excel(ruta_excel, index=False)

        # 🔸 Confirmar al usuario
        flash(f"✅ Registro guardado correctamente — Pedido {pedido}", "success")
        return redirect(url_for("formulario"))

    # ✅ Si es GET (abrir formulario)
    return render_template("form.html")

# ------------------------------------------------------------
# CONSULTA PEDIDO FENIX / REGISTROS (versión con depuración)
# ------------------------------------------------------------
@app.route("/buscar_pedido/<pedido_id>")
def buscar_pedido(pedido_id):
    pedido_id = str(pedido_id).strip()
    print(f"🔍 Buscando pedido: {pedido_id}")  # <-- para depuración en consola

    if df_fenix.empty:
        print("❌ Archivo FENIX_ANS está vacío o no existe.")
        return jsonify({"error": "Archivo FENIX_ANS no encontrado o vacío"})

    # 1️⃣ Buscar primero en registros_formulario.xlsx
    ruta_excel = base_dir / "registros_formulario.xlsx"
    if ruta_excel.exists():
        df_reg = pd.read_excel(ruta_excel)
        df_reg["pedido"] = df_reg["pedido"].astype(str)

        registro = df_reg[df_reg["pedido"] == pedido_id]
        if not registro.empty:
            fila = registro.iloc[0]
            estado_real = fila.get("estado", "Sin estado")
            print(f"📋 Encontrado en registros_formulario.xlsx con estado: {estado_real}")
            return jsonify({
                "origen": "registro",
                "mensaje": f"📋 El pedido {pedido_id} ya fue registrado con estado: <strong>{estado_real}</strong>",
                "estado_real": estado_real,
                "observacion": fila.get("observacion", ""),
                "metodo_envio": fila.get("metodo_envio", "")
            })

    # 2️⃣ Si no está en registros, buscar en FENIX
    df_fenix.columns = df_fenix.columns.str.strip().str.upper()  # asegurar mayúsculas
    df_fenix["PEDIDO"] = df_fenix["PEDIDO"].astype(str).str.strip()

    resultado = df_fenix[df_fenix["PEDIDO"] == pedido_id]
    print(f"Resultado búsqueda en FENIX → {len(resultado)} filas")

    if not resultado.empty:
        fila = resultado.iloc[0]
        datos = {
            "origen": "fenix",
            "clienteid": str(fila.get("CLIENTEID", "")),
            "nombre_cliente": str(fila.get("NOMBRE_CLIENTE", "")),
            "telefono": str(fila.get("TELEFONO_CONTACTO", "")),
            "celular": str(fila.get("CELULAR_CONTACTO", "")),
            "direccion": str(fila.get("DIRECCION", "")),
            "fecha_limite_ans": str(fila.get("FECHA_LIMITE_ANS", "")),
            "estado_fenix": str(fila.get("ESTADO", ""))
        }
        print(f"✅ Datos enviados al frontend: {datos}")
        return jsonify(datos)
    

    print("⚠ No se encontró el pedido en ningún archivo.")
    return jsonify({"error": f"Pedido {pedido_id} no existe...."})
# ------------------------------------------------------------
# EJECUCIÓN
# ------------------------------------------------------------
if __name__ == "__main__":
    print("Ruta absoluta esperada del static:")
    print(app.static_folder)
    print("Contenido real de esa carpeta:")
    print(os.listdir(app.static_folder))
    app.run(debug=True, host="0.0.0.0")
