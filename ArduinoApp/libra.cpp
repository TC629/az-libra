#include <Arduino.h>
#include <stdlib.h>

#include <libra.hpp>

int main() {

    // ---------------------------
    // Codigo original de Arduino.
    // ---------------------------

    init();

    #if defined(USBCON)
        USBDevice.attach();
    #endif

    // ------------------------
    // Codigo de la aplicacion.
    // ------------------------

    chBegin(chSetup); // nunca devuelve el control
 
    return 0;
}


// Esta funcion se corre desde el hilo principal.
void chSetup() {

    // Threads controladores de balanzas

    // Thread de comunicacion
    chThdCreateStatic(waCommThread, sizeof(waCommThread),
        NORMALPRIO + 1, CommThread, NULL);
}

// Hilo que se encarga de manejar la comunicacion
// entre el Arduino y el pcDuino.
msg_t CommThread(void* arg) {

    int nBytesIn = 0;

    // Se inicia la comunicacion serial con el pcDuino.
    // Se debe esperar un momento, debido a que utilizamos
    // serial a traves de USB.
    Serial.begin(9600);
    while(!Serial) {
    }

    // El resto de los threads deben esperar a que
    // se establezca la comunicacion serial.
    // Esto se logra con un semaforo que actua de barrera.
    while(Serial.available() <= 0) {
    }

    // El pcDuino envia un byte para dar la sennal de inicio,
    // descartamos ese byte.
    Serial.read();
    Serial.println("ack");

    // Dejamos que el resto de los threads inicien.
    while(waiting_at_barrier > 0) {
        chSemSignal(&barrier_sem);
        --waiting_at_barrier;
    } 

    while(1) {

        nBytesIn = Serial.available();
        if(nBytesIn > 0) {
    
        }
    }

    return 0;
}
