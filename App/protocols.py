import json
import os

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ProcessProtocol
from twisted.protocols.basic import LineReceiver
from twisted.enterprise import adbapi

from twisted.internet import utils as twisted_utils

from autobahn.twisted.websocket import WebSocketServerProtocol

from config import APP_PATH, DATABASE_PATH

dbpool = adbapi.ConnectionPool('sqlite3', DATABASE_PATH, check_same_thread=False)

class LCDProtocol(Protocol):
    ''' Protocolo para controlar la LCD serial de Sparkfun.
        Para una referencia de los comandos ver:
        https://github.com/jimblom/Serial-LCD-Kit/wiki/Serial-Enabled-LCD-Kit-Datasheet
    '''

    def dataReceived(self, data):
        pass

    def showMessage(self, line1, line2=None):
        self.transport.write('\xFE\x01')
        # 16 caracteres de ancho maximo
        self.transport.write(line1[0:16].ljust(16,' '))
        if line2 is not None:
            self.transport.write(line2[0:16].ljust(16,' '))

class ArduinoClientProtocol(LineReceiver):
    ''' Protocolo que maneja la comunicacion con el Arduino.
        Se hereda de LineReceiver porque los mensajes que se envian
        desde Arduino utilizan Serial.println.
    '''

    def alert(self, data):
        print('Recibido: {0}'.format(data))

    def processData(self, data):
        # Prueba que se hizo con un push button.
        #dbpool.runQuery("update foo set count = count+1 where id = 1;", ()).addCallback(self.alert)
        pass

    def lineReceived(self, line):
        try:
            data = line.split()
            self.processData(data)
        except ValueError:
            print('Error al intentar parsear: %s' % line)
            return

    def start(self, serverAddr):
        ''' Envia un byte al Arduino para darle la sennal de iniciar.
            Esto lo hacemos con el objetivo de que el Arduino no envie nada
            hasta que el servidor libra este listo para recibir datos.
        '''
        print('Iniciando sistema Arduino.')
        self.transport.write('b')

    def shutdown(self):
        ''' Envia un mensaje al Arduino para que se detenga. '''
        print('Apagando sistema Arduino.')
        # Falta implementar

class LibraServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print('Nueva conexion: {0}'.format(request.peer))

    def onOpen(self):
        pass

    def onMessage(self, payload, isBinary):
        args = json.loads(payload)
        if(args['command'] == 'tocsv'):
            output = twisted_utils.getProcessOutput(os.path.join(APP_PATH, 'tocsv'), (str(args['id']),))
            output.addCallback(lambda val : self.sendMessage(val.replace('tmp','csv')))
        else:
            pass

    def onClose(self, wasClean, code, reason):
        print('Conexion terminada.')

class HRProtocol(ProcessProtocol):
    ''' HR (Halt/Reboot)
        Protocolo para utilizar con reactor.spawnProcess para
        correr los scripts de Bash que apagan o reinician el
        pcDuino. No hacemos nada con el output de los procesos.
        Notese que halt/shutdown fallaran en ejecutarse en la maquina
        de desarrollo, salvo que se haya corrido con "sudo".
    '''

    def __init__(self, msg=''):
        self.msg = msg
    
    def connectionMade(self):
        pass

    def outReceived(self, data):
        pass

    def errReceived(self, data):
        pass

    def inConnectionLost(self):
        pass

    def outConnectionLost(self):
        pass

    def errConnectionLost(self):
        pass

    def processExited(self, reason):
        print(self.msg)

    def processEnded(self, reason):
        reactor.stop()
