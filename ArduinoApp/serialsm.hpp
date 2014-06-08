#ifndef LIBRA_SERIAL_HPP
#define LIBRA_SERIAL_HPP

#define CMD_START_BYTE '<'
#define CMD_END_BYTE '>'

#define BUFFER_SIZE 64
#define MAX_COMMANDS 10

#include "queue.hpp"

enum CommandCode {

    CMD_SET_MIN_WEIGHT, // 0
    CMD_SET_MAX_WEIGHT, // 1
    CMD_START,          // 2
    CMD_STOP,           // 3
    CMD_PING,           // 4
    CMD_UNDEFINED
};

struct Command {

    CommandCode code;
    char* arg;

    Command() : code(CMD_UNDEFINED), arg(0) { }

    void freeMemory() { if(arg) { delete[] arg; arg = 0; } }
};

class SerialSM {

    public:
        SerialSM();

        void processInput(const char* bytesIn, const int nBytesIn);

        bool commandAvailable();
        Command nextCommand();

    private:

        enum State {

            IDLE,
            READING
        };

        State state;

        char bytesBuffered[BUFFER_SIZE];
        char* nextBufferByte;

        Queue<Command> commands;
};

#endif
