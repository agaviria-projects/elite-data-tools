"""Informe de confirmaciones registrado en SQLite, sin COM ni envíos.

La consulta es una instantánea de solo lectura. Exportar no actualiza el
monitor, no consulta Outlook y nunca cambia un estado del seguimiento.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import closing
from datetime import date, datetime, timedelta
import math
import os
from pathlib import Path
import re
import sqlite3
import tempfile

from modules import seguimiento_lectura as motor

ESTADOS = {
    'pendiente_envio': 'Pendiente de envío',
    'esperando_confirmacion': 'Sin confirmación de lectura',
    'lectura_confirmada': 'Lectura confirmada',
    'limite_alcanzado': 'Máximo alcanzado',
    'sin_recordatorios': 'Sin recordatorios',
    'jornada_finalizada': 'Jornada finalizada',
    'revision_requerida': 'Revisión requerida',
    'error_sin_reintento': 'Error: revisar Outlook',
    'sin_envio_verificado': 'Envío no verificado',
    'cancelado': 'Cancelado',
    'intento_recordatorio': 'Intento incierto: revisar Outlook',
    'preparado': 'Borrador preparado',
    'original_solicitado': 'Envío solicitado a Outlook',
    'enviado': 'Envío original verificado',
}
CONFIRMADA = 'Confirmada'
SIN_CONFIRMACION = 'Sin confirmación registrada'
NO_EVALUADA = 'No evaluada'
SIN_ENVIO = 'Envío no verificado'
CATEGORIAS = (CONFIRMADA, SIN_CONFIRMACION, NO_EVALUADA, SIN_ENVIO)


def validar_fechas(inicial, final):
    def convertir(valor):
        if isinstance(valor, datetime):
            raise ValueError('Indique fechas sin hora con el formato DD/MM/AAAA.')
        if isinstance(valor, date):
            return valor
        if not isinstance(valor, str) or not re.fullmatch(r'\d{2}/\d{2}/\d{4}', valor.strip()):
            raise ValueError('Ingrese ambas fechas con el formato DD/MM/AAAA.')
        try:
            return datetime.strptime(valor.strip(), '%d/%m/%Y').date()
        except ValueError:
            raise ValueError('Hay una fecha no válida. Use DD/MM/AAAA.') from None
    inicio, fin = convertir(inicial), convertir(final)
    if inicio > fin:
        raise ValueError('La fecha inicial no puede superar la fecha final.')
    # Se necesita el inicio exclusivo del día siguiente para incluir horas.
    if fin == date.max:
        raise ValueError('La fecha final está fuera del rango admitido.')
    return inicio, fin


def _numero_fecha(valor, nombre):
    if valor is None:
        return None
    if isinstance(valor, bool) or not isinstance(valor, (float, int)) or not math.isfinite(valor):
        raise ValueError(f'El historial contiene una {nombre} no válida; no se exportó.')
    try:
        datetime.fromtimestamp(valor, motor.BOGOTA)
    except (OverflowError, OSError, ValueError):
        raise ValueError(f'El historial contiene una {nombre} fuera de rango.') from None
    return valor


def fecha_registro(fila):
    """Fecha de envío real; si no está verificado, fecha de creación aparte."""
    valor = fila['enviado'] if fila['enviado'] is not None else fila['creado']
    valor = _numero_fecha(valor, 'fecha del correo')
    if valor is None:
        raise ValueError('Hay un correo sin fecha de envío ni fecha de creación.')
    return datetime.fromtimestamp(valor, motor.BOGOTA).date()


def estado_visible(fila):
    estado, detalle = fila['estado'], fila['detalle'] or ''
    if fila['estado_informe'] in ('revision_requerida', 'error_sin_reintento', 'sin_envio_verificado'):
        estado = fila['estado_informe']
        detalle = fila['detalle_informe'] or detalle
    return ESTADOS.get(estado, estado), detalle


def consultar_informe(inicial, final, *, ruta_db=None, ahora=None):
    """Lee un único snapshot. No crea ni migra la base, incluso si es histórica.

    Filtra por fecha colombiana del envío original (no por el período del
    asunto). Borradores y envíos no verificados se filtran por creación y se
    cuentan por separado, nunca como destinatarios de un envío comprobado.
    """
    inicio, fin = validar_fechas(inicial, final)
    desde = datetime.combine(inicio, datetime.min.time(), motor.BOGOTA).timestamp()
    hasta = datetime.combine(fin + timedelta(days=1), datetime.min.time(), motor.BOGOTA).timestamp()
    ruta = Path(ruta_db) if ruta_db is not None else motor.RAIZ / 'seguimiento.sqlite3'
    if not ruta.is_file():
        raise FileNotFoundError('Todavía no hay historial de seguimiento guardado en este equipo.')
    limite = _numero_fecha(ahora, 'fecha de consulta') if ahora is not None else None
    with closing(sqlite3.connect(ruta.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        tablas = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'informes', 'destinatarios'}.issubset(tablas):
            raise ValueError('La base no contiene el historial esperado de DataSuite.')
        columnas_i = {r[1] for r in db.execute('PRAGMA table_info(informes)')}
        columnas_d = {r[1] for r in db.execute('PRAGMA table_info(destinatarios)')}
        corte = 'i.corte' if 'corte' in columnas_i else "''"
        correlacion = 'i.correlacion' if 'correlacion' in columnas_i else "'asunto'"
        confirmacion = 'd.confirmacion_detectada' if 'confirmacion_detectada' in columnas_d else 'NULL'
        filas = [dict(r) for r in db.execute(f'''SELECT d.*,
            {confirmacion} AS fecha_confirmacion, i.asunto,i.creado,i.enviado,i.cierre,
            i.espera,i.intervalo,i.maximo,{corte} AS corte,{correlacion} AS correlacion,
            i.estado AS estado_informe,i.detalle AS detalle_informe
            FROM destinatarios d JOIN informes i ON i.token=d.token
            WHERE COALESCE(i.enviado,i.creado)>=? AND COALESCE(i.enviado,i.creado)<?
            ORDER BY COALESCE(i.enviado,i.creado),i.token,d.id''', (desde, hasta))]
        verificados = {}
        if 'mensajes_internos' in tablas:
            verificados = {(r['token'], r['destinatario']): r['cantidad'] for r in db.execute('''
                SELECT m.token,m.destinatario,COUNT(*) AS cantidad
                FROM mensajes_internos m JOIN informes i ON i.token=m.token
                WHERE COALESCE(i.enviado,i.creado)>=? AND COALESCE(i.enviado,i.creado)<?
                AND m.destinatario<>'' AND m.enviado IS NOT NULL
                GROUP BY m.token,m.destinatario''', (desde, hasta))}
        consultado = datetime.now(motor.BOGOTA) if limite is None else datetime.fromtimestamp(limite, motor.BOGOTA)
    registros = []
    por_dia = defaultdict(list)
    for fila in filas:
        for nombre in ('creado', 'enviado', 'cierre', 'proximo', 'fecha_confirmacion'):
            _numero_fecha(fila.get(nombre), nombre)
        for nombre in ('intentos', 'maximo'):
            if type(fila[nombre]) is not int or fila[nombre] < 0:
                raise ValueError('El historial contiene cantidades de recordatorios no válidas.')
        envio_verificado = fila['enviado'] is not None
        if not envio_verificado:
            categoria = SIN_ENVIO
        elif fila['estado'] == 'lectura_confirmada' or fila['fecha_confirmacion'] is not None:
            categoria = CONFIRMADA
        elif fila['estado'] in ('sin_recordatorios', 'cancelado'):
            categoria = NO_EVALUADA
        else:
            categoria = SIN_CONFIRMACION
        estado, detalle = estado_visible(fila)
        registro = dict(fila, fecha=fecha_registro(fila), confirmacion=categoria,
                        estado_visible=estado, detalle_visible=detalle,
                        recordatorios_verificados=(verificados.get((fila['token'], fila['destinatario']), 0)
                            if fila['correlacion'] == 'interno' and 'mensajes_internos' in tablas else None))
        registros.append(registro)
        por_dia[registro['fecha']].append(registro)
    resumen = []
    for dia, grupo in sorted(por_dia.items()):
        resumen.append(dict(fecha=dia, correos=len({r['token'] for r in grupo}),
            correos_verificados=len({r['token'] for r in grupo if r['enviado'] is not None}),
            registros=len(grupo), personas=len({r['destinatario'].strip().lower() for r in grupo}),
            **{nombre:sum(r['confirmacion'] == nombre for r in grupo) for nombre in CATEGORIAS},
            intentos=sum(r['intentos'] for r in grupo),
            recordatorios_verificados=sum(r['recordatorios_verificados'] or 0 for r in grupo),
            verificacion_completa=all(r['recordatorios_verificados'] is not None for r in grupo)))
    return dict(inicial=inicio, final=fin, consultado=consultado, registros=registros,
                resumen=resumen, fuente=str(ruta.resolve()))


def exportar_informe(datos, destino, *, sobrescribir=False):
    """Exporta exclusivamente las ocho columnas operativas del seguimiento."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    from openpyxl.worksheet.table import Table, TableStyleInfo
    from openpyxl.formatting.rule import FormulaRule

    destino = Path(destino)
    if destino.suffix.lower() != '.xlsx':
        raise ValueError('Guarde el informe con la extensión .xlsx.')
    if destino.exists() and not sobrescribir:
        raise FileExistsError('El archivo ya existe. Elija otro nombre o confirme reemplazarlo.')
    if not destino.parent.is_dir():
        raise FileNotFoundError('La carpeta de destino no existe.')

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Detalle'
    hoja.sheet_view.showGridLines = False
    hoja.sheet_properties.tabColor = '007D69'
    hoja.sheet_properties.pageSetUpPr.fitToPage = True
    hoja.page_setup.orientation = 'landscape'
    hoja.page_setup.paperSize = hoja.PAPERSIZE_A3
    hoja.page_setup.fitToWidth, hoja.page_setup.fitToHeight = 1, 0
    hoja.print_title_rows = '3:3'

    encabezados = [
        'Envío original verificado', 'Destinatario', 'Confirmación de lectura',
        'Estado del seguimiento', 'Intentos de recordatorio',
        'Recordatorios con envío verificado', 'Máximo de recordatorios',
        'Detalle del seguimiento',
    ]
    anchos = [24, 43, 31, 30, 20, 25, 19, 77]
    for columna, (titulo, ancho) in enumerate(zip(encabezados, anchos), 1):
        celda = hoja.cell(3, columna)
        celda.value = titulo
        celda.fill = PatternFill('solid', fgColor='007D69')
        celda.font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        celda.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        celda.border = Border(right=Side(style='thin', color='FFFFFF'))
        hoja.column_dimensions[celda.column_letter].width = ancho
    hoja.row_dimensions[3].height = 44

    def texto_seguro(valor):
        limpio = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', str(valor))
        return limpio[:32740] + ' [texto recortado]' if len(limpio) > 32767 else limpio

    for numero, registro in enumerate(datos['registros'], 4):
        enviado = registro['enviado']
        fecha_envio = (datetime.fromtimestamp(enviado, motor.BOGOTA).replace(tzinfo=None)
                       if enviado is not None else None)
        valores = [
            fecha_envio, registro['destinatario'], registro['confirmacion'],
            registro['estado_visible'], registro['intentos'],
            registro['recordatorios_verificados'], registro['maximo'],
            registro['detalle_visible'],
        ]
        for columna, valor in enumerate(valores, 1):
            celda = hoja.cell(numero, columna)
            if isinstance(valor, str):
                celda.value = texto_seguro(valor)
                celda.data_type = 's'
            else:
                celda.value = valor
            celda.font = Font(name='Arial', size=10)
            celda.alignment = Alignment(vertical='center',
                horizontal='center' if columna in (5, 6, 7) else 'left',
                wrap_text=columna in (3, 4, 8))
        hoja.cell(numero, 1).number_format = 'dd/mm/yyyy hh:mm:ss'
        hoja.row_dimensions[numero].height = 28

    ultima = 3 + len(datos['registros'])
    if datos['registros']:
        tabla = Table(displayName='DetalleConfirmaciones', ref=f'A3:H{ultima}')
        tabla.tableStyleInfo = TableStyleInfo(name='TableStyleMedium2', showRowStripes=True)
        hoja.add_table(tabla)
        hoja.conditional_formatting.add(f'C4:C{ultima}', FormulaRule(
            formula=['C4="Sin confirmación registrada"'],
            fill=PatternFill('solid', fgColor='FFF2CC')))
    else:
        hoja['A4'] = 'No hay registros para el rango seleccionado.'
    hoja.freeze_panes = 'C4'
    hoja.print_area = f'A3:H{max(4, ultima)}'
    # No escribir sobre el destino hasta que el Excel temporal esté completo.
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(dir=destino.parent,prefix='.lecturas-',suffix='.xlsx',delete=False) as tmp:
            temporal = Path(tmp.name)
        libro.save(temporal)
        libro.close()
        if sobrescribir:
            os.replace(temporal,destino)
        else:
            # xb evita sobrescribir incluso si otro proceso creó el nombre al exportar.
            creada = False
            try:
                with destino.open('xb') as salida, temporal.open('rb') as entrada:
                    creada = True
                    import shutil
                    shutil.copyfileobj(entrada,salida)
            except Exception:
                if creada:
                    destino.unlink(missing_ok=True)
                raise
        return destino
    finally:
        libro.close()
        if temporal is not None:
            temporal.unlink(missing_ok=True)
