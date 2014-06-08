#ifndef LIBRA_HPP_
#define LIBRA_HPP_

// Define los estados en los que puede estar el controlador.
enum ControllerState {

    CONTROLLER_IDLE,
    CONTROLLER_RUNNING
};

// Define los estados en los que puede estar una celda de carga.
enum CellState {

  CELL_READING,
  CELL_READY,
  CELL_STALLED
};

// Prototipos de los procedimientos y funciones.
void setup();
void loop();
void serialEvent();

float getWeight(const int addr);
void setWeight(const int addr, const float value);


#endif
