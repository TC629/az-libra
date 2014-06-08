# Makefile
# Este programa se utiliza para asistir el desarrollo de la aplicacion.
#
# El tarball puede contener solo la aplicacion escrita en Python
# o tambien puede incluir los archivos .eep y .hex que requiere
# avrdude para flashear el Arduino.
# Este tarball sirve para realizar una actualizacion desde 
# "update.py".

# Para entender como se crean el .eep y el .hex:
# * Consulte http://arduino.cc/en/Hacking/BuildProcess
# * Consulte el documento boards.txt de 
#	http://arduino.googlecode.com/files/arduino-1.0.5-linux64.tgz
# * Analice el output del Arduino IDE, para ello elija las opciones
#	"compilation" y "upload" al lado de "Show verbose output during:"
#	en el panel de preferencias.

# Las configuraciones se manejan en Config.mk
# Los parametros ahi definidos son los que pueden variar
# entre ambientes de desarrollo.
include Config.mk

# Configuracion del tarball
# Se asume que el tarball se creara desde un repositorio de Git.
VERSION = $(shell git describe --always --tag)
DIR = libra-$(VERSION)
TARBALL = $(DIR).tar.gz
INCLUDE_EEP = False

# Estas variables se utilizan para instalar la aplicacion en la computadora
# de desarrollo. Por defecto se llama libra0, para poder probar el script de
# actualizacion "update.py".
APP_FILES_PATH = /var/libra
APP_PATH = /opt/libra0
APP_SYMLINK = /opt/libra

# La instalacion local se crea con permisos para el usuario que esta ejecutando
# este Makefile (usuario del desarrollador).
USER = $(shell whoami)

# Archivo donde generar la base de datos.
DB = libra.sqlite3

# Archivo de configuracion de Libra.
LIBRA_CONFIG_FILE = config.txt

# No confundir el siguiente archivo con el archivo "avrdude.conf".
# Este es un archivo que se genera para "update.py" no para "avrdude".
AVRDUDE_CONFIG_FILE = avrdude_config

# Configuracion del codigo objeto para Arduino
HEXFILE = $(ARDUINO_DIR)/libra.hex
ELFFILE = $(ARDUINO_DIR)/libra.elf
EEPFILE = $(ARDUINO_DIR)/libra.eep
CORELIB = $(ARDUINO_DIR)/core.a

# Herramientas de la toolchain para AVR
AR = avr-ar
CC = avr-gcc
CXX = avr-g++
OBJCOPY = avr-objcopy
OBJDUMP = avr-objdump
SIZE = avr-size

AVRDUDE = avrdude

# Directorios de codigo fuente
ARDUINO_DIR = ArduinoApp
ARDUINO_CORE_DIR = $(ARDUINO_DIR)/ArduinoCore
ARDUINO_VARIANT_DIR = $(ARDUINO_DIR)/ArduinoVariant/$(ARDUINO_VARIANT)
AVRLIBC_DIR = $(ARDUINO_CORE_DIR)/avr-libc
EEPROM_DIR = $(ARDUINO_DIR)/EEPROM
WIRE_DIR = $(ARDUINO_DIR)/Wire
WIRE_TWI_DIR = $(WIRE_DIR)/utility
ADAFRUIT_DIR = $(ARDUINO_DIR)/Adafruit_ADS1X15

#CHIBIOS_DIR = $(ARDUINO_DIR)/ChibiOS
#CHIBIOS_UTIL_DIR = $(ARDUINO_DIR)/ChibiOS/utility

# Archivos de codigo fuente y codigo objeto
ARDUINO_CORE_FILES = wiring_pulse.c WInterrupts.c wiring_digital.c wiring_shift.c wiring_analog.c wiring.c \
Stream.cpp USBCore.cpp HardwareSerial.cpp new.cpp HID.cpp IPAddress.cpp Tone.cpp CDC.cpp WString.cpp Print.cpp WMath.cpp 
ARDUINO_CORE_SRC = $(addprefix $(ARDUINO_CORE_DIR)/, $(ARDUINO_CORE_FILES))
ARDUINO_CORE_OBJ_0 = $(ARDUINO_CORE_SRC:.c=.o)
ARDUINO_CORE_OBJ = $(ARDUINO_CORE_OBJ_0:.cpp=.o)

AVRLIBC_FILES = malloc.c realloc.c
AVRLIBC_SRC = $(addprefix $(AVRLIBC_DIR)/, $(AVRLIBC_FILES))
AVRLIBC_OBJ = $(AVRLIBC_SRC:.c=.o)

EEPROM_FILES = EEPROM.cpp
EEPROM_SRC = $(addprefix $(EEPROM_DIR)/, $(EEPROM_FILES))
EEPROM_OBJ = $(EEPROM_SRC:.cpp=.o)

WIRE_FILES = Wire.cpp
WIRE_SRC = $(addprefix $(WIRE_DIR)/, $(WIRE_FILES))
WIRE_OBJ = $(WIRE_SRC:.cpp=.o)

WIRE_TWI_FILES = twi.c
WIRE_TWI_SRC = $(addprefix $(WIRE_TWI_DIR)/, $(WIRE_TWI_FILES))
WIRE_TWI_OBJ = $(WIRE_TWI_SRC:.c=.o)

ADAFRUIT_FILES = Adafruit_ADS1015.cpp
ADAFRUIT_SRC = $(addprefix $(ADAFRUIT_DIR)/, $(ADAFRUIT_FILES))
ADAFRUIT_OBJ = $(ADAFRUIT_SRC:.cpp=.o)

#CHIBIOS_FILES = ChibiOS_AVR.c
#CHIBIOS_SRC = $(addprefix $(CHIBIOS_DIR)/, $(CHIBIOS_FILES))
#CHIBIOS_OBJ = $(CHIBIOS_SRC:.c=.o)

#CHIBIOS_UTIL_FILES = board.c chlists.c chcond.c chmempools.c chmemcore.c chschd.c chmsg.c chvt.c chsys.c chsem.c \
chregistry.c chqueues.c chdynamic.c chmtx.c chdebug.c chcore.c chheap.c chevents.c chmboxes.c hal.c chthreads.c 
#CHIBIOS_UTIL_SRC = $(addprefix $(CHIBIOS_UTIL_DIR)/, $(CHIBIOS_UTIL_FILES))
#CHIBIOS_UTIL_OBJ = $(CHIBIOS_UTIL_SRC:.c=.o)

LIBRA_FILES = libra.cpp serialsm.cpp
LIBRA_SRC = $(addprefix $(ARDUINO_DIR)/, $(LIBRA_FILES))
LIBRA_OBJ = $(LIBRA_SRC:.cpp=.o)

CORE_OBJ = $(ARDUINO_CORE_OBJ) $(AVRLIBC_OBJ) 
APP_OBJ = $(WIRE_TWI_OBJ) $(WIRE_OBJ) $(EEPROM_OBJ) $(ADAFRUIT_OBJ) $(LIBRA_OBJ)

# Banderas de GCC.
INC = \
-I$(ARDUINO_CORE_DIR) \
-I$(ARDUINO_VARIANT_DIR) \
-I$(ARDUINO_DIR) \
-I$(EEPROM_DIR) \
-I$(WIRE_TWI_DIR) \
-I$(WIRE_DIR) \
-I$(ADAFRUIT_DIR)

#-I$(CHIBIOS_DIR) \
#-I$(CHIBIOS_UTIL_DIR) \


FLAGS = -ffunction-sections -fdata-sections -mmcu=$(GCC_MCU) -DF_CPU=16000000L -MMD -DUSB_VID=null -DUSB_PID=null \
-DARDUINO=105 $(INC)
CFLAGS = -Os -Wall $(FLAGS)
XFLAGS = -Os -Wall -fno-exceptions $(FLAGS)

# Reglas de compilacion del codigo para Arduino.
%.o : %.c
	$(CC) -c $(CFLAGS) $< -o $@

%.o : %.cpp
	$(CXX) -c $(XFLAGS) $< -o $@

# Variables para configuracion de rootfs-additions-gen
ROOTFS_ADDITIONS_BASE = rootfs-additions-base
ROOTFS_ADDITIONS_GEN = rootfs-additions

# Regla por defecto: mostrar ayuda.
all: help

# Dependencias del codigo objeto.
$(AVRLIBC_OBJ) : $(AVRLIBC_SRC)

$(ARDUINO_CORE_OBJ) : $(ARDUINO_CORE_SRC)

$(EEPROM_OBJ) : $(EEPROM_SRC)

$(WIRE_TWI_OBJ) : $(WIRE_TWI_SRC)

$(WIRE_OBJ) : $(WIRE_SRC)

$(ADAFRUIT_OBJ) : $(ADAFRUIT_SRC)

#$(CHIBIOS_OBJ): $(CHIBIOS_SRC)

#$(CHIBIOS_UTIL_OBJ): $(CHIBIOS_UTIL_SRC)

$(LIBRA_OBJ) : $(LIBRA_SRC)

# Regla para crear la libreria de Arduino.
$(CORELIB) : $(CORE_OBJ)
	$(AR) rcs $(CORELIB) $^

# Regla para crear el ELF.
$(ELFFILE) : $(APP_OBJ) $(CORELIB)
	$(CC) -Os -Wl,--gc-sections,--relax -mmcu=$(GCC_MCU) -o $@ $^ -L$(ARDUINO_DIR) -lm

# Regla para crear el EEP.
$(EEPFILE) : $(ELFFILE)
	$(OBJCOPY) -O ihex -j .eeprom --set-section-flags=.eeprom=alloc,load --no-change-warnings \
--change-section-lma .eeprom=0 $< $@

# Regla para crear el HEX.
$(HEXFILE) : $(ELFFILE) $(EEPFILE)
	$(OBJCOPY) -O ihex -R .eeprom $< $@

# Reglas para la creacion del tarball.
avrdude-config:
	echo partno=$(AVRDUDE_PARTNO) > $(AVRDUDE_CONFIG_FILE)
	echo programmer=$(AVRDUDE_PROGRAMMER) >> $(AVRDUDE_CONFIG_FILE)
	echo port=$(AVRDUDE_PORT) >> $(AVRDUDE_CONFIG_FILE)
	echo speed=$(AVRDUDE_SPEED) >> $(AVRDUDE_CONFIG_FILE)
	echo hex=$(notdir $(HEXFILE)) >> $(AVRDUDE_CONFIG_FILE)
	echo witheep=$(INCLUDE_EEP) >> $(AVRDUDE_CONFIG_FILE)
	echo eep=$(notdir $(EEPFILE)) >> $(AVRDUDE_CONFIG_FILE)

target:
	mkdir -p $(DIR)
	rm -f App/*
	cp -r App/* $(DIR)

target-with-hex: target avrdude-config $(HEXFILE)
	mkdir -p $(DIR)/arduino
	cp $(HEXFILE) $(DIR)/arduino
	cp $(EEPFILE) $(DIR)/arduino
	cp $(AVRDUDE_CONFIG_FILE) $(DIR)/arduino

build-tarball: target
	chmod 755 $(DIR)/libra
	chmod 755 $(DIR)/update.py
	chmod 755 $(DIR)/tocsv
	tar -zcvf $(TARBALL) $(DIR)
	rm -Rf $(DIR)
	echo $(TARBALL) > update_pending

build-tarball-with-hex: target-with-hex
	chmod 755 $(DIR)/libra
	chmod 755 $(DIR)/update.py
	chmod 755 $(DIR)/tocsv
	tar -zcvf $(TARBALL) $(DIR)
	rm -Rf $(DIR)
	echo $(TARBALL) > update_pending

# Simula una actualizacion.
update: build-tarball-with-hex
	cp $(TARBALL) $(APP_FILES_PATH)/updates
	cp update_pending $(APP_FILES_PATH)/updates
	sudo $(APP_SYMLINK)/update.py
	sudo chown -R $(USER):$(USER) $(APP_FILES_PATH)
	sudo chown -R $(USER):$(USER) $(APP_SYMLINK)
	rm update_pending
	rm $(TARBALL)

# Instala la aplicacion para hacer pruebas.
install: build-db
	sudo rm -fr $(APP_PATH)
	sudo rm -fr $(APP_FILES_PATH)
	sudo rm -f $(APP_SYMLINK)
	sudo mkdir -p $(APP_PATH)
	sudo mkdir -p $(APP_FILES_PATH)
	sudo chown -R $(USER):$(USER) $(APP_FILES_PATH)
	sudo chown -R $(USER):$(USER) $(APP_PATH)
	cp -ar App/* $(APP_PATH)
	cp $(DB) $(APP_FILES_PATH)/$(DB)
	cp $(LIBRA_CONFIG_FILE) $(APP_FILES_PATH)/$(LIBRA_CONFIG_FILE)
	mkdir -p $(APP_FILES_PATH)/updates
	sudo ln -sr $(APP_PATH) $(APP_SYMLINK)
	sudo chown $(USER):$(USER) $(APP_SYMLINK)
	chmod 755 $(APP_SYMLINK)/libra
	chmod 755 $(APP_SYMLINK)/update.py
	chmod 664 $(APP_FILES_PATH)/$(DB)

# Genera el directorio rootfs-additions
build-rootfs-additions: $(ROOTFS_ADDITIONS_BASE) build-db
	rm -rf $(ROOTFS_ADDITIONS_GEN)
	mkdir -p $(ROOTFS_ADDITIONS_GEN)
	cp -ar $(ROOTFS_ADDITIONS_BASE)/* $(ROOTFS_ADDITIONS_GEN)
	echo 'network={' >> $(ROOTFS_ADDITIONS_GEN)/etc/wpa_supplicant.conf
	echo ssid=\"$(WPA_SUPPLICANT_SSID)\" >> $(ROOTFS_ADDITIONS_GEN)/etc/wpa_supplicant.conf
	echo psk=\"$(WPA_SUPPLICANT_PSK)\" >> $(ROOTFS_ADDITIONS_GEN)/etc/wpa_supplicant.conf
	echo "}" >> $(ROOTFS_ADDITIONS_GEN)/etc/wpa_supplicant.conf
	# Instala la aplicacion Libra en el rootfs
	mkdir -p $(ROOTFS_ADDITIONS_GEN)$(APP_PATH)
	mkdir -p $(ROOTFS_ADDITIONS_GEN)$(APP_FILES_PATH)
	mkdir -p $(ROOTFS_ADDITIONS_GEN)$(APP_FILES_PATH)/updates
	ln -sr $(ROOTFS_ADDITIONS_GEN)$(APP_PATH) $(ROOTFS_ADDITIONS_GEN)$(APP_SYMLINK)
	cp -ar App/* $(ROOTFS_ADDITIONS_GEN)$(APP_PATH)
	cp $(DB) $(ROOTFS_ADDITIONS_GEN)$(APP_FILES_PATH)
	cp $(LIBRA_CONFIG_FILE) $(ROOTFS_ADDITIONS_GEN)$(APP_FILES_PATH)
	sed -i 's/DEVELOPMENT=True/DEVELOPMENT=False/g' $(ROOTFS_ADDITIONS_GEN)$(APP_FILES_PATH)/config.txt
	sed -i 's/SERVER_PORT=[[:digit:]]*/SERVER_PORT=80/g' $(ROOTFS_ADDITIONS_GEN)$(APP_FILES_PATH)/config.txt
	sed -i 's/NC_WPA_SSID=[a-zA-Z0-9]*/NC_WPA_SSID=$(WPA_SUPPLICANT_SSID)/g' $(ROOTFS_ADDITIONS_GEN)$(APP_FILES_PATH)/config.txt
	sed -i 's/NC_WPA_PSK=[a-zA-Z0-9]*/NC_WPA_PSK=$(WPA_SUPPLICANT_PSK)/g' $(ROOTFS_ADDITIONS_GEN)$(APP_FILES_PATH)/config.txt

# Reglas para desarrollo en Arduino correspondientes a las funciones "Verify" y
# "Upload" del Arduino IDE.

print-hexsize:
	$(eval HEXFILE_SIZE = $(word 1, $(shell wc -c $(HEXFILE))))
	$(eval PERCENTAGE = $(shell python -c "print(float($(HEXFILE_SIZE))/float($(HEXFILE_MAXSIZE))*100.0)"))
	$(info Size: $(HEXFILE_SIZE)/$(HEXFILE_MAXSIZE) ($(PERCENTAGE)% ocupado))
    
build-hex: $(HEXFILE) print-hexsize

flash-hex: $(HEXFILE)
	$(AVRDUDE) -p$(AVRDUDE_PARTNO) -c$(AVRDUDE_PROGRAMMER) -P$(AVRDUDE_PORT) -b$(AVRDUDE_SPEED) \
-Uflash:w:$(HEXFILE):i 

# Regla para crear el archivo de la base de datos.
build-db: schema.sql
	rm -f $(DB)
	sqlite3 $(DB) < $<

# Reglas para limpiar archivos generados.
clean:
	rm -f $(TARBALL)
	rm -f update_pending
	rm -f $(HEXFILE)
	rm -f $(EEPFILE)
	rm -f $(ELFFILE)
	rm -f $(CORELIB)
	rm -f $(AVRDUDE_CONFIG_FILE)
	rm -f $(DB)
	rm -rf $(ROOTFS_ADDITIONS_GEN)

clean-all: clean
	rm -f $(CORE_OBJ) $(APP_OBJ)
	rm -f $(CORE_OBJ:.o=.d)
	rm -f $(APP_OBJ:.o=.d)

help:
	$(info ----------------------------------------------------------------------------------) 
	$(info Haga:)
	$(info make build-tarball - para crear el tarball sin el hexfile)
	$(info make build-tarball-with-hex - para crear el tarball con el hexfile)
	$(info make build-db - para recrear el archivo de bd)
	$(info make build-hex - para compilar el codigo de Arduino)
	$(info make build-rootfs-additions - para generar archivos adicionales del rootfs)
	$(info make clean - para limpiar archivos generados)
	$(info make clean-all - para limpiar todos los archivos generados)
	$(info make flash-hex - para subir el codigo al Arduino)
	$(info make help - para mostrar este mensaje)
	$(info make install - para instalar la aplicacion en esta computadora)
	$(info make print-hexsize - para mostrar el tamano total en bytes del codigo de Arduino)
	$(info make update - para simular una actualizacion en esta computadora)
	$(info ----------------------------------------------------------------------------------)
