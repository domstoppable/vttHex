#ifndef __COMMANDSTREAM_H
#define __COMMANDSTREAM_H

#include "HexGrid.h"
#include "Display.h"
#include "SoundBite.h"

#define CMD_HEADER            0x00
#define CMD_CALIBRATE         0x01
#define CMD_CELL_ENABLE       0x02
#define CMD_CELL_DISABLE      0x03
#define CMD_PITCH             0x04
#define CMD_INTENSITY         0x05
#define CMD_COMBINED_SIGNAL   0x06
#define CMD_STOP              0x07
#define CMD_SOUNDBITE         0x08
#define CMD_PLAY_BITE         0x09
#define CMD_SET_ACTUATOR_INT  0x0A
#define CMD_PULSE_ACTUATOR    0x0B
#define CMD_PING              0x0C

#define NUM_COMMANDS 13

#define MAX_CMD_SIZE 32768

#define FACE_VIBING     "\n    ^  ^\n   ~~~~~~\0"
#define FACE_NORMAL     "\n    O  O\n   \\____/\0"
#define FACE_LONELY     "\n    x  x\n    ----\0"
#define FACE_CONFUSED   "\n    ?  ?\n    ----\0"

extern uint8_t CMD_PAYLOAD_SIZES[NUM_COMMANDS];

extern uint8_t commandBuffer[MAX_CMD_SIZE];

class CommandStream {
public:
	HexGrid* grid = nullptr;
	Display* display = nullptr;
	Stream* stream = nullptr;
	SoundBite* soundBites = nullptr;

	long lastPing = 0l;

	CommandStream(){}

	void configure(Stream* stream, HexGrid* hexGrid, Display* display, SoundBite* soundBites){
		this->stream = stream;
		this->grid = hexGrid;
		this->display = display;
		this->soundBites = soundBites;

		for(int i=0; i<MAX_CMD_SIZE; i++){
			commandBuffer[i] = 0;
		}
	}

	void update();
	void sendOk();

private:
	int bufferIdx = 0;
	uint8_t commandBuffer[MAX_CMD_SIZE];

	byte nextByte();
	bool flushToLatestCommand();
	byte readBlocking();
	void flush();
	void playBite(uint8_t id);

	bool everReceivedCommand = false;
};

#endif