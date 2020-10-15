#include "RingArray.h"

#define TAU 6.2831853072
#define PI 3.1415926535

#define STRENGTH_MIN 0
#define STRENGTH_MAX 180
#define STRENGTH_RANGE STRENGTH_MAX-STRENGTH_MIN

float mod(float a, float divisor){
	return a -(floor(a/divisor) * divisor);
}

float angleDelta(float a, float b){
	return abs(mod((a-b+PI), TAU)-PI);
}

void RingArray::setup(){
	actuators.setup(actuatorCount, 1, 4);
}

void RingArray::calibrate(){
	actuators.calibrate();
}

void RingArray::update(unsigned long delta){
	if(!enabled) return;

	theta += (delta / 1000.0f) / 60.0f * rpm * TAU;
	theta = mod(theta, TAU);

	float radsPerSector = TAU / (actuatorCount/2);

	for(int actuatorID = 0; actuatorID < actuatorCount; actuatorID++) {
		float actuatorAngle = actuatorID*radsPerSector;
		float delta = angleDelta(actuatorAngle, theta);
		float strengthPercent = (radsPerSector - delta) / radsPerSector;
		if(strengthPercent < 0){
			strengthPercent = 0;
		}

		actuators.setValue(actuatorID, (strengthPercent * intensity) * STRENGTH_RANGE + STRENGTH_MIN);
	}
}

void RingArray::disable(){
	enabled = false;
	actuators.disableAll();
}

void RingArray::enable(){
	enabled = true;
}

void RingArray::enable(int rpm, float intensity){
	enabled = true;
	this->rpm = rpm;
	this->intensity = intensity;
}