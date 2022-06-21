#include "Logger.h"

#include "Arduino.h"

class SerialLogger: public Logger{
	public:
		void log(LogLevel level, char* msg){
			if(level >= filterLevel){
				Serial.print(getLevelName(level));
				Serial.print(": ");
				Serial.println(msg);
			}
		}
};
