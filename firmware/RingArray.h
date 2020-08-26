#ifndef __RINGARRAY_H
#define __RINGARRAY_H

#include "LRAArray.h"

class RingArray {
	public:
		void setup();
		void calibrate();
		void setDebugFunc(void (*func)(char*));
		void update(long delta);

		bool enabled;
		int rpm = 0;
		uint8_t intensity = 0;

	protected:
		LRAArray actuators;
		float theta = 0;
		uint8_t actuatorCount = 4;
};

#endif
