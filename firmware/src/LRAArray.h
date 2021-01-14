#ifndef __LRA_ARRAY_H
#define __LRA_ARRAY_H


#include "Arduino.h"
#include "MuxedDriver.h"

class LRAArray {
	public:
		void setup();

		void calibrate(bool fast=true);
		void setValue(int id, int value);
		void setDriverChannelValue(int driverID, int channelID, int value);

		void disableAll();

		Haptic_DRV2605 hapticDriver;

	protected:
		MuxedDriver drivers[5];

		int addressPins[3] = {-1, -1, -1};
		int busPositions[5] = { -1, -1, -1, -1, -1 };

		void switchToDriver(int driverID);
};

#endif
