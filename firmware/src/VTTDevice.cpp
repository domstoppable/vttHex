#include "VTTDevice.h"
#include "Logger.h"
#include "CommandStream.h"

#if defined (USE_WIFI)
	#include "WIFI_Credentials.h"
	#include <WiFi.h>
	#include <ESPmDNS.h>

	WiFiServer server;
	WiFiClient client;

	char hostname[] = "vt00";
#endif


void VTTDevice::setup(){
	display.setup();

	char startScreen[41];
	esp_reset_reason_t resetReason = esp_reset_reason();
	sprintf(startScreen, "   Vibey\nTranscribey\n   v2.6\n% 11d", resetReason);
	display.showText(startScreen);

	#if defined (USE_WIFI)
		WiFi.begin(WIFI_SSID, WIFI_KEY);
	#endif

	Serial.begin(115200);
	Serial.setRxBufferSize(2048);

	delay(2000);

	Logger* GlobalLogger = new CombinedLogger(&display);
	Logger::setGlobal(GlobalLogger);

	grid.setup();

	#if defined (USE_WIFI)
		long startWait = millis();
		Logger::getGlobal()->info("Trying wifi...");
		while(WiFi.status() != WL_CONNECTED) {
			if(millis() - startWait > 3000){
				break;
			}
		}

		char ipAsChars[32] = "No wifi\0";

		if(WiFi.status() != WL_CONNECTED) {
			Logger::getGlobal()->info("Wifi failed :(");
			delay(2000);
		}else{
			Logger::getGlobal()->info("Wifi ok!");
			IPAddress ip = WiFi.localIP();

			sprintf(ipAsChars, "  %d.%d.\n    %d.%d", ip[0], ip[1], ip[2], ip[3]);
			Logger::getGlobal()->info(ipAsChars);

			if (!MDNS.begin(hostname)) {
				Logger::getGlobal()->error("Error setting up MDNS responder!");
			}
		}

		server = WiFiServer(1234);
		server.begin();
	#endif

	while(Serial.available() > 0){
		Serial.read();
	}

	commandStreams[0].configure(&Serial, &grid, &display, soundBites);

	#if defined (USE_WIFI)
		char msg[45];
		sprintf(msg, "  Ready :)\n%s.local\n%s", hostname, ipAsChars);
		Logger::getGlobal()->info(msg);
	#else
		Logger::getGlobal()->info("\n  Ready :)");
	#endif
}

void VTTDevice::update(){

	#if defined (USE_WIFI)
		WiFiClient client = server.available();
		if(client){
			Logger::getGlobal()->debug("New client");
			WiFiClient* clientPtr = new WiFiClient();
			*clientPtr = client;
			commandStreams[1].configure(clientPtr, &grid, &display, soundBites);
			Logger::getGlobal()->debug("New TCP client");
		}
	#endif

	for(int i=0; i<2; i++){
		commandStreams[i].update();
	}
}
