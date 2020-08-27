#include "HexGrid.h"

void HexGrid::setup(){
	actuators.setup(12, 0, 0);
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
