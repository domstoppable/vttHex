#include "LRAArray.h"
#include "MuxedDriver.h"
#include "Wire.h"

#include "Logger.h"

#define DS0    5
#define DS1   18
#define DS2   19

#define RPOS   2
#define RS0   23
#define RS1   32

#define GPOS   4
#define GS0   33
#define GS1   25

#define BPOS   3
#define BS0   14
#define BS1   12

#define YAPOS  0
#define YAS   13

#define YBPOS  1
#define YBS    4

#define RC_POS 2, 1, 0, 3
#define GC_POS 2, 1, 0, 3
#define BC_POS 2, 1, 0, 3

void LRAArray::setup(
){
	addressPins[0] = DS0;
	addressPins[1] = DS1;
	addressPins[2] = DS2;

	for(int i=0; i<3; i++){
		if(addressPins[i] > -1){
			pinMode(addressPins[i], OUTPUT);
			digitalWrite(addressPins[i], LOW);
		}
	}

	busPositions[0] = RPOS;
	busPositions[1] = GPOS;
	busPositions[2] = BPOS;
	busPositions[3] = YAPOS;
	busPositions[4] = YBPOS;

	drivers[0].setup(RS0, RS1, -1, RC_POS);
	drivers[1].setup(GS0, GS1, -1, GC_POS);
	drivers[2].setup(BS0, BS1, -1, BC_POS);
	drivers[3].setup(YAS, -1, -1, 0, 1, -1, -1);
	drivers[4].setup(YBS, -1, -1, 0, 1, -1, -1);
}

void LRAArray::switchToDriver(int driverID){
	char buffer[128];

	int busPosition = busPositions[driverID];

	for(int i=0; i<3; i++){
		int pinValue = (busPosition >> i) & 1;
		digitalWrite(addressPins[i], pinValue);
	}
}

void LRAArray::calibrate(bool fast){
	Wire.begin();

	//char buffer[128];
	//sprintf(buffer, "\nCalibrate...\n fast=%d", fast);
	//Logger::getGlobal()->info(buffer);
	//delay(1500);

	for(int driverID=0; driverID<5; driverID++){
		//sprintf(buffer, "Calibrate\n driver %d", driverID);
		//Logger::getGlobal()->info(buffer);

		switchToDriver(driverID);
		drivers[driverID].calibrate(fast);
	}
}

void LRAArray::setValue(int id, uint8_t value) {
	if(id < 12){
		int driverID = id / 4;
		int channelID = id % 4;
		setDriverChannelValue(driverID, channelID, value);
	}else if(id<16){
		int driverID = 3 + (id%2);
		int channelID = (id-12)/2;
		setDriverChannelValue(driverID, channelID, value);
	}
}

void LRAArray::setDriverChannelValue(int driverID, int channelID, uint8_t value){
	/*
	float maxtensity = 255.0f;
	if(value > 0){
		value = (int)((maxtensity-mintensity) * (value/maxtensity) + mintensity);
	}
	value = max((uint8_t)0, min(value, (uint8_t)maxtensity));
	*/
	if(value > 0){
		value = (int)((255.0f-mintensity) * (value/255.0f) + mintensity);
	}
	value = max((uint8_t)0, min(value, (uint8_t)254));

	switchToDriver(driverID);
	drivers[driverID].setValue(channelID, value);
}

void LRAArray::disableAll(){
	for(int channelID=0; channelID<5; channelID++){
		setDriverChannelValue(channelID, 0, 0);
	}
}
