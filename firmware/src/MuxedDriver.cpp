#include "MuxedDriver.h"
#include "Wire.h"

#include "Logger.h"

void MuxedDriver::setup(){
	setup(-1, -1, -1, -1);
}

void MuxedDriver::setup(int driverEnablePin){
	setup(driverEnablePin, -1, -1, -1);
}

void MuxedDriver::setup(int driverEnablePin, int muxAddressPin0){
	setup(driverEnablePin, muxAddressPin0, -1, -1);
}
void MuxedDriver::setup(int driverEnablePin, int muxAddressPin0, int muxAddressPin1){
	setup(driverEnablePin, muxAddressPin0, muxAddressPin1, -1);
}

void MuxedDriver::setup(int driverEnablePin, int muxAddressPin0, int muxAddressPin1, int muxAddressPin2) {
	this->driverEnablePin = driverEnablePin;
	this->muxAddressPins[0] = muxAddressPin0;
	this->muxAddressPins[1] = muxAddressPin1;
	this->muxAddressPins[2] = muxAddressPin2;

	if(this->driverEnablePin != -1){
		pinMode(this->driverEnablePin, OUTPUT);
	}

	for(int i=0; i<3; i++){
		if(this->muxAddressPins[i] != -1){
			pinMode(this->muxAddressPins[i], OUTPUT);
		}
	}
}

void MuxedDriver::setEnabled(bool enabled){
	if(driverEnablePin > -1){
		digitalWrite(driverEnablePin, enabled);
	}
}

void MuxedDriver::setChannel(int channelID){
	for(int i=0; i<3; i++){
		if(muxAddressPins[i] > -1){
			int enabled = 1 & (channelID >> i);
			digitalWrite(muxAddressPins[i], enabled);
		}
	}
}

void MuxedDriver::setValue(int channelID, uint8_t value){
	setChannel(channelID);
	if(value > 0){
		hapticDriver.setMode(STREAM_MODE);
		hapticDriver.setRealtimeValue(value);
	}else{
		hapticDriver.setRealtimeValue(0);
		hapticDriver.setMode(INACTIVE_MODE);
	}
}

void MuxedDriver::calibrate(bool fast){
	char buffer[255];

	setEnabled(true);

	int driverStatus = hapticDriver.begin();

	if (driverStatus != HAPTIC_SUCCESS) {
		sprintf(buffer, "\tDriver init fail! Status = %d", driverStatus);
		Logger::getGlobal()->info(buffer);
	}else{
		for(int channelID=0; channelID<4; channelID++){
			sprintf(buffer, "\tChannel = %d", channelID);
			Logger::getGlobal()->info(buffer);

			setChannel(channelID);

			hapticDriver.setActuatorType(LRA);
			hapticDriver.writeRegScript(default_mplus_0934w);
			if(fast){
				hapticDriver.setMode(STREAM_MODE);
				hapticDriver.setRealtimeValue(255);
				delay(100);
				hapticDriver.setRealtimeValue(0);
				hapticDriver.setMode(INACTIVE_MODE);
			}else{
				hapticDriver.writeRegScript(calibrate_mplus_0934w);

				uint8_t feedbackControl = hapticDriver.readReg(DRV2605_REG_FEEDBACK);
				sprintf(buffer, "\t\t  Feedback control = %d", feedbackControl);
				Logger::getGlobal()->info(buffer);

				uint8_t calComp = hapticDriver.readReg(DRV2605_REG_AUTOCALCOMP);
				sprintf(buffer, "\t\t  calComp          = %d", calComp);
				Logger::getGlobal()->info(buffer);

				uint8_t calBemf = hapticDriver.readReg(DRV2605_REG_AUTOCALEMP);
				sprintf(buffer, "\t\t  calBemf          = %d", calBemf);
				Logger::getGlobal()->info(buffer);
				Logger::getGlobal()->info("");
			}
		}
	}
}
