#ifndef __LOOPTIMER_H
#define __LOOPTIMER_H

#include "Arduino.h"

class LoopTimer {
	protected:
		unsigned long startTime = 0l;
		unsigned long lastTime = 0l;

	public:
		unsigned long update(){
			unsigned long now = millis();

			if(startTime == 0){
				startTime = now;
				lastTime = now;
			}

			unsigned long delta = now - lastTime;
			lastTime = now;

			return delta;
		}

		unsigned long totalDelta(){
			return lastTime - startTime;
		}

		void reset(){
			startTime = 0l;
			lastTime = 0l;
		}
};

#endif
