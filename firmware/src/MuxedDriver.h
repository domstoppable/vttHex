#pragma once

#define DRV2605_ADDR 0x5A

#include "Arduino.h"
#include "Haptic_DRV2605.h"

class MuxedDriver {
	public:
		void setup();
		void setup(int driverEnablePin);
		void setup(int driverEnablePin, int muxAddressPin0);
		void setup(int driverEnablePin, int muxAddressPin0, int muxAddressPin1);
		void setup(int driverEnablePin, int muxAddressPin0, int muxAddressPin1, int muxAddressPin2);

		void setEnabled(bool enabled);
		void setValue(int channelID, uint8_t value);

		void calibrate(bool fast);

	protected:
		int driverEnablePin;
		int muxAddressPins[3];

		void setChannel(int channelID);

		Haptic_DRV2605 hapticDriver;
};


const struct scr_type calibrate_mplus_0934w[] = {
	{DRV2605_REG_MODE,          0x80}, //! DRV2605 - reset
	{ACTUATOR_SCRIPT_DELAY,     0x50}, //! DRV2605 - delay 50mSec for Reset? no spec?

	{DRV2605_REG_MODE,          0x07}, //! DRV2605 - Calibrate Mode!

	{DRV2605_REG_GO,            0x01}, //! DRV2605 - trigger a calibrate cycle
	{ACTUATOR_SCRIPT_DELAY,     0xFF}, //! DRV2605 - delay 0.25 sec
	{ACTUATOR_SCRIPT_DELAY,     0xFF}, //! DRV2605 - delay 0.25 sec
	{ACTUATOR_SCRIPT_DELAY,     0xFF}, //! DRV2605 - delay 0.25 sec
	{ACTUATOR_SCRIPT_DELAY,     0xFF}, //! DRV2605 - delay 0.25 sec
	{ACTUATOR_SCRIPT_DELAY,     0xFF}, //! DRV2605 - delay 0.25 sec (1.25 sec max)

	{DRV2605_REG_MODE,          0x01}, //! DRV2605 - calibrate

	{ACTUATOR_SCRIPT_END,       0x00}  //! DRV2605 - end of script flag
};

const struct scr_type default_mplus_0934w[] = {
	{DRV2605_REG_MODE,          0x80}, //! DRV2605 - reset
	{ACTUATOR_SCRIPT_DELAY,     0x50}, //! DRV2605 - delay 50mSec for Reset? no spec?

	{DRV2605_REG_RATEDV,        0x51}, //! DRV2605 - rated voltage 2V
	{DRV2605_REG_CLAMPV,        0x64}, //! DRV2605 - clamp voltage = 2.2V
	{DRV2605_REG_FEEDBACK,      0xF6}, //! DRV2605 - LRA mode

	{DRV2605_REG_CONTROL1,      0x93}, //! DRV2605 - drive_time set for 200Hz = 2.5mSec
	{DRV2605_REG_CONTROL2,      0xF5}, //! DRV2605 - sample_time = 3, balnk =1, idiss = 1
	{DRV2605_REG_CONTROL3,      0x88}, //! DRV2605 - LRA closed loop
	{DRV2605_REG_CONTROL4,      0x30}, //! DRV2605 - Autocal time = 3 (1.2 seconds!)

	{DRV2605_REG_LIBRARY,       0x06}, //! DRV2605 - Library 6 is LRA

	{DRV2605_REG_AUTOCALCOMP,   0x0C},
	{DRV2605_REG_AUTOCALEMP,    0x6C},

	{DRV2605_REG_MODE,          0x00}, //! DRV2605 - calibrate
	{ACTUATOR_SCRIPT_END,       0x00}  //! DRV2605 - end of script flag
};

const struct scr_type calibrate_jinlong_G1040003D_base[] = {
	{DRV2605_REG_MODE,          0x80}, //! DRV2605 - reset
	{ACTUATOR_SCRIPT_DELAY,     0x50}, //! DRV2605 - delay 50mSec for Reset? no spec?

	{DRV2605_REG_RATEDV,        0x65}, //! DRV2605 - rated voltage 2.5v
	{DRV2605_REG_CLAMPV,        0x7D}, //! DRV2605 - clamp voltage = 2.75V
	{DRV2605_REG_FEEDBACK,      0xF6}, //! DRV2605 - LRA mode

	{DRV2605_REG_CONTROL1,      0x9D}, //! DRV2605 - drive_time set for 170Hz = 2.5mSec - @TODO: lookup and confirm
	{DRV2605_REG_CONTROL2,      0xF5}, //! DRV2605 - sample_time = 3, balnk =1, idiss = 1
	{DRV2605_REG_CONTROL3,      0x88}, //! DRV2605 - LRA closed loop
	{DRV2605_REG_CONTROL4,      0x30}, //! DRV2605 - Autocal time = 3 (1.2 seconds!)

	{ACTUATOR_SCRIPT_END,       0x00}  //! DRV2605 - end of script flag
};
