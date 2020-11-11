#ifndef __LRA_ARRAY_H
#define __LRA_ARRAY_H

#define TCA_ADDR 0x70
#define DRV2605_ADDR 0x5A
#define MAX_ACTUATORS 128

#include "Arduino.h"
#include "Haptic_DRV2605.h"

typedef struct {
	uint8_t muxAddress;
	uint8_t deviceID;
} MuxedActuator;


class LRAArray{
	public:
		void setup(uint8_t arrayCount, uint8_t startMux, uint8_t startIdx);
		void calibrate(bool fast=true);
		void switchTo(uint8_t id);
		void setValue(uint8_t value);
		void setValue(uint8_t id, uint8_t value);
		bool isOk(uint8_t id);
		void disableMuxForActuator(uint8_t id);
		void sendThenDisableMux(uint8_t id, uint8_t value);

		MuxedActuator toMuxed(uint8_t logicalID);

		void disableAll();

		Haptic_DRV2605 driver;
		uint8_t actuatorStatus[MAX_ACTUATORS];

	protected:
		uint8_t arrayCount = 0;
		uint8_t startMux = 0;
		uint8_t startIdx = 0;
};

const struct scr_type calibrate_mplus_0934w[] = {
	{DRV2605_REG_MODE,          0x07}, //! DRV2605 - Calibrate Mode!

	{DRV2605_REG_RATEDV,        0x51}, //! DRV2605 - rated voltage 2V
	{DRV2605_REG_CLAMPV,        0x64}, //! DRV2605 - clamp voltage = 2.2V
	{DRV2605_REG_FEEDBACK,      0xF6}, //! DRV2605 - LRA mode

	{DRV2605_REG_CONTROL1,      0x93}, //! DRV2605 - drive_time set for 200Hz = 2.5mSec
	{DRV2605_REG_CONTROL2,      0xF5}, //! DRV2605 - sample_time = 3, balnk =1, idiss = 1
	{DRV2605_REG_CONTROL3,      0x88}, //! DRV2605 - LRA closed loop
	{DRV2605_REG_CONTROL4,      0x30}, //! DRV2605 - Autocal time = 3 (1.2 seconds!)

	{DRV2605_REG_LIBRARY,       0x06}, //! DRV2605 - Library 6 is LRA
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
	{ACTUATOR_SCRIPT_END,       0x00}  //! DRV2605 - end of script flag
};

#endif
