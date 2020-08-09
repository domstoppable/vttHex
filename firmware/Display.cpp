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

void Display::showText(char* text){
	clearDisplay();
	setCursor(0, 10);
	println(text);
	display();
}
