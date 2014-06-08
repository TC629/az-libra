#include "serialsm.hpp"

#include "string.h"

#include <stdlib.h>

SerialSM::SerialSM() :
    state(IDLE),
    nextBufferByte(0) {
}

void SerialSM::processInput(const char* bytesIn, const int nBytesIn) {

    for(int i = 0; i < nBytesIn; ++i) {
        
        switch(state) {
        
            case READING:

                if(nextBufferByte >= bytesBuffered+BUFFER_SIZE) {
                    // Ya no hay espacio en el buffer, entonces ignoramos
                    // este comando...
                    state = IDLE;
                }
                else {

                    if(CMD_END_BYTE != bytesIn[i]) {

                        *nextBufferByte++ = bytesIn[i];
                    }
                    else {

                        if(commands.size() < MAX_COMMANDS) {

                            // Si todavia no se ha alcanzado el
                            // maximo numero de comandos, entonces
                            // agregamos el recien leido. Si no
                            // lo descartamos.

                            *nextBufferByte++ = '\0';
                            // Crear el comando.
                            Command cmd;

                            char* codeEnd = strchr(bytesBuffered, ';');
                            if(codeEnd) {
                                *codeEnd = '\0';
                            }

                            const int code = atoi(bytesBuffered);

                            if(code < CMD_UNDEFINED) {
                                cmd.code = CommandCode(code);
                            }
                            else {
                                cmd.code = CMD_UNDEFINED;
                            }

                            if(codeEnd) {
                                const char* argStart = codeEnd+1;
                                const int cmdArgSize = strlen(argStart);
                                if(cmdArgSize) {
                                    cmd.arg = new char[cmdArgSize+1]; 
                                    memcpy(cmd.arg, argStart, cmdArgSize);
                                    cmd.arg[cmdArgSize] = '\0';
                                }
                                else {
                                    cmd.arg = 0;
                                }
                            }
                            else {
                                cmd.arg = 0;
                            }

                            // Agregar el comando a la cola.
                            commands.enqueue(cmd);
                        }

                        // Reiniciar el estado.
                        state = IDLE;
                    }
                }
            break;

            case IDLE:
                
                if(CMD_START_BYTE == bytesIn[i]) {

                    nextBufferByte = bytesBuffered;
                    state = READING;
                }
                // else: descartamos, porque es basura...

            break;

            default:
            break;
        }
    } 
}

bool SerialSM::commandAvailable() {

    return commands.size() > 0;
}

Command SerialSM::nextCommand() {

    if(commands.size() > 0) {

        return commands.dequeue();
    }
    else {

        Command cmd;
        return cmd;
    }
}
