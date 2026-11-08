"""Trazabilidad de los bytes procesados. No contiene reglas de negocio."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import uuid

BOGOTA = timezone(timedelta(hours=-5))
MANIFIESTO = 'control_ultima_validacion.json'


def huella(datos):
    return hashlib.sha256(datos).hexdigest()


def guardar_estado(proyecto, estado):
    salida = Path(proyecto) / 'outputs'
    salida.mkdir(parents=True, exist_ok=True)
    temporal = salida / ('.control-' + uuid.uuid4().hex + '.tmp')
    temporal.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding='utf-8')
    temporal.replace(salida / MANIFIESTO)


def iniciar_ejecucion(proyecto):
    estado = dict(version=1, ejecucion=uuid.uuid4().hex, estado='iniciada',
                  inicio=datetime.now(BOGOTA).isoformat(), archivos=[], fechas=[])
    guardar_estado(proyecto, estado)  # Un intento fallido no autoriza el informe anterior.
    return estado


def fecha_dato(valor):
    """Formatos explícitos: no usa heurísticas ni toma fechas del nombre del TXT."""
    texto = str(valor).strip()
    for patron, formato in (
        (r'\d{2}/\d{2}/\d{4}', '%d/%m/%Y'),
        (r'\d{2}-\d{2}-\d{4}', '%d-%m-%Y'),
        (r'\d{4}-\d{2}-\d{2}', '%Y-%m-%d'),
        (r'\d{4}/\d{2}/\d{2}', '%Y/%m/%d'),
        (r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', '%d/%m/%Y %H:%M:%S'),
        (r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}', '%Y-%m-%d %H:%M:%S'),
        (r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', '%Y/%m/%d %H:%M:%S'),
    ):
        if re.fullmatch(patron, texto):
            try:
                return datetime.strptime(texto.replace('T', ' '), formato).date()
            except ValueError:
                return None
    return None


def registrar_archivo(estado, archivo, datos, df, modificado):
    archivo = Path(archivo)
    subzonas = sorted(set(df['subz'].dropna().astype(str).str.strip()) - {''}) if 'subz' in df else []
    pedidos = df['pedido'].dropna().astype(str).str.strip() if 'pedido' in df else []
    registro = dict(nombre=archivo.name, sha256=huella(datos), bytes=len(datos),
        modificado=datetime.fromtimestamp(modificado, BOGOTA).isoformat(),
        zona_nombre=archivo.stem.rsplit('_', 1)[-1] if '_' in archivo.stem else '',
        subzonas=subzonas, registros=len(df),
        pedidos=len(set(pedidos) - {''}),
        con=int(df['tipo'].eq('CON').sum()) if 'tipo' in df else 0,
        sum=int(df['tipo'].eq('SUM').sum()) if 'tipo' in df else 0)
    estado['archivos'].append(registro)
    # Se muestran TODOS los campos reconocibles, sin elegir uno como período oficial.
    for columna in df.columns:
        nombre = str(columna).strip().lower()
        if 'fecha' not in nombre and not nombre.startswith(('fec_', 'fch_')):
            continue
        valores = [str(v).strip() for v in df[columna].dropna() if str(v).strip()]
        fechas = [fecha_dato(v) for v in valores]
        validas = [f for f in fechas if f is not None]
        estado['fechas'].append(dict(archivo=archivo.name, campo=str(columna),
            minima=min(validas).isoformat() if validas else None,
            maxima=max(validas).isoformat() if validas else None,
            validas=len(validas), no_reconocidas=len(valores)-len(validas),
            vacias=len(df)-len(valores)))


def verificar_fuentes(proyecto, estado):
    carpeta = Path(proyecto) / 'data_mo_materiales'
    actuales = {p.name: p for p in carpeta.iterdir() if p.is_file() and p.suffix.lower() == '.txt'}
    esperados = {r['nombre']: r for r in estado['archivos']}
    if set(actuales) != set(esperados):
        raise ValueError('Cambió la lista de TXT desde la validación. Pulse Validar Materiales nuevamente.')
    for nombre, registro in esperados.items():
        if huella(actuales[nombre].read_bytes()) != registro['sha256']:
            raise ValueError(f'Cambió el contenido de {nombre}. Pulse Validar Materiales nuevamente.')
    maestra = Path(proyecto) / 'data_master' / 'RELACION_MO_MATERIALES.xlsx'
    if huella(maestra.read_bytes()) != estado['maestra']['sha256']:
        raise ValueError('Cambió la Base Maestra. Pulse Validar Materiales nuevamente.')


def finalizar_ejecucion(proyecto, archivo, estado):
    verificar_fuentes(proyecto, estado)
    actual = json.loads((Path(proyecto)/'outputs'/MANIFIESTO).read_text(encoding='utf-8'))
    if actual['ejecucion'] != estado['ejecucion']:
        raise RuntimeError('Comenzó otra validación. No se registrará esta como última ejecución.')
    datos = Path(archivo).read_bytes()
    estado.update(estado='completada', fin=datetime.now(BOGOTA).isoformat(),
                  informe=dict(nombre=Path(archivo).name, sha256=huella(datos), bytes=len(datos)))
    guardar_estado(proyecto, estado)


def obtener_informe_verificado(proyecto):
    proyecto = Path(proyecto)
    ruta = proyecto / 'outputs' / MANIFIESTO
    if not ruta.is_file():
        raise ValueError('No hay una validación con control de exportes. Pulse Validar Materiales primero.')
    estado = json.loads(ruta.read_text(encoding='utf-8'))
    if estado.get('version') != 1 or estado.get('estado') != 'completada':
        raise ValueError('La última validación no terminó correctamente. No se adjuntará un informe anterior.')
    verificar_fuentes(proyecto, estado)
    referencia = estado['informe']
    candidatos = []
    for archivo in ruta.parent.iterdir():
        if (archivo.is_file() and archivo.suffix.lower() == '.xlsx'
                and not archivo.name.startswith('~$') and archivo.stat().st_size == referencia['bytes']
                and huella(archivo.read_bytes()) == referencia['sha256']):
            candidatos.append(archivo)
    original = ruta.parent / referencia['nombre']
    if original in candidatos:
        return original, estado
    if len(candidatos) == 1:
        return candidatos[0], estado
    if not candidatos:
        raise ValueError('No se encontró el informe intacto de la última validación en outputs. '
                         'Si editó el Excel o lo movió fuera de outputs, valide nuevamente.')
    raise ValueError('Hay varias copias idénticas del informe renombrado en outputs. '
                     'Deje una sola copia en outputs o valide nuevamente.')


def copiar_informe_verificado(proyecto, ejecucion):
    informe, estado = obtener_informe_verificado(proyecto)
    if estado['ejecucion'] != ejecucion:
        raise ValueError('Cambió la ejecución después de confirmar. Genere el correo nuevamente.')
    datos = informe.read_bytes()
    if huella(datos) != estado['informe']['sha256']:
        raise ValueError('El informe cambió mientras se preparaba el adjunto. No se generará el correo.')
    carpeta = Path(proyecto) / 'outputs' / 'correos' / ('verificado-' + uuid.uuid4().hex)
    carpeta.mkdir(parents=True)
    destino = carpeta / informe.name
    with destino.open('xb') as salida:
        salida.write(datos)
    return destino


def resumen_control(informe, estado):
    generado = datetime.fromisoformat(estado['inicio']).strftime('%d/%m/%Y %H:%M:%S')
    texto = [f'Informe: {Path(informe).name}', f'Ubicación: {Path(informe).parent}',
             f'Validación iniciada: {generado} (Colombia)',
             f'TXT procesados: {len(estado["archivos"])} · Registros leídos: {estado["registros"]}',
             'Archivos de Fénix utilizados:']
    texto.extend(f'  {r["nombre"]} — {r["registros"]} registros; subzonas: '
                 + (', '.join(r['subzonas']) or 'sin dato') for r in estado['archivos'])
    for campo in sorted({r['campo'] for r in estado['fechas']}):
        filas = [r for r in estado['fechas'] if r['campo'] == campo]
        minimas = [r['minima'] for r in filas if r['minima']]
        maximas = [r['maxima'] for r in filas if r['maxima']]
        if minimas:
            texto.append(f'Fechas observadas en {campo}: {min(minimas)} a {max(maximas)}.')
        texto.append(f'{campo}: {sum(r["no_reconocidas"] for r in filas)} fechas no reconocidas; '
                     f'{sum(r["vacias"] for r in filas)} vacías.')
    if not estado['fechas']:
        texto.append('No hay columnas de fecha reconocibles en los TXT.')
    texto.append('El período digitado del correo no se verifica por el nombre del archivo. '
                 'Revise las fechas observadas en este resumen cuando estén disponibles.')
    return '\n'.join(texto)


def escribir_hoja_control(wb, estado):
    """Vista deliberadamente sencilla: solo los TXT, al final del informe."""
    from openpyxl.styles import Alignment, Font, PatternFill
    # create_sheet sin índice conserva el orden de todas las hojas anteriores.
    ws = wb.create_sheet('CONTROL_EXPORTACION')
    ws.sheet_view.showGridLines = False
    nombres = [r['nombre'] for r in estado['archivos']]
    ancho = min(110, max(82, max((len(n) for n in nombres), default=0) + 3))
    ws.column_dimensions['A'].width = ancho
    ws['A1'] = 'Archivos de Fénix utilizados'
    ws['A1'].font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
    ws['A1'].fill = PatternFill('solid', fgColor='00B050')
    ws['A1'].alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[1].height = 28
    for fila, nombre in enumerate(nombres, 2):
        celda = ws.cell(fila, 1, nombre)
        celda.data_type = 's'  # Nombres externos nunca se convierten en fórmulas.
        celda.font = Font(name='Arial', size=11, color='000000')
        celda.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws.row_dimensions[fila].height = max(26, 18 * (1 + len(nombre) // int(ancho)))
    ws.print_area = f'A1:A{len(nombres)+1}'
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
