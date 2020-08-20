#include "HexGrid.h"
#include "Display.h"
#include "protocol.h"
#include "SoundBite.h"

#define CALIBRATE_BUTTON 32

#define ACTUATOR_COUNT 3
HexGrid grid;
Display display;

SoundBite soundBite;

void setup(){
	display.setup();
	display.showText("0123456789AA98765432100123456789AA9876543210");

	grid.setDebugFunc(displayDebugMessage);

	Serial.begin(115200);
	Serial.setRxBufferSize(2048);
	displayDebugMessage("Init...");

	grid.setup();

	pinMode(CALIBRATE_BUTTON, INPUT_PULLUP);

	display.showText("Ready :)");
	Serial.println("Ready!");
}

void displayDebugMessage(char* msg){
	Serial.println(msg);
	display.showText(msg);
}

char msg[45];
void loop(){
	if(digitalRead(CALIBRATE_BUTTON) == LOW){
		grid.calibrate();
		display.showText("Ready :)");
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
		displayDebugMessage(msg);

		grid.enable(cellID, 255);
	}else if(cmd == CMD_ACTUATOR_DISABLE){
		byte cellID = nextByte();
		sprintf(msg, "%02d Disable", cellID);
		displayDebugMessage(msg);

		grid.disable(cellID);
	}else if(cmd == CMD_PITCH){
		byte pitch = nextByte();
		display.showText("Freq");
		Serial.print("Frequency "); Serial.println(pitch);
	}else if(cmd == CMD_COMBINED_SIGNAL){
		byte phone = nextByte();
		byte pitch = nextByte();
		byte intensity = nextByte();

		grid.enable(phone, intensity);

		sprintf(msg, " %02d ON     %03d Pitch  %03d Volume ", phone, pitch, intensity);
		display.showText(msg);
	}else if(cmd == CMD_STOP){
		grid.disableAll();
		display.showText("");
	}else if(cmd == CMD_SOUNDBITE){
		uint8_t period = nextByte();
		uint8_t sampleCountAsBytes[2] = { nextByte(), nextByte() };
		uint16_t sampleCount;

		memcpy(&sampleCount, sampleCountAsBytes, 2);

		sprintf(msg, "S-Bite in  %03d samples %03d period", sampleCount, period);
		displayDebugMessage(msg);

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
		displayDebugMessage("???");
		Serial.println(cmd);
	}
}

void playBite(){
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

			sprintf(msg, " %02d ON     %03d Pitch  %03d Volume ", sample.phone, sample.pitch, sample.intensity);
			display.showText(msg);
			lastSample = sample;
		}
	}
	grid.disableAll();
	displayDebugMessage("/SoundBite");
}