#include <Arduino.h>

#include <Adafruit_ADS1015.h>
#include <EEPROM.h>
#include <Wire.h>

#include <stdlib.h>

#include <libra.hpp>
#include <serialsm.hpp>

//#define LIBRA_DEBUG_

// Variables globales.
#define HALT_PIN 8

#define N_ADS 1        // solo tenemos un ads
#define N_CELLS_ADS 2  // cada ads puede manejar hasta 2 celdas de carga
#define N_CELLS 1      // solo tenemos una celda de carga

// Direcciones en la memoria EEPROM
#define MIN_WEIGHT_ADDR (sizeof(float) * 0)
#define MAX_WEIGHT_ADDR (sizeof(float) * 1)

// Define el numero de veces que se debe leer el mismo valor en una celda de carga
// para considerar estable su lectura.
#define MEASUREMENTS_TILL_STABLE 8
#define MEASUREMENTS_PER_LOOP (MEASUREMENTS_TILL_STABLE + 2)

// Los diferentes ADS para leer las celdas de carga.
Adafruit_ADS1115 ads[N_ADS] = {Adafruit_ADS1115(0x48)};

// Representa la abcisa de la funcion lineal.
int16_t loadCellX[N_CELLS];

// Parametros de la funcion lineal que representa la celda de carga.
// peso = f(x) = a * float(x) + b
float loadCellA[N_CELLS] = {5.1008675876};
float loadCellB[N_CELLS] = {-137.789799528};

// Pines de los LEDs que corresponden a cada celda.
int redLED[N_CELLS] = {6};
int greenLED[N_CELLS] = {7};

// Utilizados para manejar el estado de una celda de carga.
int loadCellStability[N_CELLS];
CellState loadCellState[N_CELLS];

ControllerState state;
SerialSM ssm;
char serialEventBuffer[BUFFER_SIZE];

float minWeight;
float maxWeight;

char outputBuffer[BUFFER_SIZE];

int main() {

    init();

    #if defined(USBCON)
        USBDevice.attach();
    #endif

    setup();

    while(!digitalRead(HALT_PIN)) {

        for(int i = 0; i < 10 && !digitalRead(HALT_PIN); ++i) {
          loop();
        }
        serialEvent();
    }

    Serial.println("halted");
    while(1) {}
 
    return 0;
}

void setup() {

    pinMode(HALT_PIN, INPUT);

    for(int i = 0; i < N_CELLS; ++i) {
        pinMode(redLED[i], OUTPUT);
        pinMode(greenLED[i], OUTPUT);
        digitalWrite(redLED[i], LOW);
        digitalWrite(greenLED[i], LOW);
    }

    minWeight = getWeight(MIN_WEIGHT_ADDR);
    maxWeight = getWeight(MAX_WEIGHT_ADDR);
    state = CONTROLLER_IDLE;

    // Inicializar variables para lectura de celdas de carga.
    for(int i = 0; i < N_CELLS; ++i) {

        loadCellStability[i] = 0;
        loadCellState[i] = CELL_READING;
    }

    // Inicializar los ADSs.
    for(int i = 0; i < N_ADS; ++i) {

        ads[i].setGain(GAIN_SIXTEEN);
        ads[i].begin();
    }

    Serial.begin(9600);
    // Flushear el buffer
    while(Serial.available()) {
      Serial.read();
    }

    Serial.println("ready");
    #ifdef LIBRA_DEBUG_
    Serial.print("minWeight = ");
    Serial.println(minWeight);
    Serial.print("maxWeight = ");
    Serial.println(maxWeight);
    #endif

}

void loop() {

    int16_t x; // una muestra
    float weight;

    switch(state) {

        case CONTROLLER_RUNNING:

            // Se hace "time-sharing" para las celdas.
            for(int m = 0; m < MEASUREMENTS_PER_LOOP; ++m) {
                for(int i = 0; i < N_CELLS; ++i) {

                    switch(loadCellState[i]) {

                        case CELL_READING:

                            if(0 == i % N_CELLS_ADS)
                                x = ads[i % N_ADS].readADC_Differential_0_1();   
                            else
                                x = ads[i % N_ADS].readADC_Differential_2_3();

                            if(x == loadCellX[i]) {
                                loadCellStability[i]++;
                                if(MEASUREMENTS_TILL_STABLE == loadCellStability[i]) {
                                    loadCellState[i] = CELL_READY;
                                }
                            }
                            else {
                                loadCellStability[i] = 0;
                                loadCellX[i] = x;
                            }

                            digitalWrite(greenLED[i], LOW);
                            digitalWrite(redLED[i], LOW);

                        break;

                        case CELL_READY:

                            loadCellState[i] = CELL_STALLED;

                            weight = loadCellA[i] * float(loadCellX[i]) + loadCellB[i];
                            if(abs(weight) > 0.1) { // weight != 0
                                if(minWeight <= weight && weight <= maxWeight) {

                                    Serial.print(i);
                                    Serial.print(';');
                                    Serial.println(weight);
                                    digitalWrite(greenLED[i], HIGH);
                                }
                                else {
                                    #ifdef LIBRA_DEBUG_
                                    Serial.print("fuera de rango: ");
                                    Serial.println(weight);
                                    #endif
                                    digitalWrite(redLED[i], HIGH);
                                }
                            }
                        break;

                        case CELL_STALLED:

                            if(0 == i % N_CELLS_ADS)
                                x = ads[i % N_ADS].readADC_Differential_0_1();   
                            else
                                x = ads[i % N_ADS].readADC_Differential_2_3();

                            if(x != loadCellX[i]) {

                                loadCellStability[i] = 0;
                                loadCellState[i] = CELL_READING;
                                delay(30);
                            }

                        break;

                    }
                }
                delay(5);
            }
             
        break;

        default:
        break;
    }

}

void serialEvent() {

    int nbytes = Serial.available();

    if(nbytes > 0) {

        Serial.readBytes(serialEventBuffer, nbytes);
        ssm.processInput(serialEventBuffer, nbytes); 

        while(ssm.commandAvailable()) {

            Command cmd = ssm.nextCommand();
            switch(cmd.code) {

                case CMD_SET_MIN_WEIGHT:
                    minWeight = atof(cmd.arg);
                    setWeight(MIN_WEIGHT_ADDR, minWeight);
                    Serial.println("ack");
                    cmd.freeMemory();
                break;

                case CMD_SET_MAX_WEIGHT:
                    maxWeight = atof(cmd.arg);
                    setWeight(MAX_WEIGHT_ADDR, maxWeight);
                    Serial.println("ack");
                    cmd.freeMemory();
                break;

                case CMD_START:
                    state = CONTROLLER_RUNNING;
                    Serial.println("ack");
                break;

                case CMD_STOP:
                    state = CONTROLLER_IDLE;
                    Serial.println("ack");
                break;

                case CMD_PING:
                    Serial.println("pong");
                break;

                case CMD_UNDEFINED:
                    Serial.println("nack");
                break;
            }
        } 
    }
}

// Devuelve el flotante almacenado a partir de la direccion addr.
// Utiliza la convencion "big-endian".
float getWeight(const int addr) {
  
    float value;
    byte* bytes = (byte*) &value;
    const int nbytes = int(sizeof(float));

    for(int i = 0; i < nbytes; ++i) {
    bytes[i] = EEPROM.read(addr+i);
    }

    return value;
}

// Guarda un flotante a partir de la direccion addr.
// Utiliza la convencion "big-endian".
void setWeight(const int addr, const float value) {

    byte* bytes = (byte*) &value;
    const int nbytes = int(sizeof(float));

    for(int i = 0; i < nbytes; ++i) {
    EEPROM.write(addr+i, bytes[i]);
    }
}
