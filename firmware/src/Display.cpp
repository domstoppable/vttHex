#include <Adafruit_GFX.h>
#include <Fonts/FreeMonoBold9pt7b.h>

#include "Display.h"

Display::Display() : Adafruit_SSD1306(128, 64){}

bool Display::setup(){
	if(!begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
		return false;
	}

	clearDisplay();
	setTextColor(SSD1306_WHITE);
	setFont(&FreeMonoBold9pt7b);

	return true;
}

void Display::showText(const char *fmt, ...) {
	va_list args;

	char text[45];
	va_start(args, fmt);
	vsprintf(text, fmt, args);

	clearDisplay();
	setCursor(0, 10);
	println(text);
	display();

	va_end(args);
}