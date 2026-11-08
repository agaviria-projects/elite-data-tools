"""Prueba aislada del nuevo motor: SOLO al correo de Héctor, nunca al equipo.

Colocar junto al lanzador, fuera de modules. Ejecutar en el venv del proyecto:
    python prueba_asunto_limpio.py
Abre un borrador para envío MANUAL. Máximo un recordatorio tras un minuto.
No modifica la configuración ni la base de seguimiento de DataSuite.
"""
from datetime import datetime
from pathlib import Path
import time
import uuid

from modules import seguimiento_lectura as motor


def main():
    import pythoncom
    import win32com.client

    # Se restringe la lista en este proceso aislado, no se editan los módulos.
    motor.DESTINATARIOS = [motor.REMITENTE]
    motor.COPIAS = []
    motor.AUTORIZADOS = {motor.REMITENTE}
    motor.RAIZ = (Path(__file__).resolve().parent / 'seguimiento_asunto_prueba'
                  / ('prueba-' + uuid.uuid4().hex))
    ahora = datetime.now(motor.BOGOTA)
    if ahora.hour < 6 or (ahora.hour, ahora.minute) >= (15, 29):
        print('Realice esta prueba entre las 06:00 y las 15:28, hora Colombia.')
        return
    print('PRUEBA AISLADA: solo a ' + motor.REMITENTE + '. Sin CC ni CCO.')
    print('Se abrirá un borrador; usted decide enviarlo. No cambie los destinatarios.')
    print('A) Ábralo y acepte enviar comprobante: debe cancelar el recordatorio.')
    print('B) En otra ejecución, no abra el recibido: debe llegar un único recordatorio.')
    print('Mantenga Outlook y esta consola abiertos. Ctrl+C detiene la prueba.')
    if input('Para abrir el borrador escriba SI: ').strip().upper() != 'SI':
        print('Cancelado. No se creó ningún correo.')
        return
    pythoncom.CoInitialize()
    token = None
    try:
        outlook = win32com.client.gencache.EnsureDispatch('Outlook.Application', bForDemand=0)
        cuenta = motor.cuenta_autorizada(outlook)
        token, asunto, adjuntos = motor.registrar(
            'PRUEBA — Seguimiento con asunto limpio — ' + ahora.strftime('%d/%m/%Y %H:%M:%S'),
            [], 1, 1, 1, [motor.REMITENTE])
        correo = motor.preparar(outlook, cuenta, asunto,
            '<html><body><h3>Prueba de asunto limpio</h3>'
            '<p>Solo a mi correo. No se incluyen destinatarios reales ni adjuntos.</p>'
            '<p>Sin confirmación se solicitará un solo recordatorio después de un minuto.</p>'
            '<p>La ausencia de comprobante no demuestra que no se haya leído.</p></body></html>',
            adjuntos, [motor.REMITENTE], lectura=True, marca=token)
        correo.Display()
        print('Borrador abierto. Revise que solo aparece su cuenta y pulse Enviar en Outlook.')
        motor.iniciar_monitor(lambda texto: print(datetime.now(motor.BOGOTA).strftime('%H:%M:%S'), texto, flush=True))
        limite = time.time() + 900
        while time.time() < limite:
            filas = [r for r in motor.consultar() if r['token'] == token]
            if filas:
                fila = filas[0]
                if fila['estado_informe'] in ('revision_requerida', 'error_sin_reintento'):
                    print('DETENIDO PARA REVISIÓN:', fila['detalle_informe'])
                    break
                if fila['estado'] in ('lectura_confirmada', 'limite_alcanzado', 'jornada_finalizada'):
                    print('Prueba terminada:', fila['estado'], '—', fila['detalle'])
                    break
            time.sleep(1)
        else:
            print('Tiempo de prueba agotado; no se continuará el seguimiento.')
    except KeyboardInterrupt:
        print('\nPrueba detenida por el usuario.')
    except Exception as error:
        print('ERROR. No se reintentará el envío:', error)
    finally:
        if token:
            motor.cambiar_informe(token, 'prueba_finalizada', 'Proceso de prueba cerrado; no reanudar.')
        pythoncom.CoUninitialize()


if __name__ == '__main__':
    main()
