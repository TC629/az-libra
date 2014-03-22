#ifndef _LIBRA_HPP_
#define _LIBRA_HPP_

#include <ChibiOS_AVR.h>

// Buffer para la entrada serial.
#define COMM_IN_BUFFER_SIZE 256
static char commBuffer[COMM_IN_BUFFER_SIZE];

// Semaforo que se utiliza a manera de barrera para que 
// los hilos esperen a que se establezca la comunicacion
// con el pcDuino.
uint8_t waiting_at_barrier = 0;
SEMAPHORE_DECL(barrier_sem, 0);

void chSetup();

static WORKING_AREA(waCommThread, 64);
static msg_t CommThread(void* arg);

#endif
