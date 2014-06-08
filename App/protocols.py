import json
import os
import time

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ProcessProtocol
from twisted.protocols.basic import LineReceiver
from twisted.enterprise import adbapi

from twisted.internet import utils as twisted_utils

from autobahn.twisted.websocket import WebSocketServerProtocol

from config import APP_PATH, CONFIG, DATABASE_PATH

dbpool = adbapi.ConnectionPool('sqlite3', DATABASE_PATH, check_same_thread=False)

# Lleva control de conexiones via WebSockets que solicitan datos
# para el dashboard.
dashboard_clients = []

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

    def lineReceived(self, line):
        data = line.split()[0]

        if data == 'ack' or data == 'nack' or data == 'halted':
            print(data)
        elif data == 'ready':
            print('Arduino listo!')
            self.transport.write('<2;>')
        else:
            scale_id, weight = data.split(';')
            timestamp = time.strftime("%H:%M:%S")
            print('{0} : {1} : {2}'.format(scale_id, weight, timestamp))
            dbpool.runQuery('insert into measurements(product_id, scale_id, weight, timestamp) values(?, ?, ?, CURRENT_TIMESTAMP);',
                (CONFIG['CURRENT_PRODUCT'], scale_id, weight))
            for client in dashboard_clients:
                client.updateDashboard(scale_id, weight, timestamp)

    def shutdown(self):
        ''' Envia un mensaje al Arduino para que se detenga. '''
        print('Apagando sistema Arduino.')
        self.transport.write('<3;>')

    def setWeights(self, min_weight, max_weight):
        self.transport.write('<0;{0}><1;{1}>'.format(min_weight, max_weight))

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
        elif(args['command'] == 'update_dashboard'):
            global dashboard_clients
            dashboard_clients.append(self)

    def onClose(self, wasClean, code, reason):
        global dashboard_clients
        if self in dashboard_clients:
            dashboard_clients.remove(self)

    def updateDashboard(self, scale_id, weight, timestamp):
        self.sendMessage(json.dumps({ 'scale_id' : scale_id, 'weight' : weight, 'timestamp' : timestamp}))

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
