#include "LRAArray.h"
#include "Wire.h"

#define DBG true

/*
extern "C" {
	#include "utility/twi.h"
}
*/

void LRAArray::setup(int arrayCount){
	this->arrayCount = arrayCount;
	Wire.begin();
	calibrate();
}

void LRAArray::switchTo(uint8_t id) {
	uint8_t tcaID = (id / 8);
	id = id % 8;

	Wire.beginTransmission(TCA_ADDR + tcaID);
	Wire.write(1 << id);
	Wire.endTransmission();
}

void LRAArray::setValue(uint8_t value){
	if(value > 0){
		driver.setMode(STREAM_MODE);
	}
	driver.setRealtimeValue(value);
	if(value == 0){
		driver.setMode(INACTIVE_MODE);
	}
}

void LRAArray::sendThenDisable(uint8_t id, uint8_t value) {
	uint8_t muxID = (id / 8);
	id = id % 8;

	Wire.beginTransmission(TCA_ADDR + muxID);
	Wire.write(1 << id);
	Wire.endTransmission();

	setValue(value);

	disableMux(muxID);
}

void LRAArray::disableMux(uint8_t muxID) {
	Wire.beginTransmission(TCA_ADDR + muxID);
	Wire.write(0);
	Wire.endTransmission();
}


void LRAArray::setValue(uint8_t id, uint8_t value) {
	if(isOk(id)){
		sendThenDisable(id, value);
	}
}

bool LRAArray::isOk(uint8_t id){
	return actuatorStatus[id] == HAPTIC_SUCCESS;
}

void LRAArray::calibrate(){
	if(debugFunc){
		debugFunc("Init status");
	}

	char buffer[45] = "Init status ";
	for (uint8_t actuatorID = 0; actuatorID < MAX_ACTUATORS; actuatorID++) {
		if(actuatorID >= arrayCount){
			actuatorStatus[actuatorID] = -99;
			continue;
		}

		uint8_t data;
		uint8_t thisStatus = -99;

		switchTo(actuatorID);
		thisStatus = driver.begin();
		if (thisStatus == HAPTIC_SUCCESS) {
			buffer[12+actuatorID] = 'O';
			if(debugFunc){
				debugFunc(buffer);
			}

			driver.setActuatorType(LRA);
			driver.playScript(0);       // Reset/Init
			driver.playScript(4);       // LRA Calibrate
			driver.setMode(INACTIVE_MODE);
		}else{

			buffer[12+actuatorID] = '-';
			if(debugFunc){
				debugFunc(buffer);
			}
		}


		actuatorStatus[actuatorID] = thisStatus;
		disableMux(actuatorID/8);
	}
}

void LRAArray::disableAll(){
	for(uint8_t i = 0; i<this->arrayCount; i++){
		setValue(i, 0);
		driver.setMode(INACTIVE_MODE);
	}
}

void LRAArray::setDebugFunc(void (*func)(char*)){
	this->debugFunc = func;
}
