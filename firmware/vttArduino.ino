#include "HexGrid.h"
#include "Display.h"

#define CMD_HEADER            0x00
#define CMD_CALIBRATE         0x01
#define CMD_ACTUATOR_ENABLE   0x02
#define CMD_ACTUATOR_DISABLE  0x03
#define CMD_BASE_FREQUENCY    0x04

#define CALIBRATE_BUTTON 10

#define ACTUATOR_COUNT 3
HexGrid grid;
Display display;

void setup(){
	display.setup();
	display.showText("Initialize\n...");

	Serial.begin(115200);
	Serial.println("Initializing...");

	grid.setup();

	pinMode(CALIBRATE_BUTTON, INPUT_PULLUP);

	display.showText("Ready :)");
	Serial.println("Ready!");
}

void loop(){
	if(digitalRead(CALIBRATE_BUTTON) == LOW){
		display.showText("Auto\nCalibrate");
		Serial.println("CALIBRATE");
		grid.calibrate();
		display.showText("Ready :)");
	}

	if(Serial.available() > 2){
		byte header = Serial.read();
		if(header != CMD_HEADER){
			Serial.print("out of sync "); Serial.println(header);
			display.showText("Serial out of sync");

			return;
		}

		byte cmd = Serial.read();
		byte data = Serial.read();

		char msg[16];
		if(cmd == CMD_CALIBRATE){
			grid.calibrate();
		}else if(cmd == CMD_ACTUATOR_ENABLE){
			sprintf(msg, "%02d Enable", data);
			display.showText(msg);
			Serial.println(msg);
			grid.enable(data);
		}else if(cmd == CMD_ACTUATOR_DISABLE){
			sprintf(msg, "%02d Disable", data);
			display.showText(msg);
			Serial.println(msg);
			grid.disable(data);
		}else if(cmd == CMD_BASE_FREQUENCY){
			display.showText("Freq");
			Serial.print("Frequency "); Serial.println(data);
		}else{
			display.showText("???");
			Serial.print("??? "); Serial.println(cmd);
		}
	}
}
