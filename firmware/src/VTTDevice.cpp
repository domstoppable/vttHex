#include "VTTDevice.h"
#include "Logger.h"
#include "CommandStream.h"
#include "WIFI_Credentials.h"

#include <WiFi.h>
#include <ESPmDNS.h>

WiFiServer server;
WiFiClient client;

char hostname[] = "vtt00";

void VTTDevice::setup(){
	char ipAsChars[16] = "---.---.---.---";

	display.setup();
	display.showText("   Vibey\nTranscribey\n\n   v2.0");
	WiFi.begin(WIFI_SSID, WIFI_KEY);

	Serial.begin(115200);
	Serial.setRxBufferSize(2048);

	delay(2000);

	Logger* GlobalLogger = new CombinedLogger(&display);
	Logger::setGlobal(GlobalLogger);

	grid.setup();

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

		ip.toString().toCharArray(ipAsChars, ipStrLength);

		Logger::getGlobal()->info(ipAsChars);

		if (!MDNS.begin(hostname)) {
			Logger::getGlobal()->error("Error setting up MDNS responder!");
		}
		delay(2000);
	}

	server = WiFiServer(1234);
	server.begin();

	while(Serial.available() > 0){
		Serial.read();
	}

	commandStreams[0].configure(&Serial, &grid, &display, soundBites);

	char msg[45];
	sprintf(msg, "Ready :)\n%s.local\n%s", hostname, ipAsChars);
	Logger::getGlobal()->info(msg);
}

void VTTDevice::update(){
	//unsigned long timeDelta = loopTimer.update();
	//ring.update(timeDelta);

	WiFiClient client = server.available();
	if(client){
		Logger::getGlobal()->debug("New client");
		WiFiClient* clientPtr = new WiFiClient();
		*clientPtr = client;
		commandStreams[1].configure(clientPtr, &grid, &display, soundBites);
		Logger::getGlobal()->debug("New TCP client");
	}

	for(int i=0; i<2; i++){
		commandStreams[i].update();
	}
}
