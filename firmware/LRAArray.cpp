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

void LRAArray::setValue(uint8_t id, uint8_t value){
	if(isOk(id)){
		switchTo(id);
		setValue(value);
	}
}

bool LRAArray::isOk(uint8_t id){
	return actuatorStatus[id] == HAPTIC_SUCCESS;
}

void LRAArray::calibrate(){
	Wire.begin();
	for (uint8_t actuatorID = 0; actuatorID < MAX_ACTUATORS; actuatorID++) {
		if(actuatorID >= arrayCount){
			actuatorStatus[actuatorID] = -99;
			continue;
		}

		uint8_t data;
		uint8_t thisStatus = -99;

		switchTo(actuatorID);
		//if (!twi_writeTo(DRV2605_ADDR, &data, 0, 1, 1)) {
		if(true){
			thisStatus = driver.begin();
			if (thisStatus == HAPTIC_SUCCESS) {
				driver.setActuatorType(LRA);
				driver.playScript(0);       // Reset/Init
				driver.playScript(1);       // LRA Motor Init
				driver.playScript(4);       // LRA Calibrate
				driver.setMode(INACTIVE_MODE);
			}
		}

		if(DBG){
			Serial.print("Actuator init status #");
			Serial.print(actuatorID);
			Serial.print(" = ");
			Serial.println(thisStatus);
		}

		actuatorStatus[actuatorID] = thisStatus;
	}
}

void LRAArray::disableAll(){
	for(uint8_t i = 0; i<this->arrayCount; i++){
		setValue(i, 0);
		driver.setMode(INACTIVE_MODE);
	}
}
