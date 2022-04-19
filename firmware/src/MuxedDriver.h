#pragma once

#define DRV2605_ADDR 0x5A

#include "Arduino.h"
#include "Haptic_DRV2605.h"


typedef struct {
	uint8_t raw;

	uint8_t deviceID;
	bool diagResult;
	bool overTemp;
	bool overCurrent;

	bool ok(){
		//return raw != 255 && deviceID == 7 && diagResult == false && overTemp == false && overCurrent == false;
		return raw != 255;
	}
} DeviceStatus;
class MuxedDriver {
	public:
		void setup(
			int muxAddressPin0, int muxAddressPin1, int muxAddressPin2,
			int posOfChannel0, int posOfChannel1, int posOfChannel2, int posOfChannel3
		);

		void setEnabled(bool enabled);
		bool setValue(int channelID, uint8_t value);

		void calibrate(bool fast);
		void writeRegister(uint8_t reg, uint8_t val);

		DeviceStatus checkStatus();

	protected:

		Haptic_DRV2605 hapticDriver;

		int muxAddressPins[3] = { -1, -1, -1 };
		int channelPositions[8] = { -1, -1, -1, -1, -1, -1, -1, -1 };

		bool setChannel(int channelID);
		bool doFullCalibration();
		bool setGoAndWait(long timeout=3000l);
};


const struct scr_type default_jinlong_G1040003D[] = {
	{DRV2605_REG_MODE,          0x80}, //! DRV2605 - reset
	{ACTUATOR_SCRIPT_DELAY,     0x50}, //! DRV2605 - delay 50mSec for Reset? no spec?

	{DRV2605_REG_RATEDV,        0x65}, //! DRV2605 - rated voltage 2.5v
	{DRV2605_REG_CLAMPV,        0x7D}, //! DRV2605 - clamp voltage = 2.75V
	{DRV2605_REG_FEEDBACK,      0xF6}, //! DRV2605 - LRA mode

	{DRV2605_REG_CONTROL1,      0x98}, //! DRV2605 - drive_time set for 170Hz = 2.94ms
	{DRV2605_REG_CONTROL2,      0x75}, //! DRV2605 - sample_time = 3, balnk =1, idiss = 1
	{DRV2605_REG_CONTROL3,      0xA9}, //! DRV2605 - LRA open loop
	{DRV2605_REG_CONTROL4,      0x30}, //! DRV2605 - Autocal time = 3 (1.2 seconds!)

	{DRV2605_REG_LIBRARY,       0x06}, //! DRV2605 - Library 6 is LRA

	{DRV2605_REG_AUTOCALCOMP,   0x0C},
	{DRV2605_REG_AUTOCALEMP,    0x6C},

	{DRV2605_REG_MODE,          0x05}, // Realtime playback mode
	{0x20,                      0x3C}, // OL_LRA_PERIOD[6:0]
	{DRV2605_REG_RTPIN,         0x7F},


	{ACTUATOR_SCRIPT_END,       0x00}  //! DRV2605 - end of script flag
};
