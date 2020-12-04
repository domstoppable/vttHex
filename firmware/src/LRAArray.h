#ifndef __LRA_ARRAY_H
#define __LRA_ARRAY_H


#include "Arduino.h"
#include "MuxedDriver.h"


class LRAArray {
	public:
		void setup(int enPin0, int enPin1, int enPin2, int adPin0_0, int adPin0_1, int adPin1_0, int adPin1_1, int adPin2_0, int adPin2_1);

		void calibrate(bool fast=true);
		void setValue(int id, int value);

		void disableAll();

		//Haptic_DRV2605 hapticDriver;

	protected:
		MuxedDriver drivers[3];

		void switchToDriver(int driverID);
		//void setDriverChannel(int driverID, int channelID);
};

#endif
