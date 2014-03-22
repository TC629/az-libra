from twisted.internet import reactor
from twisted.internet.serialport import SerialPort

from config import CONFIG
from protocols import ArduinoClientProtocol, LCDProtocol

if not CONFIG['DEVELOPMENT']:

    arduino = ArduinoClientProtocol()
    SerialPort(arduino, CONFIG['ARDUINO_PORT'], reactor, baudrate=CONFIG['ARDUINO_BAUDRATE'])
    reactor.addSystemEventTrigger('before', 'shutdown', arduino.shutdown)

    lcd = LCDProtocol()
    SerialPort(lcd, CONFIG['LCD_PORT'], reactor, baudrate=CONFIG['LCD_BAUDRATE'])

else:
    arduino = None
    lcd = None
