#include "LRAArray.h"
#include "MuxedDriver.h"
#include "Wire.h"

#include "Logger.h"

void LRAArray::setup(int enPin0, int enPin1, int enPin2, int adPin0_0, int adPin0_1, int adPin1_0, int adPin1_1, int adPin2_0, int adPin2_1){
	drivers[0].setup(enPin0, adPin0_0, adPin0_1);
	drivers[1].setup(enPin1, adPin1_0, adPin1_1);
	drivers[2].setup(enPin2, adPin2_0, adPin2_1);
}

void LRAArray::switchToDriver(int driverID){
	for(int i=0; i<3; i++){
		drivers[i].setEnabled(i == driverID);
	}
}

void LRAArray::calibrate(bool fast){
	Wire.begin();
	char buffer[128];

	Logger::getGlobal()->info("Calibrating...");

	for(int driverID=0; driverID<1; driverID++){
		switchToDriver(driverID);
		sprintf(buffer, "Calibrate driver %d", driverID);
		Logger::getGlobal()->info(buffer);
		drivers[driverID].calibrate(fast);
	}
}

void LRAArray::setValue(int id, int value) {
	int driverID = id / 4;
	int channelID = id % 4;

	switchToDriver(driverID);
	drivers[driverID].setValue(channelID, value);
}

void LRAArray::disableAll(){
	for(int id=0; id<12; id++){
		setValue(id, 0);
	}
}
