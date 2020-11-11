#ifndef __HEX_GRID_H
#define __HEX_GRID_H

#include "Arduino.h"
#include "LRAArray.h"

const int activationMap[][2] = {
	{ 3, 3}, { 3, 7}, { 7, 7}, { 7,11}, {11,11}, {11, 3},
	{ 3, 6}, { 3,10}, {10, 7}, { 7, 2}, { 2,11}, {11, 6},
	{ 6,10}, {10,10}, {10, 2}, { 2, 2}, { 2, 6}, { 6, 6},
	{ 6, 1}, { 1,10}, {10, 5}, { 5, 2}, { 2, 9}, { 9, 6},
	{ 1, 1}, { 1, 5}, { 5, 5}, { 5, 9}, { 9, 9}, { 9, 1},
	{ 4, 1}, { 1, 8}, { 8, 5}, { 5, 0}, { 0, 9}, { 9, 4},
	{ 4, 8}, { 8, 8}, { 8, 0}, { 0, 0}, { 0, 4}, { 4, 4},
};

class HexGrid{
	public:
		void setup();
		void testActuator(uint8_t actuatorID);
		void enable(uint8_t cellID, uint8_t intensity);
		void disable(uint8_t cellID);
		void calibrate();
		void disableAll();

	protected:
		LRAArray actuators;
		uint8_t currentCell = 255;

		void _setValue(uint8_t idA, uint8_t idB, uint8_t value);
};

#endif