#include "MuxedDriver.h"
#include "Logger.h"

#include <Wire.h>

void MuxedDriver::setup(
	int muxAddressPin0, int muxAddressPin1, int muxAddressPin2,
	int posOfChannel0, int posOfChannel1, int posOfChannel2, int posOfChannel3
) {
	this->muxAddressPins[0] = muxAddressPin0;
	this->muxAddressPins[1] = muxAddressPin1;
	this->muxAddressPins[2] = muxAddressPin2;

	this->channelPositions[0] = posOfChannel0;
	this->channelPositions[1] = posOfChannel1;
	this->channelPositions[2] = posOfChannel2;
	this->channelPositions[3] = posOfChannel3;

	for(int i=0; i<3; i++){
		if(this->muxAddressPins[i] != -1){
			pinMode(this->muxAddressPins[i], OUTPUT);
			digitalWrite(this->muxAddressPins[i], LOW);
		}
	}
}

bool MuxedDriver::setChannel(int channelID){
	int position = channelPositions[channelID];
	if(position == -1){
		return false;
	}

	for(int i=0; i<3; i++){
		if(muxAddressPins[i] > -1){
			int enabled = 1 & (position >> i);
			digitalWrite(muxAddressPins[i], enabled);
		}
	}

	return true;
}

bool MuxedDriver::setValue(int channelID, uint8_t value){
	if(!setChannel(channelID)){
		return false;
	}

	if(value > 0){
		hapticDriver.setMode(STREAM_MODE);
		hapticDriver.setRealtimeValue(value);
	}else{
		hapticDriver.setRealtimeValue(0);
		hapticDriver.setMode(INACTIVE_MODE);
	}
	return true;
}

void MuxedDriver::calibrate(bool fast){
	char buffer[255];

	Wire.begin();

	DeviceStatus status = checkStatus();
	if (status.ok()) {
		Serial.println("\t** init ok! **\n");
		hapticDriver.writeRegScript(default_jinlong_G1040003D);
		for(int i=0; i<8; i++){
			if(!fast){
				if(setChannel(i)){
					doFullCalibration();
				}
			}else{
				if(setValue(i, 255)){
					delay(150);
					setValue(i, 0);
					delay(100);
				}
			}
		}

		status = checkStatus();
	}else{
		Serial.println("\t** init fail! **\n");
	}
}

DeviceStatus MuxedDriver::checkStatus(){
	DeviceStatus status;
	status.raw = hapticDriver.readReg(DRV2605_REG_STATUS);
	status.deviceID = (status.raw & 0b11100000 ) >> 5;
	status.diagResult = (status.raw & 0b100) >> 2;
	status.overTemp = (status.raw & 0b10) >> 1;
	status.overCurrent = (status.raw & 0b1);

	Serial.print("*** Device status: ");
	Serial.println(status.raw);
	Serial.print("*  Device ID   : ");
	Serial.println(status.deviceID);
	Serial.print("*  diagResult  : ");
	Serial.println(status.diagResult);
	Serial.print("*  overTemp    : ");
	Serial.println(status.overTemp);
	Serial.print("*  overCurrent : ");
	Serial.println(status.overCurrent);

	return status;
}

bool MuxedDriver::doFullCalibration(){
	hapticDriver.writeReg(DRV2605_REG_MODE, 0x07);
	hapticDriver.writeReg(DRV2605_REG_GO, 0x01);

	// wait for go bit to clear
	long startTime = millis();
	while (hapticDriver.readReg(DRV2605_REG_GO) & 0x01) {
		if(millis() - startTime > 3000){
			Serial.println("TIMEOUT");
			return false;
		}
		yield();
	}
	hapticDriver.writeReg(DRV2605_REG_MODE, 0x05);

	char buffer[255];
	Serial.println("Reading results");
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

	return true;
}
