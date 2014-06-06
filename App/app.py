# -*- coding: utf-8 -*-

# Librerias externas.
import os
import sqlite3
import hashlib

# El uso de locks es para los threads que sirven las paginas de Flask.
import threading

from functools import wraps

from math import ceil

from twisted.internet import reactor

from twisted.web.wsgi import WSGIResource
from twisted.web.server import Site
from twisted.web.static import File

from twisted.python.threadpool import ThreadPool

from autobahn.twisted.resource import WebSocketResource, WSGIRootResource
from autobahn.twisted.websocket import WebSocketServerFactory

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.utils import secure_filename

# Otros modulos de la aplicacion.
import utils

from db import alterDB, createDB, destroyDB, queryDB

from protocols import LibraServerProtocol
from protocols import HRProtocol # Utilizado por halt/reboot.

from config import CONFIG, APP_CONFIG_PATH, APP_PATH
from config import DATABASE_PATH, TEMPLATES_PATH, STATIC_FILES_PATH, UPDATES_PATH
from config import WPA_FILE_PATH, INTERFACE_FILE_PATH
from config import PAGE_DASHBOARD, PAGE_LOGIN, PAGE_LOGOUT, PAGE_PRODUCT, PAGE_PRODUCTS, PAGE_UPDATE
from config import PAGE_SHUTDOWN, PAGE_REBOOT, PAGE_NETCONFIG, PAGE_CHANGEPASS

from devices import arduino, lcd

# La aplicacion Flask.
app = Flask(__name__, template_folder=TEMPLATES_PATH)
app.config.update(CONFIG)

def main():
    ''' Punto de entrada de la aplicacion. '''

    # Habilitamos la interfaz Web solo si hay conexion a la red local.
    if CONFIG['NC_ADDRESS'] is not None:

        # Creamos un thread pool para la aplicacion.
        threadPool = ThreadPool(maxthreads=CONFIG['SERVER_MAX_THREADS'])
        threadPool.start()
        reactor.addSystemEventTrigger('before', 'shutdown', threadPool.stop)
        app.mutex = threading.Lock()

        # Creamos los diferentes recursos que servira el servidor de Twisted.
        wsgiResource = WSGIResource(reactor, threadPool, app)
        
        staticResource = File(STATIC_FILES_PATH)
        tmpCSVResource = File('/tmp')

        webSocketFactory = WebSocketServerFactory('ws://{0}:{1}'.format(CONFIG['SERVER_INTERFACE'],
            CONFIG['SERVER_PORT'])) 
        webSocketFactory.protocol = LibraServerProtocol
        webSocketResource = WebSocketResource(webSocketFactory)

        rootResource = WSGIRootResource(wsgiResource, {'static' : staticResource, 'ws' : webSocketResource,
            'csv' : tmpCSVResource })

        site = Site(rootResource)
        reactor.listenTCP(CONFIG['SERVER_PORT'], site)

    # Mostramos si hay conexion a la red local.
    if not CONFIG['DEVELOPMENT']:
        if CONFIG['NC_ADDRESS'] is not None:
            lcd.showMessage('{0}'.format(CONFIG['NC_ADDRESS']), '{0}'.format(CONFIG['SERVER_PORT']))
        else:
            lcd.showMessage('Desconectado')

    reactor.run()

class requireAuthenticatedUser():
    ''' Decorator que revisa que el usuario se haya autenticado. '''

    def __call__(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'authenticated' in session and session['authenticated'] == True:
                return f(*args, **kwargs)
            else:
                return redirect(url_for('login'))

        return decorated

class DeviceBusyError(Exception):
    pass

class Pagination(object):
    '''
        Esta clase corresponde a un snippet creado por Armin Ronacher.
        Ver: http://flask.pocoo.org/snippets/44/
    '''

    def __init__(self, page, perPage, totalCount):
        self.page = page
        self.pages = int(ceil(totalCount/float(perPage)))
        self.hasPrev = page > 1
        self.hasNext = page < self.pages

    def iter_pages(self, leftEdge=2, rightEdge=2, leftCurrent=2, rightCurrent=5):
        last = 0
        for n in xrange(1, self.pages+1):
            if n <= leftEdge or (n > self.page-leftCurrent-1 and n < self.page+rightCurrent) or \
               n > self.pages-rightEdge:
                if last+1 != n:
                    yield None
                yield n
                last = n

# Funciones de Flask.
@app.route('/', methods=['GET'])
@requireAuthenticatedUser()
def index():
    ''' Codigo que maneja el punto de entrada de la aplicacion. '''
    return redirect(url_for('dashboard'))

@app.route(PAGE_LOGIN[0], methods=['POST', 'GET'])
def login():
    ''' Codigo que maneja el inicio de sesion. '''
    if request.method == 'POST':
        username = hashlib.sha512(request.form['username']).hexdigest()
        password = hashlib.sha512(request.form['password']).hexdigest()
        if CONFIG['WEB_USERNAME'] == username and CONFIG['WEB_PASSWORD'] == password:
            session['authenticated'] = True
            flash('Ha iniciado sesion.')
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', title=PAGE_LOGIN[1], error='Credenciales incorrectos')
    else:
        if 'authenticated' in session and session['authenticated'] == True:
            return redirect(url_for('dashboard'))
        else:
            session['authenticated'] = False
            return render_template('login.html', title=PAGE_LOGIN[1], error=None)

@app.route(PAGE_LOGOUT, methods=['GET'])
@requireAuthenticatedUser()
def logout():
    ''' Codigo que maneja el cierre de sesion. '''

    session['authenticated'] = False
    flash('Ha cerrado la sesion.')
    return redirect(url_for('login'))

@app.route(PAGE_DASHBOARD[0], methods=['GET'])
@requireAuthenticatedUser()
def dashboard():
    ''' Codigo que maneja el dashboard de la aplicacion. '''

    createDB()
    products = queryDB('SELECT id, name FROM products;')
    destroyDB()

    kwargs = {}
    kwargs['title'] = PAGE_DASHBOARD[1]
    kwargs['serverAddr'] = CONFIG['NC_ADDRESS']
    kwargs['serverPort'] = CONFIG['SERVER_PORT']
    kwargs['products'] = products

    return render_template('dashboard.html', **kwargs)

@app.route(PAGE_PRODUCTS[0], defaults={'page' : 1}, methods=['GET'])
@app.route(PAGE_PRODUCTS[0]+'/pag/<int:page>')
@requireAuthenticatedUser()
def products(page):
    ''' Codigo que maneja el listado de productos de la aplicacion. '''

    createDB();
    count = queryDB('SELECT count(*) from products;', one=True)[0]
    
    kwargs = {}

    minID = (page-1)*CONFIG['PRODUCTS_PER_PAGE']+1
    maxID = page*CONFIG['PRODUCTS_PER_PAGE']
    kwargs['products'] = queryDB('SELECT id, name FROM products WHERE id >= ? and id <= ?', (str(minID), str(maxID)))
    destroyDB()

    if not kwargs['products'] and page != 1:
        abort(404)

    kwargs['page'] = page
    kwargs['pagination'] = Pagination(page, CONFIG['PRODUCTS_PER_PAGE'], count)
    kwargs['title'] = PAGE_PRODUCTS[1]

    return render_template('products.html', **kwargs)

@app.route(PAGE_PRODUCT[0], methods=['POST', 'GET'])
@app.route(PAGE_PRODUCT[0]+'/id/<int:id>', methods=['POST', 'GET'])
@requireAuthenticatedUser()
def product(id=None):
    ''' Codigo que maneja un producto. '''

    createDB()

    kwargs = {}
    kwargs['product'] = (None,'','','')
    kwargs['measurements'] = []
    kwargs['title'] = 'Crear producto'
    kwargs['mode'] = 'insert'
    kwargs['serverAddr'] = CONFIG['NC_ADDRESS']
    kwargs['serverPort'] = CONFIG['SERVER_PORT']

    if(id is not None):
        kwargs['mode'] = 'update'
        if request.method == 'GET':
            product = queryDB('SELECT * FROM products WHERE id = ?;', (id,))
            if product:
                kwargs['product'] = product[0]
                measurements = queryDB('SELECT * FROM measurements WHERE product_id = ? LIMIT 25;', (id,))
                kwargs['measurements'] = measurements
                kwargs['title'] = product[0][1]
            else:
                abort(404)
        else:
            # Leemos el formulario y actualizamos.
            name = request.form['name']
            minWeight = request.form['minWeight']
            maxWeight = request.form['maxWeight']
            if isFloat(minWeight) and isFloat(maxWeight) and float(minWeight) < float(maxWeight) and len(name) > 0: 
                alterDB('UPDATE products SET name = ?, min_weight = ?, max_weight = ? WHERE id = ?;',
                    (name, minWeight, maxWeight, id))
                flash('Producto actualizado!')
            else:
                flash('Datos invalidos!')

            kwargs['product'] = (id,name,minWeight,maxWeight)
            kwargs['title'] = name
            kwargs['mode'] = 'update'
            measurements = queryDB('SELECT * FROM measurements WHERE product_id = ? LIMIT 25;', (id,))
            kwargs['measurements'] = measurements
    else:
        if request.method == 'POST':
            # Creamos el producto.
            name = request.form['name']
            minWeight = request.form['minWeight']
            maxWeight = request.form['maxWeight']
            if isFloat(minWeight) and isFloat(maxWeight) and float(minWeight) < float(maxWeight) and len(name) > 0: 
                id = alterDB('INSERT INTO products(name, min_weight, max_weight) VALUES (?,?,?);',
                    (name, minWeight, maxWeight))
                flash('Producto creado!')
                return redirect(url_for('products'))
            else:
                flash('Datos invalidos!')
                kwargs['product'] = (None, name, minWeight, maxWeight)

    destroyDB() 
      
    return render_template('product.html', **kwargs)

@app.route(PAGE_UPDATE[0], methods=['POST', 'GET'])
@requireAuthenticatedUser()
def update():
    ''' Codigo que maneja la subida de archivos de actualizacion. '''

    if request.method == 'POST':
        f = request.files['tarball']
        if f:
            exts = f.filename.rsplit('.')
            if len(exts) >= 3 and 'tar' == exts[-2] and 'gz' == exts[-1]:
                filename = secure_filename(f.filename)
                f.save(os.path.join(UPDATES_PATH, filename))
                with open(os.path.join(UPDATES_PATH, 'update_pending'), 'w') as f:
                    f.write('{0}\n'.format(filename))
                    f.close()
                flash('Archivo de actualizacion "{0}" subido exitosamente.'.format(filename))
                return redirect(url_for('reboot'))
            else:
                flash('Archivo de actualizacion invalido.')
        else:
            flash('Ocurrio un error subiendo el archivo.')

    return render_template('update.html', title=PAGE_UPDATE[1])

@app.route(PAGE_SHUTDOWN, methods=['GET'])
@requireAuthenticatedUser()
def shutdown():
    ''' Codigo que apaga el dispositivo. '''

    reactor.callLater(5, halt)
    flash('El sistema se apagara pronto.')
    return redirect(url_for('logout'))

@app.route(PAGE_REBOOT, methods=['GET'])
@requireAuthenticatedUser()
def reboot():
    ''' Codigo que apaga el dispositivo. '''

    reactor.callLater(5, reboot)
    flash('El sistema se reiniciara pronto.')
    return redirect(url_for('logout'))

@app.route(PAGE_NETCONFIG[0], methods=['POST', 'GET'])
@requireAuthenticatedUser()
def netconfig():
    ''' Codigo que cambia la configuracion de red. '''
    if request.method == 'POST':

        # Vemos si hubo cambios en la configuracion de la interfaz.
        oldNetType = CONFIG['NC_TYPE']
        newNetType = request.form['netType']
        netConfig = None

        # Originalmente estaba configurada estaticamente y sigue estandolo,
        # u originalmente estaba configurada dinamicamente y
        # ahora lo esta estaticamente.
        if ('static' == oldNetType and 'static' == newNetType) or \
           ('dynamic' == oldNetType and 'static' == newNetType):

            netConfig = []
            netConfig.append(request.form['address'])
            netConfig.append(request.form['network'])
            netConfig.append(request.form['netmask'])
            netConfig.append(request.form['broadcast'])
            netConfig.append(request.form['gateway'])
            netConfig.append(request.form['ssid'])
            netConfig.append(request.form['psk'])

        elif 'static' == oldNetType and 'dynamic' == newNetType:
            netConfig = []
        else:
            newNetType = None

        # Vemos si hubo cambios en la configuracion de red.
        wpaConfig = (request.form['ssid'], request.form['psk'])
        if wpaConfig[0] == CONFIG['NC_WPA_SSID'] and wpaConfig[1] == CONFIG['NC_WPA_PSK']:
            wpaConfig = None

        # Actualizamos y reiniciamos solo si hay algun cambio.
        if newNetType is not None or wpaConfig is not None:
            try:
                if updateNetworkConfiguration(newNetType, netConfig, wpaConfig):
                    return redirect(url_for('reboot'))
                else:
                    flash(u'Ocurrió un error actualizando la configuración de red.')
            except DeviceBusyError:
                flash(u'Dispositivo ocupado, alguien más intenta actualizarlo!')
        else:
            flash('Sin cambios que aplicar!')

    # Carga el formulario.
    kwargs = {}
    kwargs['title'] = PAGE_NETCONFIG[1]
    kwargs['macs'] = CONFIG['NC_MACS']
    kwargs['netType'] = CONFIG['NC_TYPE']
    kwargs['interface'] = CONFIG['NC_INTERFACE']
    kwargs['address'] = CONFIG['NC_ADDRESS']
    kwargs['network'] = CONFIG['NC_NETWORK']
    kwargs['broadcast'] = CONFIG['NC_BROADCAST']
    kwargs['netmask'] = CONFIG['NC_NETMASK']
    kwargs['gateway'] = CONFIG['NC_GATEWAY']
    kwargs['ssid'] = CONFIG['NC_WPA_SSID']
    kwargs['psk'] = CONFIG['NC_WPA_PSK']

    return render_template('netconfig.html', **kwargs)

@app.route(PAGE_CHANGEPASS[0], methods=['POST', 'GET'])
@requireAuthenticatedUser()
def changepass():
    ''' Codigo que cambia los credenciales. '''
    if request.method == 'POST':

        oldpass = hashlib.sha512(request.form['oldpass']).hexdigest()
        newpass1 = request.form['newpass1']
        newpass2 = request.form['newpass2']

        if oldpass == CONFIG['WEB_PASSWORD'] and len(newpass1) >= 6 and newpass1 == newpass2:
            # Intentamos adquirir el mutex, sin bloquear.
            if app.mutex.acquire(False):
                CONFIG['WEB_PASSWORD'] = hashlib.sha512(newpass1).hexdigest()
                utils.writeConfig(CONFIG, APP_CONFIG_PATH)
                app.mutex.release()
                flash(u'Contraseña actualizada con éxito.')
                return redirect(url_for('logout'))
            else:
                flash(u'Dispositivo ocupado, alguien más intenta actualizarlo!')
        else:
            flash(u'Error: alguno de los campos es inválido.')

    return render_template('changepass.html', title=u'Cambiar contraseña')

# Funciones auxiliares.
def updateNetworkConfiguration(netType, netConfig, wpaConfig):
    ''' Actualiza la configuracion de red.
        netType: static | dynamic
        netConfig: (address, network, netmask, broadcast, gateway)
        wpaConfig: (ssid, psk)
        appConfig: archivo de configuracion de la aplicacion
        Consulte "man ifconfig" para informacion de configuracion.
    '''

    # Intentamos actualizar las interfaces de red.
    if netType is not None and netConfig is not None:
        interfacesTemplate = None
        template = 'ncstatic' if 'static' == netType else 'ncdynamic'
        with open(os.path.join(APP_PATH, template), 'r') as templateFile:
            interfacesTemplate = templateFile.read()
            templateFile.close()

        # Ocurrio un error, retornamos.
        if interfacesTemplate is None:
            return False

        if 'static' == netType:

            interfacesNew = interfacesTemplate
            for i,text in enumerate(netConfig):
                interfacesNew = interfacesNew.replace('{%s}' % i, text)
        else:
            interfacesNew = interfacesTemplate # verbatim

        # Intentamos adquirir el mutex, sin bloquear.
        if app.mutex.acquire(False):
            with open(INTERFACE_FILE_PATH, 'w') as interfacesFile:
                interfacesFile.write(interfacesNew)
                interfacesFile.close()

                # Actualizamos la configuracion.
                CONFIG['NC_TYPE'] = 'static' if 'static' == netType else 'dynamic'
                utils.writeConfig(CONFIG, APP_CONFIG_PATH)
            app.mutex.release()
        else:
            raise DeviceBusyError()

    # Intentamos actualizar la configuracion de WPA Supplicant.
    if wpaConfig is not None:
        wpaTemplate = None
        with open(os.path.join(APP_PATH, 'ncwpa'), 'r') as templateFile:
            wpaTemplate = templateFile.read()
            templateFile.close() 

        # Ocurrio un error, retornamos.
        if wpaTemplate is None:
            return False

        wpaNew = wpaTemplate.replace('{0}',wpaConfig[0]).replace('{1}',wpaConfig[1])

        # Intentamos adquirir el mutex, sin bloquear.
        if app.mutex.acquire(False):
            with open(WPA_FILE_PATH, 'w') as wpaFile:
                wpaFile.write(wpaNew)
                wpaFile.close()

                # Actualizamos la configuracion.
                CONFIG['NC_WPA_SSID'], CONFIG['NC_WPA_PSK'] = wpaConfig
                utils.writeConfig(CONFIG, APP_CONFIG_PATH)
            app.mutex.release()
        else:
            raise DeviceBusyError()

    return True

def halt():
    reactor.spawnProcess(HRProtocol('halting...'), os.path.join(APP_PATH, 'halt'), (), {})

def reboot():
    reactor.spawnProcess(HRProtocol('rebooting...'), os.path.join(APP_PATH, 'reboot'), (), {})

def isFloat(s):
    try:
        f = float(s)
        return True
    except ValueError:
        return False

if __name__ == '__main__':
    main()
