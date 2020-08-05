#ifndef __HEX_GRID_H
#define __HEX_GRID_H

#include "Arduino.h"
#include "LRAArray.h"

const int activationMap[][2] = {
	{ 0, 0}, { 0, 4}, { 4, 4}, { 4, 8}, { 8, 8}, { 8, 0},
	{ 0, 5}, { 0, 9}, { 9, 4}, { 4, 1}, { 1, 8}, { 8, 5},
	{ 5, 9}, { 9, 9}, { 9, 1}, { 1, 1}, { 1, 5}, { 5, 5},
	{ 5, 2}, { 2, 9}, { 9, 6}, { 6, 1}, { 1,10}, {10, 5},
	{ 2, 2}, { 2, 6}, { 6, 6}, { 6,10}, {10,10}, {10, 2},
	{ 7, 2}, { 2,11}, {11, 6}, { 6, 3}, { 3,10}, {10, 7},
	{ 7,11}, {11,11}, {11, 3}, { 3, 3}, { 3, 7}, { 7, 7}
};

class HexGrid{
	public:
		void setup();
		void enable(uint8_t cellID);
		void disable(uint8_t cellID);
		void calibrate();
		void disableAll();

	protected:
		LRAArray actuators;
		uint8_t currentCell = 255;

		void _setValue(uint8_t idA, uint8_t idB, uint8_t value);
};

#endif
