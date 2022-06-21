#include "Logger.h"
#include "Display.h"
#include "Arduino.h"

class DisplayLogger: public Logger{
	protected:
		Display* display = nullptr;

	public:
		DisplayLogger(Display* display){
			this->display = display;
		}

		void log(LogLevel level, char* msg){
			if(level >= filterLevel){
				if(level == LogLevel::INFO){
					display->showText(msg);
				}else{
					char buffer[255];

					sprintf(buffer, "%s: %s", getLevelName(level), msg);
					display->showText(buffer);
				}
			}
		}
};
