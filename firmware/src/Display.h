#ifndef __DISPLAY_H
#define __DISPLAY_H

#include <Adafruit_SSD1306.h>

class Display : Adafruit_SSD1306{
	public:
		Display();
		bool setup();
		void showText(const char* text);
};

#endif
