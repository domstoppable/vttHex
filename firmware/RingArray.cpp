#include "RingArray.h"

#define TAU 6.2831853072
#define PI 3.1415926535

float mod(float a, float divisor){
	return a -(floor(a/divisor) * divisor);
}

float angleDelta(float a, float b){
	return abs(mod((a-b+PI), TAU)-PI);
}

void RingArray::setup(){
//	actuators.setup(actuatorCount, 1, 4);
	actuators.setup(actuatorCount, 0, 0);
}

void RingArray::update(unsigned long delta){
	if(!enabled) return;

	theta += (delta / 1000.0f) / 60.0f * rpm;

	float radsPerSector = TAU / actuatorCount;

	for(int actuatorID = 0; actuatorID < actuatorCount; actuatorID++) {
		float actuatorAngle = actuatorID*radsPerSector;
		float delta = angleDelta(actuatorAngle, theta);
		float strengthPercent = (radsPerSector - delta) / radsPerSector;
		if(strengthPercent < 0){
			strengthPercent = 0;
		}

		actuators.setValue(actuatorID, strengthPercent * intensity);
	}
}
