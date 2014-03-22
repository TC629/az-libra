# -*- coding: utf-8 -*-

import os
import utils

APP_PATH = os.path.abspath('/opt/libra/')
FILES_PATH = os.path.abspath('/var/libra')

APP_CONFIG_PATH = os.path.join(FILES_PATH, 'config.txt')
CONFIG = utils.readConfig(APP_CONFIG_PATH)

CONFIG['NC_INTERFACE'], CONFIG['NC_ADDRESS'], CONFIG['NC_NETWORK'], \
CONFIG['NC_BROADCAST'], CONFIG['NC_NETMASK'], CONFIG['NC_GATEWAY'] = utils.getNetworkInfo()

CONFIG['NC_MACS'] = utils.getMacAddresses()

DATABASE_PATH = os.path.join(FILES_PATH, CONFIG['DBNAME'])

UPDATES_PATH = os.path.join(FILES_PATH, 'updates')
UPDATE_PENDING_PATH = os.path.join(UPDATES_PATH, 'update_pending')

TMP_FILES_PATH = os.path.join(FILES_PATH, 'tmp')

STATIC_FILES_PATH = os.path.join(APP_PATH, 'static')
TEMPLATES_PATH = os.path.join(APP_PATH, 'templates')

# Cambiamos la ruta de estos archivos dependiendo de si estamos en una
# maquina de desarrollo o no!
if 'DEVELOPMENT' in CONFIG and CONFIG['DEVELOPMENT'] == True:
    INTERFACE_FILE_PATH = os.path.join(FILES_PATH, 'interfaces')
    WPA_FILE_PATH = os.path.join(FILES_PATH, 'wpa_supplicant.conf')
else:
    INTERFACE_FILE_PATH = os.path.abspath('/etc/network/interfaces')
    WPA_FILE_PATH = os.path.abspath('/etc/wpa_supplicant.conf')

# El primer componente de la tupla describe el URL de la pagina y el 
# segundo el texto que se utiliza para el titulo de la misma.
PAGE_DASHBOARD = ('/dashboard', 'Dashboard')
PAGE_LOGIN = ('/iniciar-sesion', u'Iniciar sesión')
PAGE_LOGOUT = '/cerrar-sesion'
PAGE_PRODUCT = ('/product', 'Producto')
PAGE_PRODUCTS = ('/productos', 'Productos')
PAGE_UPDATE = ('/actualizar', u'Subir archivo de actualización')
PAGE_SHUTDOWN = '/apagar'
PAGE_REBOOT = '/reiniciar'
PAGE_NETCONFIG = ('/configuracion-de-red', u'Configuración de red')
PAGE_CHANGEPASS = ('/actualizar-credenciales', u'Actualizar credenciales')
