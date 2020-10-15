#ifndef __RINGARRAY_H
#define __RINGARRAY_H

#include "LRAArray.h"

class RingArray {
	public:
		void setup();
		void calibrate();
		void update(unsigned long delta);
		void enable();
		void enable(int rpm, float intensity);
		void disable();

		bool enabled = false;
		int rpm = 60;
		float intensity = 1.0f;
		float theta = 0;

	protected:
		LRAArray actuators;
		uint8_t actuatorCount = 4;
};

#endif
