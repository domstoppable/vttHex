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

void HexGrid::enable(uint8_t cellID, uint8_t intensity, uint8_t pitch){
	if(currentCell != 255){
		disable(currentCell);
	}
	_setValue(activationMap[cellID][0], activationMap[cellID][1], 255);
	currentCell = cellID;

	// pitch/intensity array
	int overlaps = 3;
	int actuatorIdxA = min(2, (int)(pitch/255.0f * overlaps));
	int overlapWidth = 255 / overlaps;

	for(int i=0; i<2; i++){
		int actuatorIdx = actuatorIdxA+i;

		float actuatorHotspot = 255.0f * (actuatorIdx)/3.0f;
		float distanceFromHotspot = abs(pitch - actuatorHotspot);
		float relativeValue = ((float)intensity) * (1.0f - (distanceFromHotspot / overlapWidth));
		uint8_t clampedValue = min(255.0f, max(0.0f, relativeValue));

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
		value *= 0.5f;
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
