#include "VTTDevice.h"
#include "Logger.h"

void VTTDevice::setup(){
	display.setup();
	display.showText("   Vibey\nTranscribey\n\n   v2.0");

	Serial.begin(115200);
	Serial.setRxBufferSize(2048);

	delay(2000);

	Logger::setGlobal(new CombinedLogger(&display));
	grid.setup();
	//ring.setup();

	pinMode(CALIBRATE_BUTTON, INPUT_PULLUP);
	pinMode(BUTTON_2, INPUT_PULLUP);

	Logger::getGlobal()->info("Ready :)");
}

void VTTDevice::update(){
	unsigned long timeDelta = loopTimer.update();
	//ring.update(timeDelta);

	if(digitalRead(CALIBRATE_BUTTON) == LOW){
		grid.calibrate();
		//ring.calibrate();
		Logger::getGlobal()->info("Ready :)");
	}

	if(!flushToLatestCommand()){
		return;
	}
	byte cmd = nextByte();

	if(cmd == 255 || cmd == 0){
		// NOP
	}else if(cmd == CMD_CALIBRATE){
		grid.calibrate();
	}else if(cmd == CMD_ACTUATOR_ENABLE){
		byte cellID = nextByte();
		sprintf(msg, "%02d Enable", cellID);
		Logger::getGlobal()->debug(msg);

		grid.enable(cellID, 255);
	}else if(cmd == CMD_ACTUATOR_DISABLE){
		byte cellID = nextByte();
		sprintf(msg, "%02d Disable", cellID);
		Logger::getGlobal()->debug(msg);

		grid.disable(cellID);
	}else if(cmd == CMD_PITCH){
		byte pitch = nextByte();
		display.showText("Freq");
		Serial.print("Frequency "); Serial.println(pitch);

	}else if(cmd == CMD_COMBINED_SIGNAL){
		byte phone = nextByte();
		byte pitch = nextByte();
		byte intensity = nextByte();

		if(phone != 255){
			grid.enable(phone, intensity);
			//ring.enable(pitch, (float)intensity/255.0f);
			sprintf(msg, " %02d ON     %03d Pitch  %03d Volume ", phone, pitch, intensity);
			display.showText(msg);
		}
	}else if(cmd == CMD_STOP){
		grid.disableAll();
		//ring.disable();
		display.showText("");
	}else if(cmd == CMD_SOUNDBITE){
		uint8_t period = nextByte();
		uint8_t sampleCountAsBytes[2] = { nextByte(), nextByte() };
		uint16_t sampleCount;

		memcpy(&sampleCount, sampleCountAsBytes, 2);

		sprintf(msg, "S-Bite in  %03d samples %03d period", sampleCount, period);
		Logger::getGlobal()->debug(msg);

		soundBite.init(period, sampleCount);
		for(int i=0; i<sampleCount; i++){
			soundBite.samples[i].phone = serialReadBlocking();
			soundBite.samples[i].pitch = serialReadBlocking();
			soundBite.samples[i].intensity = serialReadBlocking();
		}
	}else if(cmd == CMD_PLAY_BITE){
		Serial.println("Play SoundBite");
		playBite();
	}else{
		Logger::getGlobal()->debug("???");
		Serial.println(cmd);
	}
}

void VTTDevice::playBite(){
	long startTime = millis();
	long now = startTime;

	long sampleIdx = 0;
	Sample lastSample;
	while(sampleIdx < soundBite.sampleCount){
		long delta = millis() - startTime;
		sampleIdx = int(delta / soundBite.period);

		Sample sample = soundBite.samples[sampleIdx];
		if(sample != lastSample){
			grid.enable(sample.phone, sample.intensity);
			//ring.enable(sample.pitch, (float)sample.intensity/255.0f);

			sprintf(msg, " %02d ON     %03d Pitch  %03d Volume ", sample.phone, sample.pitch, sample.intensity);
			display.showText(msg);
			lastSample = sample;
		}
	}
	grid.disableAll();
	//ring.disable();
	Logger::getGlobal()->debug("/SoundBite");
}
