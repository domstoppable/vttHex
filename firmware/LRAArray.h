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
		void calibrate();
		void switchTo(uint8_t id);
		void setValue(uint8_t value);
		void setValue(uint8_t id, uint8_t value);
		bool isOk(uint8_t id);
		void disableMuxForActuator(uint8_t id);
		void sendThenDisable(uint8_t id, uint8_t value);

		MuxedActuator toMuxed(uint8_t logicalID);

		void disableAll();

		Haptic_DRV2605 driver;
		uint8_t actuatorStatus[MAX_ACTUATORS];

	protected:
		uint8_t arrayCount = 0;
		uint8_t startMux = 0;
		uint8_t startIdx = 0;
};

#endif
