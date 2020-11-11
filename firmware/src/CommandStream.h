#ifndef __COMMANDSTREAM_H
#define __COMMANDSTREAM_H

#include "HexGrid.h"
#include "Display.h"
#include "SoundBite.h"

#define CMD_HEADER            0x00
#define CMD_CALIBRATE         0x01
#define CMD_ACTUATOR_ENABLE   0x02
#define CMD_ACTUATOR_DISABLE  0x03
#define CMD_PITCH             0x04
#define CMD_INTENSITY         0x05
#define CMD_COMBINED_SIGNAL   0x06
#define CMD_STOP              0x07
#define CMD_SOUNDBITE         0x08
#define CMD_PLAY_BITE         0x09

#define MAX_CMD_SIZE 65536
#define NUM_COMMANDS 10

extern uint8_t CMD_PAYLOAD_SIZES[NUM_COMMANDS];
extern uint8_t commandBuffer[MAX_CMD_SIZE];

class CommandStream {
public:
	HexGrid* grid;
	Display* display;
	Stream* stream;

	CommandStream(Stream* stream, HexGrid* hexGrid, Display* display){
		this->stream = stream;
		this->grid = hexGrid;
		this->display = display;
		for(int i=0; i<MAX_CMD_SIZE; i++){
			commandBuffer[i] = 0;
		}
	}

	void update();

private:
	SoundBite soundBite;

	int bufferIdx = 0;
	uint8_t commandBuffer[MAX_CMD_SIZE];

	byte nextByte();
	bool flushToLatestCommand();
	byte readBlocking();
	void flush();
	void playBite();

};

#endif