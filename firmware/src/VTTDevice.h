#ifndef __VTTDEVICE_H
#define __VTTDEVICE_H


#include "Logger.h"
#include "SerialLogger.h"
#include "DisplayLogger.h"

#include "HexGrid.h"
#include "Display.h"
#include "protocol.h"
#include "SoundBite.h"
#include "RingArray.h"
#include "LoopTimer.h"

#define CALIBRATE_BUTTON 32
#define BUTTON_2 33
#define ACTUATOR_COUNT 3

class CombinedLogger: public Logger {
	protected:
		DisplayLogger* displayLogger;
		SerialLogger* streamLogger;

	public:
		CombinedLogger(Display* display){
			this->displayLogger = new DisplayLogger(display);
			this->streamLogger = new SerialLogger();
		}

		void log(LogLevel level, char* msg){
			if(level >= filterLevel){
				displayLogger->log(level, msg);
				streamLogger->log(level, msg);
			}
		}
};

class VTTDevice {
	protected:
		LoopTimer loopTimer;

		HexGrid grid;
//		RingArray ring;
		SoundBite soundBite;

		Display display;

		char msg[45];

	public:
		void setup();
		void update();

	protected:
		void playBite();
		void displayDebugMessage(char* msg);

};

#endif
