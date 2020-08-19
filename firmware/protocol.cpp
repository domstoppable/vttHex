#include <Arduino.h>
#include "protocol.h"

uint8_t CMD_PAYLOAD_SIZES[NUM_COMMANDS] = {
	0,
	0,
	1,
	1,
	1,
	1,
	3,
	0,
	3,
	0
};

uint8_t commandBuffer[MAX_CMD_SIZE];


int bufferIdx = 0;

bool flushToLatestCommand(){
	if(Serial.available() == 0){
		return false;
	}

	bufferIdx = 0;
	commandBuffer[0] = 255;
	int commands = 0;
	while(Serial.available() > 0){
		byte header = serialReadBlocking();
		if(header != CMD_HEADER){
			Serial.print("out of sync "); Serial.println(header);
			return false;
		}

		byte cmd = serialReadBlocking();
		if(cmd > NUM_COMMANDS){
			Serial.print("Unknown command "); Serial.println(cmd);
			return false;
		}

		commandBuffer[0] = cmd;
		for(int payloadIdx=0; payloadIdx<CMD_PAYLOAD_SIZES[cmd]; payloadIdx++){
			commandBuffer[payloadIdx+1] = serialReadBlocking();
		}
		commands++;
		if(cmd == CMD_SOUNDBITE){
			return true;
		}
	}

	return true;
}

byte serialReadBlocking(){
	while(Serial.available() == 0){}

	return Serial.read();
}

void flushSerialInput(){
	while(Serial.available() > 0){
		Serial.read();
	}
}

byte nextByte(){
	return commandBuffer[bufferIdx++];
}
