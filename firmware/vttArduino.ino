#include "HexGrid.h"
#include "Display.h"

#define CMD_HEADER            0x00
#define CMD_CALIBRATE         0x01
#define CMD_ACTUATOR_ENABLE   0x02
#define CMD_ACTUATOR_DISABLE  0x03
#define CMD_BASE_FREQUENCY    0x04
#define CMD_INTENSITY         0x05
#define CMD_COMBINED_SIGNAL   0x06
#define CMD_STOP              0x07

#define CALIBRATE_BUTTON 10

#define ACTUATOR_COUNT 3
HexGrid grid;
Display display;

void setup(){
	display.setup();
	display.showText("   ...");
	display.showText("0123456789AA98765432100123456789AA9876543210");

	delay(5000);
	Serial.begin(115200);
	Serial.println("Initializing...");
	display.showText("Initialize\n...");

	grid.setup();

	pinMode(CALIBRATE_BUTTON, INPUT_PULLUP);

	display.showText("Ready :)");
	Serial.println("Ready!");
}

char msg[45];
void loop(){
	if(digitalRead(CALIBRATE_BUTTON) == LOW){
		display.showText("Auto\nCalibrate");
		Serial.println("CALIBRATE");
		//grid.calibrate();
		delay(1000);
		display.showText("Ready :)");
	}

	if(Serial.available() > 0){
		byte header = serialReadBlocking();
		if(header != CMD_HEADER){
			Serial.print("out of sync "); Serial.println(header);
			display.showText("Serial out of sync");
			grid.disableAll();
			flushSerialInput();
			return;
		}

		byte cmd = serialReadBlocking();

		if(cmd == CMD_CALIBRATE){
			display.showText("Calibrate");
			grid.calibrate();
		}else if(cmd == CMD_ACTUATOR_ENABLE){
			byte data = serialReadBlocking();
			sprintf(msg, "%02d Enable", data);
			display.showText(msg);
			Serial.println(msg);
			grid.enable(data, 255);
		}else if(cmd == CMD_ACTUATOR_DISABLE){
			byte data = serialReadBlocking();
			sprintf(msg, "%02d Disable", data);
			display.showText(msg);
			Serial.println(msg);
			grid.disable(data);
		}else if(cmd == CMD_BASE_FREQUENCY){
			byte data = serialReadBlocking();
			display.showText("Freq");
			Serial.print("Frequency "); Serial.println(data);
		}else if(cmd == CMD_COMBINED_SIGNAL){
			byte phone = serialReadBlocking();
			byte pitch = serialReadBlocking();
			byte intensity = serialReadBlocking();

			grid.enable(phone, intensity);
			//display.display();

			//sprintf(msg, " %02d ON     %03d Pitch  %03d Volume ", phone, pitch, intensity);
			//display.showText(msg);
			//display.showText("0123456789AA98765432100123456789AA9876543210");
			//Serial.println(msg);

		}else if(cmd == CMD_STOP){
			grid.disableAll();
			//display.showText("disable all");
		}else{
			display.showText("???");
			Serial.print("??? "); Serial.println(cmd);
		}
	}
}

byte serialReadBlocking(){
	while(Serial.available() == 0){}

	return Serial.read();
}

void flushSerialInput(){
	while(Serial.available() > 0){
		Serial.read();
	}
}
