#ifndef __SOUND_BITE_H
#define __SOUND_BITE_H

#include <Arduino.h>

typedef struct sample {
	uint8_t phone = 0;
	uint8_t pitch = 0;
	uint8_t intensity = 0;

	bool operator==(const sample& rhs) const {
		return (
			phone == rhs.phone &&
			pitch == rhs.pitch &&
			intensity == rhs.intensity
		);
	}

	bool operator!=(const sample& rhs) const {
		return !operator==(rhs);
	}
} Sample;

class SoundBite {
	public:
		uint8_t period = 0;
		uint16_t sampleCount = 0;
		Sample samples[12288];
		uint sampleIdx = 0;

		void init(uint8_t period, uint sampleCount);
};

#endif
