#Proyecto TCU-TC629-AZ

##Estado
**En desarrollo**
###Pendientes

##Introducción

##Descripción del problema

##Descripción de la solución

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
- [Bibliotecas de Arduino (ArduinoCore, ArduinoVariant)](http://www.arduino.cc/)
- [ChibiOS (versión de Arduino RTOS)](http://code.google.com/p/rtoslibs/) [(*ver licencia*)](http://www.chibios.org/dokuwiki/doku.php?id=chibios:license)

###Construcción del rootfs
- [Buildroot](http://buildroot.uclibc.org/)
- [Crosstool-NG](http://crosstool-ng.org/)

##Preparando el ambiente de desarrollo

Es necesario contar con una computadora que utilice Linux,
se recomienda alguna versión reciente de Ubuntu.
El desarrollo se hizo en una computadora con Ubuntu 13.10 x86-64.

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

##Uso del *Makefile*

Se provee un *Makefile* para asistir el proceso de desarrollo
de la aplicación, a continuación se describen algunos de los comandos.
Ejecute ```make help``` para obtener información de referencia más reciente.

| Comando | Descripción |
| :-----: | :---------: |
| make all| Crea el tarball de actualización completo. |
| make build-tarball | Crear el tarball de actualización omitiendo el código de Arduino. |
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

##Corriendo la aplicación en la máquina de desarrollo

Para correr la aplicación en la máquina de desarrollo necesita
conectar el Arduino a la misma e instalar la aplicación utilizando *make*.
Luego nada más ejecute ```/opt/libra/libra```.

##Utilizando *Buildroot*
Es necesario crear (o re-generar) el directorio *rootfs-additions*.
Para ello ejecute ````make build-rootfs-additions````.
Luego haga *utils/buildroot/* su directorio de trabajo.
Ejecute ```make```.
Después de completado el proceso de construcción, encontrará
los archivos necesarios para crear la tarjeta SD en el directorio
*utils/buildroot/output/images*.

##Creando una tarjeta SD con la aplicación

Se asume que la computadora a utilizar tiene lector de memorias SD.
Si se utiliza un lector externo (USB) los pasos son los mismos pero 
debera sustituir los nombres */dev/mmcblk* con alguno de la forma
*/dev/sd*.
Tambien se asume que la tarjeta SD tiene una capacidad de 8GB.
Si utiliza alguna con capacidad distinta, solo debe cambiar el paso
7.13, de manera que quede espacio de 512MB para una particion *SWAP*.
Se recomienda que la tarjeta sea de al menos 4GB y que sea **SDHC**.

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
1. haga *"utils/buildroot/output/images"* su directorio de trabajo.
2. ejecute
    ````
        sudo su
    ````
3. ejecute
    ````
        dd if=/dev/zero of=/dev/mmcblk0 bs=1024 count=32768
    ````
4. ejecute
    ````
        dd if=sunxi-spl.bin of=/dev/mmcblk0 bs=1024 seek=8
    ````
5. ejecute
    ````
        dd if=u-boot.img of=/dev/mmcblk0 bs=1024 seek=40
    ````
6. ejecute
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

8. ejecute
    ````
        mkfs.ext2 /dev/mmcblk0p1
        mkfs.ext4 /dev/mmcblk0p2
    ````

9. ejecute
    ````
        mount /dev/mmcblk0p1 /mnt
    ````

10. ejecute
    ````
        cp uImage /mnt
        cp script.bin /mnt
        cp boot.src /mnt
        sync
    ````

11. ejecute
    ````
        umount /mnt
    ````

12. ejecute
    ````
        mount /dev/mmcblk0p2 /mnt
    ````

13. ejecute
    ````
        tar -C /mnt -xjpf rootfs.tar.bz2
        sync
    ````

14. ejecute
    ````
        umount /mnt
    ````

15. ejecute
    ````
        exit
    ````

##Referencias
En esta sección se listan fuentes de información que han consultado en el proceso de desarrollo, las mismas se dividen por tema.

###Buildroot
- [The Buildroot user manual](http://buildroot.uclibc.org/downloads/manual/manual.html)
- [Using Buildroot for real projects](http://elinux.org/images/2/2a/Using-buildroot-real-project.pdf)

###Crosstool-NG
- [CrosstoolNG - Linaro Wiki](https://wiki.linaro.org/WorkingGroups/ToolChain/Using/CrosstoolNg) 
- [CroostoolNG Download and Usage](http://crosstool-ng.org/#download_and_usage)

###Miscelaneas
- [a13-olinuxino Buildroot configuration](http://code.google.com/p/a13-olinuxino/wiki/BuildRootConfig)
- [Creating a bootable SD card for the pcDuino - pcduino.com](http://pcduino.com/forum/index.php?topic=3642.0)
- [MDev Primer](http://svn.mcs.anl.gov/repos/ZeptoOS/trunk/BGP/packages/busybox/src/docs/mdev.txt)
- [The Linux BootPrompt HowTo](http://www.tldp.org/HOWTO/BootPrompt-HOWTO-3.html)

###Python Twisted
- [The Twisted Documentation](http://twistedmatrix.com/documents/current/core/howto/book.pdf)
- [Using processes](http://twistedmatrix.com/documents/current/core/howto/process.html)

###U-Boot
- [U-Boot Sunxi](http://linux-sunxi.org/U-Boot)
- [u-boot-sunxi Wiki](http://github.com/linux-sunxi/u-boot-sunxi/wiki)
