#include "HexGrid.h"

#include "LRAArray.h"

#define EN_R 23
#define EN_G 19
#define EN_B 16

#define RS0 33
#define RS1 32

#define GS0 5
#define GS1 18

#define BS0 27
#define BS1 14

void HexGrid::setup(){
	actuators.setup(EN_R, EN_G, EN_B, RS0, RS1, GS0, GS1, BS0, BS1);
	actuators.calibrate(true);
}

void HexGrid::testActuator(uint8_t actuatorID){
	actuators.setValue(actuatorID, 255);
	delay(1000);
	actuators.setValue(actuatorID, 0);
}

void HexGrid::enable(uint8_t cellID, uint8_t intensity){
	if(currentCell != 255){
		disable(currentCell);
	}
	_setValue(activationMap[cellID][0], activationMap[cellID][1], intensity);
	currentCell = cellID;
}

void HexGrid::disable(uint8_t cellID){
	_setValue(activationMap[cellID][0], activationMap[cellID][1], 0);
	currentCell = 255;
}

void HexGrid::_setValue(uint8_t idA, uint8_t idB, uint8_t value){
	actuators.setValue(idA, value);
	actuators.setValue(idB, value);
}

void HexGrid::calibrate(){
	actuators.calibrate();
}

void HexGrid::disableAll(){
	actuators.disableAll();
}
