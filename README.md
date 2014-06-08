#Proyecto TCU-TC629-AZ

##Introducción
En este proyecto se exploró la viabilidad de desarrollar un sistema automático para el control de pesos en una línea de producción (de una PYMe de la industria alimenticia) utilizando un presupuesto limitado. Un sistema de esta naturaleza debe poder utilizarse con diferentes productos cada uno con un rango de pesos aceptables, debe indicarle al operario mediante luces si se acepta o rechaza el producto, y debe registrar los pesos de los productos con pesos válidos.

##Descripción de la solución

###El diseño en general
Se contaba con un Arduino UNO y un pcDuino para este proyecto. Se decidió dedicar el Arduino a la lectura de las celdas de carga y el pcDuino al resto de la funcionalidad (almacenamiento de los datos, interfaz Web, script de actualización,...).
Ambos dispositivos se comunican utilizando serial vía USB, lo que tiene las siguientes ventajas:

- se aprovecha el mecanismo de subida de programas original del Arduino IDE (bootloader + avrdude) para implementar la funcionalidad de actualización
- el Arduino se reinicia cuando lo hace el pcDuino

Como la interfaz es Web, el pcDuino utiliza una LCD serial para comunicar la dirección ip y el puerto (por defecto el 80) a donde esta escuchando el servidor. Se hace uso de WebSockets para mostrar las últimas mediciones que se han tomado, y para implementar la interacción que permite la generación y descarga de documentos CSV con los datos de un producto.
La funcionalidad de actualización está inspirada en las de los *routers* caseros, a los que se debe subir un tarball con la actualización. Hay un init script (en Python) que se encarga de revisar por estos tarballs en un directorio específico, y si existe alguno procede con la actualización. El tarball puede incluir un hexfile para el Arduino, que se *flashea* al Arduino utilizando *avrdude*. Cuando el usuario sube un nuevo tarball, el pcDuino se reinicia y se corre el init script de actualización.
La comunicación serial sigue un protocolo sencillo que consta de comandos compuestos por un código y un argumento opcional, este se describe a continuación.

###Comunicación serial
El código de Arduino implementa una máquina de estados que se encarga de parsear los comandos recibidos. Cada vez que se reconoce un comando se almacena en un buffer (máximo 10) que es accesado a manera de cola.
Los comandos son de la forma <code;arg>:

- <0;*pesoMin*> : utilizar nuevo peso mínimo (también modifica la EEPROM)
- <1;*pesoMax*> : utilizar nuevo peso máximo (también modifica la EEPROM)
- <2;>        : reanudar lecturas
- <3;>        : pausar lecturas
- <4;>        : ping (para probar conexión serial)

Todos los comandos anteriores son respondidos con un *ack*, salvo último, que se responde con *pong*.
En el proceso de desarrollo, se utilizó un *push button* para forzar un *halt* del Arduino (escapar el loop principal). Esto fué necesario porque problemas con la comunicación serial pudieron haber ocasionado que el *bootloader* no respondiera para subir otro programa.
El Arduino indica cuando está listo para recibir comandos con ````ready\n````.
Cada vez que se registra un peso dentro del rango especificado, el Arduino envía un ````*idBalanza*;*peso*\n```` para indicar el peso y la balanza que lo registró.

###La celda de carga
Como se hizo difícil conseguir una celda de carga para esta aplicación a un precio accesible, se consiguió una romana sencilla, marca WeightMax, de la que se extrajeron todos los componentes menos la celda de carga; con la ventaja adicional de contar con un soporte diseñado para esa celda de carga.
La celda de esa romana es de 4 pares, que se codifican (según la PCB) como:

- rojo: exitación positiva
- blanco: señal negativa
- verde: señal positiva
- negro: exitación negativa

###Leyendo la celda de carga
Inicialmente se intentó utilizar un circuito amplificador para leer la celda de carga. Sin embargo, no se pudo implementar correctamente y aunque hubiera funcionado, existía la limitante de que los ADCs del Arduino son de 10bits (lo que afectaría en la resolución de las lecturas).
Luego se consiguió un ADC de 24bits por separado, que era de montaje superficial. La idea era implementar el circuito que se recomendaba en la *datasheet* del mismo. Sin embargo, a la hora de hacer pruebas, las lecturas reportadas eran siempre la misma.
Finalmente, se optó por un *breakout board* de Adafruit que implementa un circuito para utilizar el ADC ADS1115, con la limitante de que su ADC es de solo 16bits.

###Mapeando las mediciones a pesos

La celda de carga es una función lineal creciente. Para aproximarla, se tomaron varias muestras de pesos conocidos (se utilizó otra balanza ya calibrada para obtenerlos) y se utilizó *numpy* para hacer el ajuste de la curva.
A continuación se muestra el uso de *numpy* para hacer este ajuste y se muestra un gráfico que compara las muestras contra la curva estimada.

```sh
sudo make install python-numpy
sudo make install python-matplotlib
```

```python
import numpy as np
import matplotlib.pyplot as plt

x = [26.0, 27.0, 28.0, 35.0, 37.0, 44.0, 47.0, 54.0, 57.0, 64.0, 72.0, 79.0, 90.0, 99.0, 102.0]
y = [0.0, 0.0, 0.0, 38.0, 51.0, 89.0, 102.0, 140.0, 150.0, 188.0, 230.0, 268.0, 319.0, 370.0, 380.0]

a,b = np.polyfit(x,y,1)
f = np.poly1d(np.polyfit(x,y,1))

xf = np.linspace(min(x), max(x)+20.0)
plt.plot(x,y,'.',xf,f(xf),'-')
plt.ylim(min(y), max(y)+20.0)
plt.ylabel('Peso estimado')
plt.xlabel('Lectura ADC')
plt.grid(True)
plt.title('f(x) = {0} * x + {1}'.format(a,b))

plt.show()

```

###Limitaciones
- Precisión de las lecturas de la celda de carga: se utiliza un ADC de 16bits.
- Limite en el número de celdas de carga: hasta 8 utilizando el diseño actual.
- Capacidad del microprocesador: actualmente se utiliza un Arduino UNO y se utiliza un 88% del almacenamiento disponible. Podría considerarse utilizar un Arduino Mega si se requiere extender la funcionalidad.
- Falta de un reloj de tiempo real: actualmente se configuró un cliente de NTP para sincronizar el tiempo con un reloj externo, sin embargo esto requiere de una conexión a Internet. Lo ideal sería complementarlo con un RTC I2C y un init script que corra antes del que inicia el cliente de NTP. Por ejemplo con el [BOB0099](https://www.sparkfun.com/products/99) de *Sparkfun*, o preferiblemente, uno resistente a los cambios de temperatura. Se hizo pruebas con un BOB0099 pero no fué posible ponerlo en marcha.
- El producto es apenas un prototipo de lo que podría llegar a ser un dispositivo de esta naturaleza, y por eso las conexiones y el ensamble de los componentes es muy artesanal.

###Conclusión
Se logró probar que es viable realizar un dispositivo para esta aplicación utilizando componentes accesibles, y utilizando tecnología *open source* y *open hardware*. Sin embargo, para poder hacer uso del dispositivo en un ambiente real, es necesario mejorar muchos aspectos; entre los que destacan la resolución de las lecturas de las celdas de carga y la calibración de las balanzas.
Una alternativa sería utilizar el software que corre en el pcDuino y adaptarlo para que funcione con balanzas profesionales que se comuniquen utilizando RS-232, pero habría que utilizar una alternativa al pcDuino que tenga tantos puertos seriales como balanzas se ocupen.

##Lista de materiales

##Dependencias
Libra utiliza las siguientes dependencias. Por comodidad algunas se incluyen en el repositorio y para otras se incluye un *script* para descargarlas e instalarlas. Por favor refiérase a los sitios oficiales para ver las licencias de cada una.

###Aplicación en Python
- [Autobahn](http://github.com/tavendo/AutobahnPython)
- [Flask](http://flask.pocoo.org/)
- [Jinja2](http://jinja.pocoo.org/)
- [Twisted](http://twistedmatrix.com/trac/)
- [Werkzeug](http://werkzeug.pocoo.org/)

###Aplicación de Arduino
- [Bibliotecas de Arduino (ArduinoCore, ArduinoVariant, EEPROM, Wire)](http://www.arduino.cc/)

###Construcción del rootfs
- [Buildroot](http://buildroot.uclibc.org/)
- [Crosstool-NG](http://crosstool-ng.org/)

##Preparando el ambiente de desarrollo

Es necesario contar con una computadora que utilice Linux,
se recomienda alguna versión reciente de Ubuntu. 
Se probó con las siguientes versiones:
- 13.10 x86-64
- 14.04 x86-64

###Instalar pre-requisitos

Corra los siguientes comandos para instalar algunos paquetes necesarios.
````
sudo su
apt-get install git subversion mercurial
apt-get install bison flex
apt-get install build-essential automake
apt-get install libncurses5-dev
apt-get install unzip
apt-get install libusb-1.0-0-dev
apt-get install avrdude binutils-avr avr-libc gcc-avr
apt-get install python-virtualenv
apt-get install python-dev
apt-get install u-boot-tools
apt-get install libffi-dev
apt-get install screen
exit 
````

###Correr scripts

Haga *"utils/"* su directorio de trabajo y corra los siguientes comandos.
Revise los archivos para más información de lo que sucede en este paso.

````
./clone-repos.sh
./build-ctng.sh
./build-arm-toolchain.sh
./build-buildroot.sh
./build-pythonvirtualenv.sh
````

###Construir las herramientas de Sunxi
Haga *"utils/sunxi-tools/"* su directorio de trabajo y corra los siguientes comandos.

````
make
````

###Permitir que el usuario utilice puertos seriales
Debido a que se utiliza un puerto serial para acceder a la consola del pcduino, el usuario debe tener permisos para ello.
Esto se logra agregando el usuario al grupo *dialout*, como se muestra a continuación.

````
sudo adduser `whoami` dialout
````

##Accediendo el pcDuino desde la máquina de trabajo.
Se utiliza un cable USB-serial (3.3V) para comunicarse con el pcDuino desde la máquina de trabajo, en particular se recomienda [este cable que ofrece Olimex](https://www.olimex.com/Products/Components/Cables/USB-Serial-Cable/USB-Serial-Cable-F).
El cable esta configurado de la siguiente manera:

- azul = tierra
- verde = rx
- rojo = tx

Los pines del pcDuino a utilizar son los identificados como J5, refierase al *pinout* para identificarlos. Recuerde que debe conectar el rx del cable con el tx del pcDuino, el tx del cable con el rx del pcDuino y conectar las tierras.
Asumiendo que el cable es el único dispositivo USB-serial conectado a la máquina de desarrollo, ejecute el siguiente comando para iniciar la comunicación.

````
screen /dev/ttyUSB0 115200
````

##Uso del *Makefile*

Se provee un *Makefile* para asistir el proceso de desarrollo de la aplicación, a continuación se describen algunos de los comandos.
Ejecute ```make help``` para obtener información de referencia más reciente.

| Comando | Descripción |
| :-----: | :---------: |
| make build-tarball | Crear el tarball de actualización omitiendo el código de Arduino. |
| make build-tarball-with-hex | Crear el tarball de actualización incluyendo el código de Arduino. |
| make build-db | Genera el archivo de la base de datos. |
| make build-hex | Compila el código de Arduino. |
| make build-rootfs-additions | Genera los archivos adicionales del rootfs. |
| make clean | Limpia los archivos generados. |
| make clean-all | Limpia todos los archivos generados. |
| make flash-hex | Sube el código al Arduino. |
| make help | Muestra un mensaje de ayuda para utilizar el Makefile. |
| make install | Instala la aplicación en la computadora de desarrollo. |
| make print-hexsize | Muestra el tamaño total en bytes del código de Arduino. |
| make update | Simula una actualización en la computadora de desarrollo. |

##Probando la aplicación
Es importante poder correr la aplicación desde la máquina de desarrollo (para agilizar el proceso). El *Makefile* provee facilidades para esto. Instale la aplicación localmente haciendo ```make install```, este paso requiere que tenga privilegios para ejecutar el comando *sudo*. La aplicación se instalará en los directorios */var/libra* y /opt/libra*. Ejecute la aplicación haciendo ```/opt/libra/libra```, la aplicación estará disponible en el puerto 8080.

##Utilizando *Buildroot*
En esta sección se explica como utilizar Buildroot para crear las imagenes que se instalaran en la tarjeta SD. Lo primero que debe hacer es crear (o re-generar) el directorio *rootfs-additions*. Esto se hace ejecutando ````make build-rootfs-additions````.
Luego haga *utils/buildroot/* su directorio de trabajo y ejecute ```make```. Después de completado el proceso de construcción, encontrará los archivos necesarios para crear la tarjeta SD en el directorio *utils/buildroot/output/images*.

##Creando una tarjeta SD con la aplicación

En esta sección se explica el proceso de creación de una tarjeta SD. Se asume que la computadora a utilizar tiene lector de memorias SD.
Si se utiliza un lector externo (USB) los pasos son los mismos pero deberá sustituir los nombres */dev/mmcblk* con alguno de la forma */dev/sd*. También se asume que la tarjeta SD tiene una capacidad de 8GB. Si utiliza alguna con capacidad distinta, solo debe cambiar el paso
7.13, de manera que quede espacio de 512MB para una partición *SWAP*. Se recomienda que la tarjeta sea de al menos 4GB y que sea **SDHC**.

###Layout de la tarjeta
| Sector | Start | Size | Use                                                 |
| -----: | ----: | ---: | :-------------------------------------------------- |
|   0    |0      |8KB   | Unused, available for partition table etc.          |
|  16    |8      |32KB  | Initial SPL loader                                  |
|  80    |40     |504KB | u-boot  (sector 64 / 32KB for 2013.07 and earlier)  |
|1088    |544    |128KB | environment                                         |
|1344    |672    |128KB | Falcon mode boot params                             |
|1600    |800    |  -   | Falcon mode kernel start                            |
|2048    |1024   |  -   | Free for partitions (higher if using Falcon boot)   |

**Tomado de:** [*Storage Map, U-Boot-Sunxi Wiki*](https://github.com/linux-sunxi/u-boot-sunxi/wiki)

###Instrucciones
1. Haga *"utils/buildroot/output/images"* su directorio de trabajo.

2. Ejecute:
    ````
        sudo su
    ````

3. Ejecute:
    ````
        dd if=/dev/zero of=/dev/mmcblk0 bs=1024 count=32768
    ````

4. Ejecute:
    ````
        dd if=sunxi-spl.bin of=/dev/mmcblk0 bs=1024 seek=8
    ````

5. Ejecute:
    ````
        dd if=u-boot.img of=/dev/mmcblk0 bs=1024 seek=40
    ````

6. Ejecute:
    ````
        fdisk /dev/mmcblk0
    ````

7. Utilizando la consola de *fdisk* haga:
    - 7.1.  **n**
    - 7.2.  **p**
    - 7.3.  **1**
    - 7.4.  **[enter]**
    - 7.5.  **+32M**
    - 7.6.  **t**
    - 7.7.  **1**
    - 7.8.  **83**
    - 7.9.  **n**
    - 7.10. **p**
    - 7.11. **2**
    - 7.12. **[enter]**
    - 7.13. **+7134M**
    - 7.14. **t**
    - 7.15. **2**
    - 7.16. **83**
    - 7.17. **n**
    - 7.18. **p**
    - 7.18. **3**
    - 7.19. **[enter]**
    - 7.20. **[enter]**
    - 7.21. **t**
    - 7.22. **3**
    - 7.23. **82**
    - 7.24. **w**

8. Ejecute:
    ````
        mkfs.ext2 /dev/mmcblk0p1
        mkfs.ext4 /dev/mmcblk0p2
    ````

9. Ejecute:
    ````
        mount /dev/mmcblk0p1 /mnt
    ````

10. Ejecute:
    ````
        cp uImage /mnt
        cp script.bin /mnt
        cp boot.src /mnt
        sync
    ````

11. Ejecute:
    ````
        umount /mnt
    ````

12. Ejecute:
    ````
        mount /dev/mmcblk0p2 /mnt
    ````

13. Ejecute:
    ````
        tar -C /mnt -xjpf rootfs.tar.bz2
        sync
    ````

14. Ejecute:
    ````
        umount /mnt
    ````

15. Ejecute:
    ````
        exit
    ````

###Credenciales por defecto

####Linux
- usuario: root
- password: foobar

####Aplicación web
- usuario: administrador
- password: foobar

Se recomienda, por supuesto, utilizar valores diferentes a los provistos por defecto.

##Acerca del proyecto
Este trabajo es financiado e implementado bajo el programa [TC-629 (Aplicación de soluciones automatizadas o robóticas en MiPYMEs)](http://tcu.ucr.ac.cr/web/tcu).

###Período 2013
**Profesores coordinadores del TCU:**
- Eldon Caldwell ([Escuela de Ing. Industrial](http://eii.ucr.ac.cr/))
- Mauricio Zamora ([Escuela de Ing. Industrial](http://eii.ucr.ac.cr/))

**Estudiantes del TCU:** 
- Jeffrey Alfaro ([Escuela de Ing. Industrial](http://eii.ucr.ac.cr/))
- Adolfo García ([Escuela de Computación](ecci.ucr.ac.cr))
- Daniel González ([Escuela de Ing. Industrial](http://eii.ucr.ac.cr/))
- Gustavo Montoya ([Escuela de Ing. Eléctrica](http://eie.ucr.ac.cr/))
- Gisella Vallejos ([Escuela de Ing. Industrial](http://eii.ucr.ac.cr/))

Se agracede también al estudiante Roberto Aguilar ([Escuela de Computación](ecci.ucr.ac.cr)) por la colaboración brindada al proyecto.

##Referencias
En esta sección se listan fuentes de información que se han consultado en el proceso de desarrollo, las mismas se dividen por tema.

###ADC
- [A guide to the ADS1115 and ADS1015 analog converters](https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/programming)

###Buildroot
- [The Buildroot user manual](http://buildroot.uclibc.org/downloads/manual/manual.html)
- [Using Buildroot for real projects](http://elinux.org/images/2/2a/Using-buildroot-real-project.pdf)

###Crosstool-NG
- [CrosstoolNG - Linaro Wiki](https://wiki.linaro.org/WorkingGroups/ToolChain/Using/CrosstoolNg) 
- [CroostoolNG Download and Usage](http://crosstool-ng.org/#download_and_usage)

###Miscelaneas
- [a13-olinuxino Buildroot configuration](http://code.google.com/p/a13-olinuxino/wiki/BuildRootConfig)
- [Add a real time clock (RTC) to pcDuino](http://www.pcduino.com/add-an-real-time-clock-rtc-to-pcduino)
- [Arduino load cell](http://www.instructables.com/id/Arduino-Load-Cell-Scale/?ALLSTEPS)
- [Creating a bootable SD card for the pcDuino - pcduino.com](http://pcduino.com/forum/index.php?topic=3642.0)
- [MDev Primer](http://svn.mcs.anl.gov/repos/ZeptoOS/trunk/BGP/packages/busybox/src/docs/mdev.txt)
- [numpy.polyfit](http://docs.scipy.org/doc/numpy/reference/generated/numpy.polyfit.html)
- [Pyplot tutorial](http://matplotlib.org/users/pyplot_tutorial.html)
- [The Linux BootPrompt HowTo](http://www.tldp.org/HOWTO/BootPrompt-HOWTO-3.html)

###Python Twisted
- [The Twisted Documentation](http://twistedmatrix.com/documents/current/core/howto/book.pdf)
- [Using processes](http://twistedmatrix.com/documents/current/core/howto/process.html)

###U-Boot
- [U-Boot Sunxi](http://linux-sunxi.org/U-Boot)
- [u-boot-sunxi Wiki](http://github.com/linux-sunxi/u-boot-sunxi/wiki)

###pcDuino
- [pcDuino pinout](http://www.robotmaker.ru/wp-content/uploads/2013/09/pcduino-pinout-300x218.jpg)

###Websockets
- [An Introduction To WebSockets](http://www.developerfusion.com/article/143158/an-introduction-to-websockets)
- [Web Socket Introduction](http://autobahn.ws/python/websocketintro.html)
