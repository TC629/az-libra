# Configuracion del Arduino a utilizar
# Solo se soportan el Arduino UNO y el Arduino Mega (R3).
# Atencion: el soporte para el Arduino UNO dependera
# tambien del codigo fuente, mas que todo por los pines de
# los que se haga uso.

AVRDUDE_PORT = /dev/ttyACM0
AVRDUDE_SPEED = 115200

# Mega 
AVRDUDE_PROGRAMMER = wiring
AVRDUDE_PARTNO = m2560
HEXFILE_MAXSIZE = 258048
ARDUINO_VARIANT = mega
GCC_MCU = atmega2560

# Uno
#AVRDUDE_PROGRAMMER = arduino
#AVRDUDE_PARTNO = m328p
#HEXFILE_MAXSIZE = 32256
#ARDUINO_VARIANT = uno
#GCC_MCU = atmega328p

WPA_SUPPLICANT_SSID=tmpssid
WPA_SUPPLICANT_PSK=tmppsk

