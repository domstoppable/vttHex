#ifndef __LRA_ARRAY_H
#define __LRA_ARRAY_H

#define TCA_ADDR 0x70
#define DRV2605_ADDR 0x5A
#define MAX_ACTUATORS 128

#include "Arduino.h"
#include "Haptic_DRV2605.h"

class LRAArray{
	public:
		void setup(int arrayCount);
		void calibrate();
		void switchTo(uint8_t id);
		void setValue(uint8_t value);
		void setValue(uint8_t id, uint8_t value);
		bool isOk(uint8_t id);
		void setDebugFunc(void (*func)(char*));
		void disableMux(uint8_t muxID);
		void sendThenDisable(uint8_t id, uint8_t value);

		void disableAll();

		Haptic_DRV2605 driver;
		uint8_t actuatorStatus[MAX_ACTUATORS];

	protected:
		int arrayCount = 0;
		void (*debugFunc)(char*);
};

#endif
