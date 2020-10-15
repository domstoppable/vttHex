#include "LRAArray.h"
#include "Wire.h"

#include "Logger.h"

#define DBG true

/*
extern "C" {
	#include "utility/twi.h"
}
*/

MuxedActuator LRAArray::toMuxed(uint8_t logicalID) {
	MuxedActuator muxedActuator = {
		TCA_ADDR + startMux + (startIdx+logicalID)/8,
		(startIdx+logicalID)%8,
	};

	return muxedActuator;
}

void LRAArray::setup(uint8_t arrayCount, uint8_t startMux, uint8_t startIdx){
	this->arrayCount = arrayCount;
	this->startMux = startMux;
	this->startIdx = startIdx;

	Wire.begin();
	calibrate();
}

void LRAArray::switchTo(uint8_t id) {
	MuxedActuator muxedActuator = toMuxed(id);

	Wire.beginTransmission(muxedActuator.muxAddress);
	Wire.write(1 << muxedActuator.deviceID);
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

void LRAArray::sendThenDisableMux(uint8_t id, uint8_t value) {
	switchTo(id);
	setValue(value);
	disableMuxForActuator(id);
}

void LRAArray::disableMuxForActuator(uint8_t id) {
	MuxedActuator muxedActuator = toMuxed(id);

	Wire.beginTransmission(muxedActuator.muxAddress);
	Wire.write(0x00);
	Wire.endTransmission();
}

void LRAArray::setValue(uint8_t id, uint8_t value) {
	if(isOk(id)){
//		Serial.print("Send then disable mux");
//		Serial.print(id);
//		Serial.print(' ');
//		Serial.println(value);
		sendThenDisableMux(id, value);
	}
}

bool LRAArray::isOk(uint8_t id){
	return actuatorStatus[id] == HAPTIC_SUCCESS;
}

void LRAArray::calibrate(){
	Logger::getGlobal()->info("Init status");

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
			Logger::getGlobal()->info(buffer);

			driver.setActuatorType(LRA);
			driver.playScript(0);       // Reset/Init
			driver.writeRegScript(calibrate_mplus_0934w);
			driver.setMode(INACTIVE_MODE);
		}else{

			buffer[12+actuatorID] = '-';
			Logger::getGlobal()->info(buffer);
		}

		actuatorStatus[actuatorID] = thisStatus;
		disableMuxForActuator(actuatorID);
	}
}

void LRAArray::disableAll(){
	uint8_t id = 0;
	for(id = 0; id+7<this->arrayCount; id+=8){
//		Serial.print("Disable mux for ");
//		Serial.println(id);
		MuxedActuator muxedActuator = toMuxed(id);

		Wire.beginTransmission(muxedActuator.muxAddress);
		Wire.write(0xFF);
		Wire.endTransmission();

		driver.setMode(INACTIVE_MODE);
		disableMuxForActuator(id);
	}

	MuxedActuator lastMux = toMuxed(id);
	uint8_t addressBits = 0;
	for(uint8_t i=0; i+id<this->arrayCount; i++){
		addressBits += 1 << i;
	}
//	Serial.print("Disable mux for ");
//	Serial.println(addressBits);
	Wire.beginTransmission(lastMux.muxAddress);
	Wire.write(addressBits);
	Wire.endTransmission();

	driver.setMode(INACTIVE_MODE);
	disableMuxForActuator(id);
}
