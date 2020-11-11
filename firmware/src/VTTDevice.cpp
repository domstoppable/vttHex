#include "VTTDevice.h"
#include "Logger.h"
#include "CommandStream.h"
#include "WIFI_Credentials.h"

#include <WiFi.h>
#include <ESPmDNS.h>

WiFiServer server;
WiFiClient client;

CommandStream* commandStreams[10];
int commandStreamCount = 0;

void VTTDevice::setup(){
	display.setup();
	display.showText("   Vibey\nTranscribey\n\n   v2.0");
	WiFi.begin(WIFI_SSID, WIFI_KEY);

	Serial.begin(115200);
	Serial.setRxBufferSize(2048);

	delay(2000);

	Logger* GlobalLogger = new CombinedLogger(&display);
	Logger::setGlobal(GlobalLogger);

	grid.setup();
	//ring.setup();

	pinMode(BUTTON_1, INPUT_PULLUP);
	pinMode(BUTTON_2, INPUT_PULLUP);

	long startWait = millis();
	Logger::getGlobal()->info("Waiting for wifi...");
	while(WiFi.status() != WL_CONNECTED) {
		if(millis() - startWait > 30000){
			break;
		}
	}
	if(WiFi.status() != WL_CONNECTED) {
		Logger::getGlobal()->info("Wifi failed :(");
		delay(2000);
	}else{
		Logger::getGlobal()->info("Wifi ok!");
		IPAddress ip = WiFi.localIP();

		int ipStrLength = ip.toString().length()+1;

		char ipAsChars[ipStrLength];
		ip.toString().toCharArray(ipAsChars, ipStrLength);

		Logger::getGlobal()->info(ipAsChars);

		if (!MDNS.begin("vtt00")) {
			Serial.println("Error setting up MDNS responder!");
		}
		delay(2000);
	}

	server = WiFiServer(1234);
	server.begin();

	while(Serial.available() > 0){
		Serial.read();
	}
	commandStreams.add(new CommandStream(&Serial, &grid, &display));

	Logger::getGlobal()->info("Ready :)");
}

void VTTDevice::update(){
	//unsigned long timeDelta = loopTimer.update();
	//ring.update(timeDelta);

	WiFiClient client = server.available();
	if(client){
		Logger::getGlobal()->debug("New client");
		WiFiClient* clientPtr = new WiFiClient();
		*clientPtr = client;
		commandStreams.add(new CommandStream(clientPtr, &grid, &display));
		Logger::getGlobal()->debug("Client ok");
	}

	if(digitalRead(BUTTON_1) == LOW){
		sprintf(msg, "T %02d", testID);
		Logger::getGlobal()->debug(msg);
		grid.testActuator(testID);

		grid.calibrate();
		//ring.calibrate();
		//Logger::getGlobal()->info("Ready :)");

	}
	if(digitalRead(BUTTON_2) == LOW){
		testID = (testID + 1) % 12;
		sprintf(msg, "TEST %02d", testID);
		Logger::getGlobal()->debug(msg);
		grid.testActuator(testID);
	}

	for(int i=0; i<commandStreams.size(); i++){
		commandStreams.get(i)->update();
	}
}
