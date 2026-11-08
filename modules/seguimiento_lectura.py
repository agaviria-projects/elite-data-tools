"""Seguimiento individual por informe y destinatario en Outlook clásico.

Los envíos inciertos nunca se reintentan automáticamente. No demuestra
lectura la ausencia de comprobante. Las reservas SQLite preceden a Send.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import html
import json
from pathlib import Path
import re
import shutil
import sqlite3
import threading
import time
import uuid

REMITENTE = 'h.gaviria@eliteingenieros.com.co'
DESTINATARIOS = [
    'd.sanchez@eliteingenieros.com.co', 'l.toro@eliteingenieros.com.co',
    'f.marin@eliteingenieros.com.co', 'a.villegas@eliteingenieros.com.co',
    'y.patino@eliteingenieros.com.co', 'y.betancur@eliteingenieros.com.co',
    'c.giraldo@eliteingenieros.com.co', 'veronica.garzon@eliteingenieros.com.co',
]
COPIAS = ['d.leon@eliteingenieros.com.co', 's.atencio@eliteingenieros.com.co',
          'diego.durango@eliteingenieros.com.co']
AUTORIZADOS = set(DESTINATARIOS + COPIAS)
BOGOTA = timezone(timedelta(hours=-5))
CORTES = {'Mañana': 90, 'Tarde': 30}
MAPI = 'http://schemas.microsoft.com/mapi/proptag/'
# Propiedad propia: no modifica campos MAPI reservados ni el asunto visible.
MARCA = ('http://schemas.microsoft.com/mapi/string/'
         '{8B2FF2B4-2B93-42F5-9BC4-4AD63FAAB924}/DataSuiteSeguimiento')
RAIZ = Path(__file__).resolve().parent.parent / 'seguimiento_correos'
_hilo = None
_guardia = threading.Lock()
_publicar = lambda mensaje: None


@contextmanager
def conectar():
    RAIZ.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(RAIZ / 'seguimiento.sqlite3', timeout=20)
    db.row_factory = sqlite3.Row
    try:
        with db:
            db.execute('''CREATE TABLE IF NOT EXISTS informes (
                token TEXT PRIMARY KEY, asunto TEXT, creado REAL, estado TEXT,
                espera INTEGER, intervalo INTEGER, maximo INTEGER,
                enviado REAL, cierre REAL, adjuntos TEXT, detalle TEXT DEFAULT '')''')
            db.execute('''CREATE TABLE IF NOT EXISTS destinatarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT,
                destinatario TEXT, rol TEXT, activo INTEGER, estado TEXT,
                proximo REAL, intentos INTEGER DEFAULT 0, detalle TEXT DEFAULT '',
                UNIQUE(token,destinatario))''')
            if 'correlacion' not in {r[1] for r in db.execute('PRAGMA table_info(informes)')}:
                db.execute("ALTER TABLE informes ADD COLUMN correlacion TEXT NOT NULL DEFAULT 'asunto'")
            db.execute('''CREATE TABLE IF NOT EXISTS mensajes_internos (
                marca TEXT PRIMARY KEY, token TEXT NOT NULL, destinatario TEXT NOT NULL,
                asunto TEXT NOT NULL, message_id TEXT DEFAULT '', report_tag TEXT DEFAULT '',
                enviado REAL)''')
            yield db
    finally:
        db.close()


def validar_opciones(espera, intervalo, maximo, destinatarios):
    if type(espera) is not int or not 1 <= espera <= 1440:
        raise ValueError('La espera inicial debe ser un entero entre 1 y 1440 minutos.')
    if type(intervalo) is not int or not 1 <= intervalo <= 1440:
        raise ValueError('El intervalo debe ser un entero entre 1 y 1440 minutos.')
    if type(maximo) is not int or maximo < 1:
        raise ValueError('El máximo de recordatorios debe ser un número entero mayor que cero.')
    if not isinstance(destinatarios, list) or len(set(destinatarios)) != len(destinatarios):
        raise ValueError('Lista de seguimiento no válida o repetida.')
    if not set(destinatarios).issubset(AUTORIZADOS):
        raise ValueError('Hay destinatarios de seguimiento no autorizados.')


def guardar_configuracion(opciones):
    validar_opciones(opciones['espera'], opciones['intervalo'], opciones['maximo'], opciones['destinatarios'])
    if 'esperas' in opciones:
        if opciones.get('corte') not in CORTES or set(opciones['esperas']) != set(CORTES):
            raise ValueError('Configuración de cortes no válida.')
        for espera in opciones['esperas'].values():
            validar_opciones(espera, opciones['intervalo'], opciones['maximo'], opciones['destinatarios'])
        if opciones['espera'] != opciones['esperas'][opciones['corte']]:
            raise ValueError('La espera seleccionada no coincide con el corte.')
    RAIZ.mkdir(parents=True, exist_ok=True)
    temporal = RAIZ / ('config-' + uuid.uuid4().hex + '.tmp')
    temporal.write_text(json.dumps(opciones, ensure_ascii=False, indent=2), encoding='utf-8')
    temporal.replace(RAIZ / 'configuracion.json')


def cargar_configuracion():
    defecto = dict(activo=True, espera=90, intervalo=30, maximo=2,
                   destinatarios=DESTINATARIOS + COPIAS,
                   corte='Mañana', esperas=dict(CORTES))
    ruta = RAIZ / 'configuracion.json'
    if not ruta.exists():
        return defecto
    opciones = json.loads(ruta.read_text(encoding='utf-8'))
    validar_opciones(opciones['espera'], opciones['intervalo'], opciones['maximo'], opciones['destinatarios'])
    if 'esperas' not in opciones:
        opciones['corte'] = 'Tarde' if opciones['espera'] == 30 else 'Mañana'
        opciones['esperas'] = dict(CORTES)
        opciones['esperas'][opciones['corte']] = opciones['espera']
    if opciones.get('corte') not in CORTES or set(opciones['esperas']) != set(CORTES):
        raise ValueError('Configuración guardada de cortes no válida.')
    for espera in opciones['esperas'].values():
        validar_opciones(espera, opciones['intervalo'], opciones['maximo'], opciones['destinatarios'])
    opciones['espera'] = opciones['esperas'][opciones['corte']]
    return opciones


def cuenta_autorizada(outlook):
    for cuenta in outlook.Session.Accounts:
        if str(cuenta.SmtpAddress or '').strip().lower() == REMITENTE:
            return cuenta
    raise RuntimeError(f'No está configurada la cuenta {REMITENTE} en Outlook clásico.')


def fijar_cuenta(correo, cuenta):
    import pythoncom
    if str(cuenta.SmtpAddress or '').strip().lower() != REMITENTE:
        raise RuntimeError('Remitente no autorizado.')
    correo._oleobj_.Invoke(correo._oleobj_.GetIDsOfNames('SendUsingAccount'),
                          0, pythoncom.DISPATCH_PROPERTYPUTREF, 0, cuenta)


def direccion_entrada(entrada):
    if str(entrada.Type).upper() == 'EX':
        usuario = entrada.GetExchangeUser()
        if usuario:
            return str(usuario.PrimarySmtpAddress or '').strip().lower()
    for tag in ('0x39FE001F', '0x39FE001E'):
        try:
            valor = str(entrada.PropertyAccessor.GetProperty(
                'http://schemas.microsoft.com/mapi/proptag/' + tag) or '').strip().lower()
            if re.fullmatch(r'[^\s<>@]+@[^\s<>@]+', valor):
                return valor
        except Exception:
            pass  # La propiedad opcional puede no estar presente.
    return str(entrada.Address or '').strip().lower()


def comprobar(correo, para, copias):
    if str(correo.BCC or '').strip() or not correo.Recipients.ResolveAll():
        raise RuntimeError('CCO no permitido o destinatarios no resueltos.')
    reales = []
    for i in range(1, correo.Recipients.Count + 1):
        receptor = correo.Recipients.Item(i)
        reales.append((direccion_entrada(receptor.AddressEntry), int(receptor.Type)))
    esperados = [(s, 1) for s in para] + [(s, 2) for s in copias]
    if sorted(reales) != sorted(esperados):
        raise RuntimeError('Los destinatarios o los roles Para/CC cambiaron. Seguimiento bloqueado.')
    cuenta = correo.SendUsingAccount
    if cuenta is None or str(cuenta.SmtpAddress or '').strip().lower() != REMITENTE:
        raise RuntimeError('Remitente no autorizado o no verificable.')


def preparar(outlook, cuenta, asunto, cuerpo, adjuntos, para, copias=(), lectura=True,
             marca=None):
    if not para or not set(para).issubset(AUTORIZADOS) or not set(copias).issubset(AUTORIZADOS):
        raise ValueError('Destinatarios fuera de la lista aprobada.')
    correo = outlook.CreateItem(0)
    fijar_cuenta(correo, cuenta)
    correo.SaveSentMessageFolder = cuenta.DeliveryStore.GetDefaultFolder(5)
    correo.DeleteAfterSubmit = False
    correo.To, correo.CC, correo.BCC = ';'.join(para), ';'.join(copias), ''
    correo.Subject, correo.HTMLBody = asunto, cuerpo
    correo.ReadReceiptRequested = bool(lectura)
    correo.Importance = 1
    if marca:
        correo.PropertyAccessor.SetProperty(MARCA, marca)
    for archivo in adjuntos:
        correo.Attachments.Add(str(Path(archivo).resolve()))
    correo.Save()
    if marca and propiedad(correo, MARCA) != marca:
        raise RuntimeError('Outlook no conservó la identificación interna; no se enviará.')
    fijar_cuenta(correo, cuenta)
    comprobar(correo, para, copias)
    return correo


def registrar(asunto_base, adjuntos, espera, intervalo, maximo, seleccionados):
    validar_opciones(espera, intervalo, maximo, seleccionados)
    token = 'DS-' + uuid.uuid4().hex
    carpeta = RAIZ / token
    carpeta.mkdir(parents=True)
    copias = []
    for i, archivo in enumerate(adjuntos):
        destino = carpeta / (str(i + 1) + '_' + Path(archivo).name)
        shutil.copy2(archivo, destino)
        copias.append(str(destino))
    asunto = asunto_base
    with conectar() as db:
        db.execute('''INSERT INTO informes
            (token,asunto,creado,estado,espera,intervalo,maximo,adjuntos,correlacion)
            VALUES (?,?,?,'preparado',?,?,?,?,'interno')''',
            (token, asunto, time.time(), espera, intervalo, maximo, json.dumps(copias)))
        for direccion in DESTINATARIOS + COPIAS:
            db.execute('''INSERT INTO destinatarios
                (token,destinatario,rol,activo,estado) VALUES (?,?,?,?,?)''',
                (token, direccion, 'Para' if direccion in DESTINATARIOS else 'CC',
                 int(direccion in seleccionados), 'pendiente_envio' if direccion in seleccionados else 'sin_recordatorios'))
        db.execute('INSERT INTO mensajes_internos (marca,token,destinatario,asunto) VALUES (?,?,?,?)',
                   (token, token, '', asunto))
    return token, asunto, copias


def propiedad(mensaje, nombre):
    """Solo las propiedades opcionales ausentes se omiten, no las consultas de carpetas."""
    try:
        return mensaje.PropertyAccessor.GetProperty(nombre)
    except Exception:
        return None


def texto_propiedad(mensaje, *tags):
    for tag in tags:
        valor = propiedad(mensaje, MAPI + tag)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return ''


def etiqueta_reporte(mensaje):
    valor = propiedad(mensaje, MAPI + '0x00310102')
    if isinstance(valor, (bytes, bytearray)):
        return bytes(valor).hex()
    if isinstance(valor, (tuple, list)) and valor and all(type(n) is int and 0 <= n <= 255 for n in valor):
        return bytes(valor).hex()
    return ''


def recientes(carpeta, creado, propiedad_fecha):
    # DASL compara las fechas en UTC. No depende de idioma ni formato regional.
    desde = datetime.fromtimestamp(creado - 300, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    return carpeta.Items.Restrict(f'@SQL="{MAPI}{propiedad_fecha}" >= \'{desde}\'')


def sincronizar_enviados(cuenta, informe):
    """Vincula la copia enviada por marca propia; nunca por asunto/fecha solamente."""
    token = informe['token']
    with conectar() as db:
        registros = {r['marca']: dict(r) for r in db.execute(
            'SELECT * FROM mensajes_internos WHERE token=?', (token,))}
    encontrados = {}
    for mensaje in recientes(cuenta.DeliveryStore.GetDefaultFolder(5), informe['creado'], '0x00390040'):
        marca = propiedad(mensaje, MARCA)
        if not isinstance(marca, str) or marca not in registros or not bool(mensaje.Sent):
            continue
        registro = registros[marca]
        if marca in encontrados:
            raise RuntimeError('Identificación interna duplicada en Enviados; revisar Outlook.')
        if str(mensaje.Subject or '') != registro['asunto']:
            raise RuntimeError('El asunto del borrador cambió; seguimiento detenido para revisión.')
        destino = registro['destinatario']
        comprobar(mensaje, [destino] if destino else DESTINATARIOS, [] if destino else COPIAS)
        enviado = fecha_enviado(mensaje)
        if enviado > time.time() + 120 or enviado < informe['creado'] - 300:
            raise RuntimeError('Fecha de envío no válida; revisar relojes.')
        mid = texto_propiedad(mensaje, '0x1035001F', '0x1035001E')
        etiqueta = etiqueta_reporte(mensaje)
        if not mid and not etiqueta:
            raise RuntimeError('Outlook no expone identificadores del mensaje enviado; no se enviarán recordatorios.')
        if ((registro['message_id'] and registro['message_id'] != mid)
                or (registro['report_tag'] and registro['report_tag'] != etiqueta)):
            raise RuntimeError('Los identificadores del mensaje enviado cambiaron; revisar Outlook.')
        with conectar() as db:
            # Una misma clave no puede identificar informes/personas diferentes.
            conflicto = db.execute('''SELECT marca FROM mensajes_internos WHERE marca<>?
                AND ((message_id<>'' AND message_id=?) OR (report_tag<>'' AND report_tag=?))''',
                (marca, mid, etiqueta)).fetchone()
            if conflicto:
                raise RuntimeError('Identificadores internos compartidos entre mensajes; revisión requerida.')
            db.execute('UPDATE mensajes_internos SET message_id=?,report_tag=?,enviado=? WHERE marca=?',
                       (mid, etiqueta, enviado, marca))
        encontrados[marca] = enviado
    return encontrados.get(token)


def registrar_recordatorio(informe, destinatario, numero, asunto):
    if informe.get('correlacion', 'asunto') != 'interno':
        return None  # Compatibilidad con informes de la versión anterior.
    marca = f'{informe["token"]}|{destinatario}|{numero}'
    with conectar() as db:
        db.execute('''INSERT OR IGNORE INTO mensajes_internos
            (marca,token,destinatario,asunto) VALUES (?,?,?,?)''',
            (marca, informe['token'], destinatario, asunto))
    return marca


def cambiar_informe(token, estado, detalle=''):
    with conectar() as db:
        db.execute('UPDATE informes SET estado=?,detalle=? WHERE token=?', (estado, detalle, token))


def cambiar_receptor(identificador, estado, detalle=''):
    with conectar() as db:
        db.execute('UPDATE destinatarios SET estado=?,detalle=? WHERE id=?', (estado, detalle, identificador))


def consultar():
    with conectar() as db:
        return [dict(r) for r in db.execute('''SELECT d.*,i.asunto,i.creado,i.enviado,i.cierre,
            i.espera,i.intervalo,i.maximo,i.estado AS estado_informe,i.detalle AS detalle_informe
            FROM destinatarios d JOIN informes i ON i.token=d.token ORDER BY i.creado DESC,d.id''')]


def cancelar(identificador):
    with conectar() as db:
        db.execute("UPDATE destinatarios SET activo=0,estado='cancelado',detalle='Cancelado por el usuario' WHERE id=?", (identificador,))


def mensajes(carpeta, token):
    if not re.fullmatch(r'DS-[a-f0-9]{32}', token):
        raise RuntimeError('Identificador de informe inválido.')
    with conectar() as db:
        informe = db.execute('SELECT * FROM informes WHERE token=?', (token,)).fetchone()
    if informe and informe['correlacion'] == 'interno':
        return recientes(carpeta, informe['creado'], '0x0E060040')
    return carpeta.Items.Restrict('@SQL="urn:schemas:httpmail:subject" LIKE \'%' + token + '%\'')


def vincular_comprobante(mensaje, token):
    """Devuelve (relacionado, destinatarios permitidos, aviso). No adivina lecturas."""
    with conectar() as db:
        informe = db.execute('SELECT * FROM informes WHERE token=?', (token,)).fetchone()
        if not informe or informe['correlacion'] == 'asunto':
            return True, AUTORIZADOS, ''
        registros = [dict(r) for r in db.execute('SELECT * FROM mensajes_internos WHERE enviado IS NOT NULL')]
    ids = {texto_propiedad(mensaje, '0x1046001F', '0x1046001E'),
           texto_propiedad(mensaje, '0x1042001F', '0x1042001E')} - {''}
    etiqueta = etiqueta_reporte(mensaje)
    coincidencias = [r for r in registros if (r['message_id'] and r['message_id'] in ids)
                     or (etiqueta and r['report_tag'] == etiqueta)]
    propias = [r for r in coincidencias if r['token'] == token]
    if propias:
        if len({r['marca'] for r in coincidencias}) != 1:
            return False, set(), 'Comprobante con identificadores contradictorios; revisar Outlook.'
        destino = propias[0]['destinatario']
        return True, {destino} if destino else AUTORIZADOS, ''
    if coincidencias:
        return False, set(), ''  # Pertenece de forma verificable a otro informe.
    # El asunto solo provoca una pausa conservadora, NUNCA confirma una lectura.
    asunto = str(mensaje.Subject or '')
    original = texto_propiedad(mensaje, '0x0049001F', '0x0049001E')
    if informe['asunto'] in asunto or informe['asunto'] == original:
        return False, set(), 'Comprobante posiblemente relacionado sin clave interna verificable; revisar Outlook.'
    return False, set(), ''


def smtp_comprobante(mensaje, outlook):
    # ReportItem no expone siempre las mismas propiedades que MailItem.
    for tag in ('0x5D01001F', '0x5D01001E', '0x0C1F001F', '0x0C1F001E'):
        try:
            valor = str(mensaje.PropertyAccessor.GetProperty(
                'http://schemas.microsoft.com/mapi/proptag/' + tag) or '').strip().lower()
            if valor in AUTORIZADOS:
                return valor
        except Exception:
            pass
    try:
        valor = str(mensaje.SenderEmailAddress or '').strip().lower()
        if valor in AUTORIZADOS:
            return valor
        if valor.startswith('/o='):
            receptor = outlook.Session.CreateRecipient(valor)
            if receptor.Resolve():
                direccion = direccion_entrada(receptor.AddressEntry)
                if direccion in AUTORIZADOS:
                    return direccion
    except Exception:
        pass
    return None


def comprobantes(carpeta, token, outlook, profundidad=0):
    if profundidad > 20:
        raise RuntimeError('No se pudo revisar toda la bandeja de entrada.')
    lecturas, negativos, avisos = set(), set(), []
    for mensaje in mensajes(carpeta, token):
        clase = str(mensaje.MessageClass or '').upper()
        if clase not in ('REPORT.IPM.NOTE.NDR', 'REPORT.IPM.NOTE.IPNRN', 'REPORT.IPM.NOTE.IPNNRN'):
            continue
        relacionado, permitidos, aviso = vincular_comprobante(mensaje, token)
        if aviso:
            avisos.append(aviso)
        if not relacionado:
            continue
        if clase == 'REPORT.IPM.NOTE.NDR':
            # Un NDR puede referirse a uno solo de los 11: no adivinar cuál.
            avisos.append('Aviso de entrega fallida: revisar Outlook antes de continuar.')
        elif clase in ('REPORT.IPM.NOTE.IPNRN', 'REPORT.IPM.NOTE.IPNNRN'):
            direccion = smtp_comprobante(mensaje, outlook)
            if not direccion or direccion not in permitidos:
                avisos.append('Comprobante sin destinatario verificable: revisar Outlook.')
            elif clase == 'REPORT.IPM.NOTE.IPNRN':
                lecturas.add(direccion)
            else:
                negativos.add(direccion)
    for subcarpeta in carpeta.Folders:
        leidos, no_leidos, otros = comprobantes(subcarpeta, token, outlook, profundidad + 1)
        lecturas.update(leidos)
        negativos.update(no_leidos)
        avisos.extend(otros)
    return lecturas, negativos, avisos


def fecha_enviado(mensaje):
    try:
        valor = mensaje.PropertyAccessor.GetProperty('http://schemas.microsoft.com/mapi/proptag/0x00390040')
        # PT_SYSTIME devuelto por PropertyAccessor está en UTC.
        return datetime(valor.year, valor.month, valor.day, valor.hour,
                        valor.minute, valor.second, tzinfo=timezone.utc).timestamp()
    except Exception:
        valor = mensaje.SentOn
        if not isinstance(valor, datetime):
            raise RuntimeError('No se pudo verificar la hora real de envío.')
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=BOGOTA)
        return valor.timestamp()


def planificar(enviado, espera, maximo):
    local = datetime.fromtimestamp(enviado, BOGOTA)
    cierre = local.replace(hour=15, minute=31, second=0, microsecond=0).timestamp()
    primero = enviado + espera * 60
    return primero, cierre


def en_jornada(ahora, enviado, cierre):
    local = datetime.fromtimestamp(ahora, BOGOTA)
    origen = datetime.fromtimestamp(enviado, BOGOTA)
    return local.date() == origen.date() and local.hour >= 6 and ahora < cierre


def reclamar(identificador, ahora):
    with conectar() as db:
        cursor = db.execute('''UPDATE destinatarios SET estado='intento_recordatorio',
            intentos=intentos+1 WHERE id=? AND activo=1 AND estado='esperando_confirmacion'
            AND proximo<=? AND token IN (SELECT token FROM informes
                WHERE estado='enviado' AND cierre>? AND maximo>destinatarios.intentos)''',
            (identificador, ahora, ahora))
        return cursor.rowcount == 1


def registrar_lecturas(token, lecturas):
    nuevas = []
    with conectar() as db:
        for direccion in lecturas:
            cursor = db.execute('''UPDATE destinatarios SET estado='lectura_confirmada',
                detalle='Comprobante de lectura recibido.' WHERE token=? AND destinatario=?
                AND estado NOT IN ('cancelado','sin_recordatorios','lectura_confirmada')''', (token, direccion))
            if cursor.rowcount:
                nuevas.append(direccion)
    return nuevas


def procesar(outlook, cuenta, informe, publicar):
    token = informe['token']
    ahora = time.time()
    if informe['estado'] in ('preparado', 'original_solicitado'):
        if outlook.Session.Offline:
            return
        if informe.get('correlacion', 'asunto') == 'interno':
            enviado_interno = sincronizar_enviados(cuenta, informe)
            candidatos = [enviado_interno] if enviado_interno is not None else []
        else:
            candidatos = mensajes(cuenta.DeliveryStore.GetDefaultFolder(5), token)
        for mensaje in candidatos:
            if isinstance(mensaje, (float, int)):
                enviado = mensaje
            elif str(mensaje.Subject or '') == informe['asunto'] and bool(mensaje.Sent):
                comprobar(mensaje, DESTINATARIOS, COPIAS)
                enviado = fecha_enviado(mensaje)
            else:
                continue
            if enviado > ahora + 120:
                raise RuntimeError('La fecha de envío está en el futuro; revisar relojes antes del seguimiento.')
            primero, cierre = planificar(enviado, informe['espera'], informe['maximo'])
            with conectar() as db:
                db.execute("UPDATE informes SET estado='enviado',enviado=?,cierre=? WHERE token=? AND estado IN ('preparado','original_solicitado')", (enviado, cierre, token))
                db.execute("UPDATE destinatarios SET estado='esperando_confirmacion',proximo=? WHERE token=? AND estado='pendiente_envio' AND activo=1", (primero, token))
            publicar(f'{token}: envío verificado; primer recordatorio previsto {datetime.fromtimestamp(primero, BOGOTA):%d/%m %H:%M}.')
            return
        if ahora - informe['creado'] > 86400:
            cambiar_informe(token, 'sin_envio_verificado', 'No se encontró original en Enviados durante 24 h.')
        return
    if informe['estado'] != 'enviado':
        return
    if ahora >= informe['cierre']:
        with conectar() as db:
            db.execute("UPDATE destinatarios SET estado='jornada_finalizada',detalle='No se enviará fuera de jornada ni otro día.' WHERE token=? AND estado='esperando_confirmacion'", (token,))
            db.execute("UPDATE informes SET estado='jornada_finalizada' WHERE token=?", (token,))
        publicar(token + ': jornada finalizada; no se enviarán más recordatorios.')
        return
    if outlook.Session.Offline:
        return
    sin_verificar = None
    if informe.get('correlacion', 'asunto') == 'interno':
        sincronizar_enviados(cuenta, informe)
        with conectar() as db:
            sin_verificar = db.execute('''SELECT m.marca,d.proximo FROM mensajes_internos m
                JOIN destinatarios d ON d.token=m.token AND d.destinatario=m.destinatario
                WHERE m.token=? AND m.enviado IS NULL AND d.intentos>0
                AND m.marca=m.token||'|'||m.destinatario||'|'||d.intentos''', (token,)).fetchone()
    bandeja = cuenta.DeliveryStore.GetDefaultFolder(6)
    lecturas, _, avisos = comprobantes(bandeja, token, outlook)
    for direccion in registrar_lecturas(token, lecturas):
        publicar(f'{token}: CONFIRMACIÓN RECIBIDA de {direccion}; sus recordatorios cancelados.')
    if avisos:
        raise RuntimeError('; '.join(sorted(set(avisos))))
    if sin_verificar:
        # Dar tiempo a sincronizar Enviados. Nunca solicitar el siguiente sin
        # poder reconocer las confirmaciones del recordatorio anterior.
        if ahora >= sin_verificar['proximo']:
            raise RuntimeError('No se verificó la copia enviada del recordatorio; revisar Outlook antes de continuar.')
        return
    with conectar() as db:
        filas = [dict(r) for r in db.execute('SELECT * FROM destinatarios WHERE token=? AND activo=1', (token,))]
    for fila in filas:
        if fila['estado'] != 'esperando_confirmacion':
            continue
        if fila['intentos'] >= informe['maximo']:
            cambiar_receptor(fila['id'], 'limite_alcanzado', 'Máximo de recordatorios alcanzado; sin confirmación.')
            continue
        if not en_jornada(time.time(), informe['enviado'], informe['cierre']):
            continue
        if time.time() < fila['proximo']:
            continue
        adjuntos = json.loads(informe['adjuntos'])
        if not all(Path(p).is_file() for p in adjuntos):
            raise RuntimeError('Falta una copia de los adjuntos. No se enviarán recordatorios.')
        numero = fila['intentos'] + 1
        asunto_recordatorio = f'Recordatorio {numero} — {informe["asunto"]}'
        marca = registrar_recordatorio(informe, fila['destinatario'], numero, asunto_recordatorio)
        correo = preparar(outlook, cuenta,
            asunto_recordatorio,
            '<html><body style="font-family:Segoe UI,Arial,sans-serif;color:#333">'
            '<h3 style="color:#00995c">Recordatorio de revisión</h3>'
            '<p>No se ha recibido confirmación de lectura de este informe. '
            'Se comparte nuevamente para facilitar su consulta.</p>'
            '<p>La ausencia de confirmación no demuestra que el correo no se haya abierto.</p>'
            f'<p>Informe: {html.escape(informe["asunto"])}</p></body></html>',
            adjuntos, [fila['destinatario']], lectura=True, marca=marca)
        # Revisión individual justo antes de enviar. No usar ReplyAll/Forward.
        leidos, _, nuevos_avisos = comprobantes(bandeja, token, outlook)
        for direccion in registrar_lecturas(token, leidos):
            publicar(f'{token}: CONFIRMACIÓN RECIBIDA de {direccion}; sus recordatorios cancelados.')
        if nuevos_avisos:
            raise RuntimeError('; '.join(sorted(set(nuevos_avisos))))
        instante = time.time()
        if outlook.Session.Offline or not en_jornada(instante, informe['enviado'], informe['cierre']):
            continue
        if not reclamar(fila['id'], instante):
            continue
        correo.Send()
        with conectar() as db:
            db.execute("UPDATE destinatarios SET estado='esperando_confirmacion',proximo=?,detalle=? WHERE id=? AND estado='intento_recordatorio'",
                (instante + informe['intervalo'] * 60,
                 f'Recordatorio {numero} solicitado a Outlook; no demuestra entrega.', fila['id']))
        publicar(f'{token}: recordatorio {numero}/{informe["maximo"]} solo a {fila["destinatario"]}.')


def iniciar_monitor(publicar):
    global _hilo, _publicar
    with _guardia:
        _publicar = publicar  # Reasociar la consola si se reconstruye la vista.
        if _hilo is not None and _hilo.is_alive():
            return

        def trabajar():
            try:
                import pythoncom
                import win32com.client
            except ImportError:
                _publicar('Seguimiento no iniciado: instale pywin32 en el entorno de DataSuite.')
                return
            pythoncom.CoInitialize()
            try:
                while True:
                    try:
                        with conectar() as db:
                            informes = [dict(r) for r in db.execute("SELECT * FROM informes WHERE estado IN ('preparado','original_solicitado','enviado')")]
                        if informes:
                            outlook = win32com.client.gencache.EnsureDispatch('Outlook.Application', bForDemand=0)
                            cuenta = cuenta_autorizada(outlook)
                            for informe in informes:
                                try:
                                    procesar(outlook, cuenta, informe, lambda s: _publicar(s))
                                except Exception as error:
                                    cambiar_informe(informe['token'], 'revision_requerida', str(error))
                                    _publicar(informe['token'] + ': seguimiento detenido para revisión. ' + str(error))
                    except Exception as error:
                        _publicar('Monitor pausado; no se solicita ningún envío: ' + str(error))
                    time.sleep(15)
            finally:
                pythoncom.CoUninitialize()

        _hilo = threading.Thread(target=trabajar, daemon=True)
        _hilo.start()
