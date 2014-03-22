#!/usr/bin/python

# Este programa se corre en el pcDuino antes de que se cree e inicie el
# daemon de la aplicacion Libra.
# Revisa si existe el archivo "update_pending", el mismo consiste en una
# unica linea correspondiente al nombre del "tarball" con la actualizacion.
# Por el momento, solo soporta hacer cambios al codigo de la aplicacion
# Python y a la aplicacion de Arduino. No soporta hacer cambios a la base de
# datos.
# Requiere de los programas: avrdude, gunzip/gzip, y tar.

from __future__ import print_function
import os
import subprocess
import shutil

from config import CONFIG
from config import UPDATE_PENDING_PATH
from config import FILES_PATH
from config import APP_PATH

def main():

    # La existencia del archivo "update_pending" indica que
    # hay una actualizacion pendiente.
    if os.path.exists(UPDATE_PENDING_PATH) and os.path.isfile(UPDATE_PENDING_PATH):
        print('Se encontro una actualizacion pendiente.')
        with open(UPDATE_PENDING_PATH, 'r') as update_pending:
            # Analizamos que exista el archivo con la actualizacion
            tarball = update_pending.readline().rstrip('\n').lstrip(' ').rstrip(' ')
            tarball = os.path.join(FILES_PATH, 'updates/'+tarball)
            print('Analizando archivo: ', end=' ')
            if os.path.exists(tarball) and os.path.isfile(tarball):
                print('OK')
                # Y si existe lo descomprimimos.
                print('Descomprimiendo archivo: ', end=' ')
                if untar(tarball):
                    print('OK')
                    new_dir = os.path.join('/opt',tarball.rstrip('.tar.gz').split('/')[-1])
                    # Revisamos si hay que actualizar el codigo en el Arduino.
                    arduino_dir = os.path.join(new_dir, 'arduino')
                    if os.path.exists(arduino_dir) and not os.path.isfile(arduino_dir):
                        print('Actualizando AVR: ', end=' ')
                        config_file = os.path.join(arduino_dir, 'avrdude_config')
                        if os.path.exists(config_file) and os.path.isfile(config_file):
                            with open(config_file, 'r') as config:
                                # Leemos la configuracion
                                avrdude_config = {}
                                for line in config.readlines():
                                    k,v = line.split('=')
                                    if 'hex' == k:
                                        v = '{0}/arduino/{1}'.format(new_dir, v)
                                    avrdude_config[k] = v.rstrip('\n')
                                # Actualizamos el Arduino.
                                if update_avr(avrdude_config):
                                    print('OK')
                                    update_symlink(new_dir, tarball)
                                else:
                                    print('FALLIDO')
                                    return
                        else:
                            print('FALLIDO')
                            return
                    else:
                        # No se requiere actualizar el codigo en el Arduino.
                        update_symlink(new_dir, tarball)
                else:
                    print('FALLIDO')
                    return
            else:
                print('FALLIDO')
                return
    else:
        print('No se encontro una actualizacion pendiente.')

def update_symlink(new_dir, tarball):
    ''' Actualiza el symlink para que apunte al directorio de la nueva version. '''

    print('Actualizando symlink: ', end=' ')

    # Obtenemos el directorio anterior.
    old_dir = os.path.realpath(APP_PATH)

    try:
        os.remove(APP_PATH)
        os.symlink(new_dir, APP_PATH)
    except OSError as e:
        # Fallo, intentamos volver al directorio anterior.
        try:
            os.symlink(old_dir, APP_PATH)
        except OSError:
            print('FALLO NO RECUPERABLE')
        else:    
            print('FALLO SIN ACTUALIZAR')
    else:
        # Exito, entonces borramos el directorio anterior.
        try:
            shutil.rmtree(old_dir)
        except Exception:
            print('FALLO AL REMOVER VERSION ANTERIOR')
        else:
            print('OK')
            # Remover el tarball
            try:
                print('Finalizando actualizacion: ', end=' ')
                os.remove(tarball)
                os.remove(UPDATE_PENDING_PATH)
                print('OK')
            except OSError:
                print('FALLIDO')

def update_avr(config):
    ''' Actualiza la memoria del Arduino utilizando la herramienta avrdude,
        la misma que utiliza el IDLE de Arduino. Requiere que el Arduino este
        conectado por USB (no via serial utilizando los pines).
    '''

    partno = config['partno']
    programmer = config['programmer']
    port = CONFIG['ARDUINO_PORT']
    speed = config['speed']
    filename = config['hex']

    devnull = open(os.devnull, 'w')
    avrdude_proc = subprocess.Popen(['avrdude','-p',partno,'-c',programmer,
        '-P', port, '-b', speed, '-Uflash:w:{0}:i'.format(filename)], stdout=devnull, stderr=devnull)
    exitcode = avrdude_proc.wait()
    devnull.close()

    return exitcode == 0

def untar(tarball):
    ''' Utiliza los programas "gunzip" y "tar" para descomprimir el 
        tarball de la actualizacion.
    '''

    # Aqui se utilizan "pipes" para pegar el output de gunzip al input de tar, el bash equivalente seria
    # algo como: gunzip -cdf <tarball> | tar -C /opt -xp
    devnull = open(os.devnull, 'w')
    gunzip_proc = subprocess.Popen(['gunzip', '-cdf', tarball], stdout=subprocess.PIPE, stderr=devnull)
    tar_proc = subprocess.Popen(['tar', '-C', '/opt', '-xp'], stdin=gunzip_proc.stdout ,stdout=devnull)
    gunzip_proc.stdout.close()
    exitcode_gunzip = gunzip_proc.wait()
    exitcode_tar = tar_proc.wait()
    devnull.close()

    return exitcode_tar == 0 and exitcode_gunzip == 0

if __name__ == '__main__':
    main()
