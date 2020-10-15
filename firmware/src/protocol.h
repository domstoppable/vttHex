#ifndef __PROTOCOL_H
#define __PROTOCOL_H

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

#define MAX_CMD_SIZE 4
#define NUM_COMMANDS 10

extern uint8_t CMD_PAYLOAD_SIZES[NUM_COMMANDS];
extern uint8_t commandBuffer[MAX_CMD_SIZE];

bool flushToLatestCommand();
byte serialReadBlocking();
void flushSerialInput();
byte nextByte();

#endif
