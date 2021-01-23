#ifndef __HEX_GRID_H
#define __HEX_GRID_H

#include "Arduino.h"
#include "LRAArray.h"

#define R1  0
#define R2  1
#define R3  2
#define R4  3

#define G1  4
#define G2  5
#define G3  6
#define G4  7

#define B1  8
#define B2  9
#define B3 10
#define B4 11

const int activationMap[][2] = {
	{R1,R1}, {R1,G1}, {G1,G1}, {G1,B1}, {B1,B1}, {B1,R1},
	{R1,G2}, {R1,B2}, {G1,B2}, {G1,R2}, {R2,B1}, {B1,G2},
	{G2,B2}, {B2,B2}, {B2,R2}, {R2,R2}, {R2,G2}, {G2,G2},
	{G2,R3}, {R3,B2}, {B2,G3}, {G3,R2}, {R2,B3}, {B3,G2},
	{R3,R3}, {R3,G3}, {G3,G3}, {G3,B3}, {B3,B3}, {B3,R3},
	{G4,R3}, {R3,B4}, {B4,G3}, {G3,R4}, {R4,B3}, {B3,G4},
	{G4,B4}, {B4,B4}, {B4,R4}, {R4,R4}, {R4,G4}, {G4,G4},
};

typedef struct {
	int driver;
	int channel;
} DriverChannelPair;

class HexGrid{
	public:
		void setup();
		void testActuator(uint8_t actuatorID);
		void enable(uint8_t cellID, uint8_t intensity, uint8_t pitch);
		void disable(uint8_t cellID);
		void calibrate();
		void disableAll();

	protected:
		LRAArray actuators;
		uint8_t currentCell = 255;

		void _setValue(uint8_t idA, uint8_t idB, uint8_t value);

};

#endif
