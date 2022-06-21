#include "HexGrid.h"

void HexGrid::setup(){
	actuators.setup();
	actuators.calibrate(true);
}

void HexGrid::testActuator(uint8_t actuatorID){
	actuators.setValue(actuatorID, 255);
	delay(1000);
	actuators.setValue(actuatorID, 0);
}

void HexGrid::setActuatorIntensity(uint8_t actuatorID, uint8_t intensity){
	actuators.setValue(actuatorID, intensity);
}
/*
float easeInOutExpo(float x) {
	if(x == 0.0f || x == 1.0f){
		return x;
	}
	if(x < 0.5f){
		return pow(2.0f, 20.0f * x - 10.0f) / 2.0f;
	}else{
		return (2.0f - pow(2.0f, -20.0f * x + 10.0f)) / 2.0f;
	}
}

float easeInOutSine(float x) {
	return -(cos(PI * x) - 1.0f) / 2.0f;
}

float easeInCubic(float x) {
	return x * x * x;
}

float easeInExpo(float x) {
	if(x == 0.0f){
		return 0.0f;
	}
	return pow(2.0f, 10.0f * x - 10.0f);
}

float easeOutExpo(float x) {
	if(x == 1.0f){
		return 1.0f;
	}

	return pow(2.0f, -10.0f * x);
}
*/

void HexGrid::enable(uint8_t cellID, uint8_t intensity, uint8_t pitch){
	const float* easeFunc = easeFunc_cubicInOut;

	if(currentCell != 255 && currentCell != cellID){
		disable(currentCell);
	}
	_setValue(activationMap[cellID][0], activationMap[cellID][1], 255);
	currentCell = cellID;

	// pitch/intensity array
	int actuatorCount = 4;
	int actuatorIdxA = min(2, (int)(pitch/255.0f * (actuatorCount-1)));
	int overlapWidth = 255 / (actuatorCount-1);

	int transitionIdx = pitch % overlapWidth;
	float values[] = {
		intensity*easeFunc[overlapWidth - transitionIdx - 1],
		intensity*easeFunc[transitionIdx]
	};

	for(int i=0; i<2; i++){
		int actuatorIdx = actuatorIdxA+i;

		uint8_t clampedValue = min(255.0f, max(0.0f, values[i]));

		int driverID = (actuatorIdx % 2) + 3;
		int channelID = (actuatorIdx / 2);

		actuators.setDriverChannelValue(driverID, channelID, clampedValue);
	}
}

void HexGrid::disable(uint8_t cellID){
	_setValue(activationMap[cellID][0], activationMap[cellID][1], 0);
	currentCell = 255;
}

void HexGrid::_setValue(uint8_t idA, uint8_t idB, uint8_t value){
	if(idA != idB){
		value *= 0.75f;
	}
	actuators.setValue(idA, value);
	actuators.setValue(idB, value);
}

void HexGrid::calibrate(){
	actuators.calibrate();
}

void HexGrid::disableAll(){
	actuators.disableAll();
}
