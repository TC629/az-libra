import subprocess
import re
import os

from twisted.internet import reactor

def _getIfconfigOutput():
    ''' Utiliza el programa ifconfig (o busybox ifconfig) para encontrar la
        informacion de red de las diferentes interfaces que no sean la loopback.
    '''

    # Obtenemos el resultado de correr "ifconfig"
    devnull = open('/dev/null', 'w')
    ifconfig_proc = subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE, stderr=devnull)
    output = ifconfig_proc.stdout.read()
    ifconfig_proc.stdout.close()
    exitcode = ifconfig_proc.wait()
    devnull.close()

    return output

def _getIpRouteOutput():
    ''' Utiliza el programa ip para encontrar la informacion del gateway
        de la red local.
    '''

    # Obtenemos el resultado de correr "ip route"
    devnull = open('/dev/null', 'w')
    ip_proc = subprocess.Popen(['ip','route'], stdout=subprocess.PIPE, stderr=devnull)
    output = ip_proc.stdout.read()
    ip_proc.stdout.close()
    exitcode = ip_proc.wait()
    devnull.close()

    return output

def getNetworkInfo():
    ''' Devuelve la informacion de red de la configuracion actual. '''

    output1 = _getIfconfigOutput()
    output2 = _getIpRouteOutput()

    # Extraemos la informacion de red de las interfaces activas.
    p1 = r'[0-9A-Fa-f][0-9A-Fa-f]'
    p2 = r'([1-2][0-9][0-9]|[1-9][0-9]|[0-9])'
    p3 = '([a-z0-9]+)(\s+Link encap:)([a-zA-Z]+)(\s+HWaddr\s+)({0}\:{0}\:{0}\:{0}\:{0}\:{0})(\s+inet\s+addr:)({1}\.{1}\.{1}\.{1})(\s+Bcast:)({1}\.{1}\.{1}\.{1})(\s+Mask:)({1}\.{1}\.{1}\.{1})'.format(p1, p2)
    netinfo = re.findall(p3, output1)

    # Extraemos la direccion del gateway.
    p4 = r'(default\s+via\s+)({0}\.{0}\.{0}\.{0})'.format(p2)
    routeinfo = re.findall(p4, output2) 

    if len(netinfo) > 0:
        interface = netinfo[0][0]
        address = netinfo[0][6]
        broadcast = netinfo[0][12]
        netmask = netinfo[0][18]
        # Calculamos la direccion de red.
        quad1 = (int(q) for q in address.split('.'))
        quad2 = (int(q) for q in netmask.split('.'))
        network = '.'.join((str(q1 & q2) for q1,q2 in zip(quad1,quad2)))
        gateway = None
        if len(routeinfo) > 0:
            gateway = routeinfo[0][1]
        return (interface, address, network, broadcast, netmask, gateway)
    else:
        return (None, None, None, None, None)

def getMacAddresses():
    ''' Utiliza el programa ifconfig para encontrar las direcciones fisicas
        de las interfaces de red.
    '''

    output = _getIfconfigOutput()

    # Extraemos las direcciones MAC.
    p1 = r'[0-9A-Fa-f][0-9A-Fa-f]'
    p2 = '([a-z0-9]+)(\s+)(Link encap:)([a-zA-Z]+)(\s+)(HWaddr)(\s+)({0}\:{0}\:{0}\:{0}\:{0}\:{0})'.format(p1)
    macinfo = re.findall(p2, output)

    if len(macinfo) > 0:
        # [(name, description, mac)]
        return tuple((m[0], m[3], m[7]) for m in macinfo)
    else:
        return (None, None, None)

def readConfig(configFilePath):
    ''' Retorna un diccionario con el contenido del archivo de configuracion
        config.txt, donde cada linea tiene la forma VARIABLE=VALOR.
    '''

    config = {}
 
    with open(configFilePath, 'r') as f:
        for line in f.readlines():
            try:
                k,v = line.strip(' ').rstrip('\n').split('=')
                if '#' != k[0]: # ignoramos comentarios
                    try:
                        config[k] = int(v)
                    except ValueError:
                        if "'" == v[0] and "'" == v[-1]:
                            config[k] = v[1:-1]
                        elif 'true' == v.lower():
                            config[k] = True
                        elif 'false' == v.lower():
                            config[k] = False
                        elif 'none' == v.lower():
                            config[k] = None
                        else:
                            config[k] = v
            except ValueError:
                pass # ignoramos lineas corruptas o comentarios
        f.close()

    return config

def writeConfig(config, configFilePath):
    ''' Escribe una configuracion al archivo config.txt. '''

    with open(configFilePath, 'w') as f:
        for k,v in config.items():
            f.write('{0}={1}\n'.format(k,v))
        f.close()
