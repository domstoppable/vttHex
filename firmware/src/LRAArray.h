#ifndef __LRA_ARRAY_H
#define __LRA_ARRAY_H


#include "Arduino.h"
#include "MuxedDriver.h"

class LRAArray {
	public:
		void setup();

		void calibrate(bool fast=true);
		void setValue(int id, uint8_t value);
		void setDriverChannelValue(int driverID, int channelID, uint8_t value);

		void disableAll();
		void writeRegister(uint8_t reg, uint8_t val);

	protected:
		MuxedDriver drivers[5];

		int addressPins[3] = {-1, -1, -1};
		int busPositions[5] = { -1, -1, -1, -1, -1 };
		int mintensity = 128;

		void switchToDriver(int driverID);
};

#endif
