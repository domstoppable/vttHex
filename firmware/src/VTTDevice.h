#ifndef __VTTDEVICE_H
#define __VTTDEVICE_H


#include "Logger.h"
#include "SerialLogger.h"
#include "DisplayLogger.h"

#include "HexGrid.h"
#include "Display.h"
#include "CommandStream.h"
#include "SoundBite.h"
#include "LoopTimer.h"

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
		SoundBite soundBites[10];

		Display display;

		char msg[45];
		uint8_t testID = 0;

	public:
		void setup();
		void update();

	protected:
		//void playBite(SoundBite* bite);
		void displayDebugMessage(char* msg);
		CommandStream commandStreams[2];
};

#endif
