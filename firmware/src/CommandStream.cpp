#include "CommandStream.h"
#include "Logger.h"

uint8_t CMD_PAYLOAD_SIZES[NUM_COMMANDS] = {
	0,	// CMD_HEADER
	0,	// CMD_CALIBRATE
	1,	// CMD_CELL_ENABLE
	1,	// CMD_CELL_DISABLE
	1,	// CMD_PITCH
	1,	// CMD_INTENSITY
	3,	// CMD_COMBINED_SIGNAL
	0,	// CMD_STOP
	9,	// CMD_SOUNDBITE
	1,	// CMD_PLAY_BITE
	2,	// CMD_SET_ACTUATOR_INT
	1,	// CMD_PULSE_ACTUATOR
	0,	// CMD_PING
};

void CommandStream::update(){
	long now = millis();
	char face[45] = FACE_NORMAL;

	if(stream == nullptr){
		return;
	}

	if(flushToLatestCommand()) {
		everReceivedCommand = true;

		char msg[45];
		uint8_t cmd = nextByteFromBuffer();

		bool doFlush = false;

		if(cmd == 255 || cmd == 0){
			// NOP
		}else if(cmd == CMD_CALIBRATE){
			grid->calibrate();
			sendOk();

		}else if(cmd == CMD_CELL_ENABLE){
			uint8_t cellID = nextByteFromBuffer();
			sprintf(msg, "%02d Enable", cellID);
			Logger::getGlobal()->debug(msg);

			grid->enable(cellID, 255, 0);
			doFlush = true;
			sendOk();

		}else if(cmd == CMD_CELL_DISABLE){
			uint8_t cellID = nextByteFromBuffer();
			sprintf(msg, "%02d Disable", cellID);
			Logger::getGlobal()->debug(msg);

			grid->disable(cellID);
			doFlush = true;
			sendOk();

		}else if(cmd == CMD_PULSE_ACTUATOR){
			sendOk();

			uint8_t actuatorID = nextByteFromBuffer();

			display->showText(FACE_VIBING);
			long startTime = now;
			long duration = 500l;
			while(now-startTime < duration){
				now = millis();
				float elapsed = (float)(now-startTime)/(float)duration;
				elapsed = min(max(elapsed, 0.0f), 1.0f);
				uint8_t intensity = 255*(1.0f-abs(elapsed*2.0f - 1.0f));
				grid->setActuatorIntensity(actuatorID, intensity);
			}

			doFlush = true;

		}else if(cmd == CMD_SET_ACTUATOR_INT){
			uint8_t actuatorID = nextByteFromBuffer();
			uint8_t intensity = nextByteFromBuffer();

			grid->setActuatorIntensity(actuatorID, intensity);
			if(intensity > 0){
				strcpy(face, FACE_VIBING);
			}
			doFlush = true;
			sendOk();

		}else if(cmd == CMD_PITCH){
			//@TODO: implement pitch changing
			//uint8_t pitch = nextByteFromBuffer();
			nextByteFromBuffer();
			sendOk();

		}else if(cmd == CMD_COMBINED_SIGNAL){
			uint8_t phone = nextByteFromBuffer();
			uint8_t pitch = nextByteFromBuffer();
			uint8_t intensity = nextByteFromBuffer();

			if(phone != 255){
				display->showText(FACE_VIBING);
				grid->enable(phone, intensity, pitch);
			}
			sendOk();

		}else if(cmd == CMD_STOP){
			grid->disableAll();
			doFlush = true;
			sendOk();

		}else if(cmd == CMD_SOUNDBITE){
			sendOk();
			lastPing = now;

		}else if(cmd == CMD_PLAY_BITE){
			sendOk();
			display->showText(FACE_VIBING);
			playBite(nextByteFromBuffer());
			doFlush = true;
			lastPing = millis();

		}else if(cmd == CMD_PING){
			lastPing = now;
			sendOk();

		}else{
			sprintf(msg, "Unknown command: 0x%02x", cmd);
			Logger::getGlobal()->debug(msg);
			strcpy(face, FACE_CONFUSED);
		}

		if(doFlush){
			flush();
		}
	}

	if(now - lastPing > 5000l){
		strcpy(face, FACE_LONELY);
	}

	if(everReceivedCommand){
		display->showText(face);
	}
}

void CommandStream::sendOk(){
	//stream->println("ok");
}

bool CommandStream::flushToLatestCommand(){
	if(stream->available() == 0){
		return false;
	}

	bufferIdx = 0;
	commandBuffer[0] = 255;

	while(stream->available() > 0){
		uint8_t header = readBlocking();
		if(header != CMD_HEADER){
			stream->print("out of sync "); stream->println(header);
			return false;
		}

		uint8_t cmd = readBlocking();
		commandBuffer[0] = cmd;

		for(int payloadIdx=0; payloadIdx<CMD_PAYLOAD_SIZES[cmd]; payloadIdx++){
			commandBuffer[payloadIdx+1] = readBlocking();
		}

		if(cmd == CMD_SOUNDBITE){
			bufferIdx = 1;
			uint8_t id = nextByteFromBuffer(); // dump the ID

			uint32_t period = 0;
			for(int i=0; i<4; i++){
				uint8_t b = nextByteFromBuffer();
				period += b << (i*8);
			}

			uint32_t sampleCount = 0;
			for(int i=0; i<4; i++){
				uint8_t b = nextByteFromBuffer();
				sampleCount += b << (i*8);
			}

			soundBite->init(period, sampleCount);
			for(int i=0; i<sampleCount; i++){
				if(i < MAX_SAMPLES){
					soundBite->samples[i].phone = readBlocking();
					soundBite->samples[i].pitch = readBlocking();
					soundBite->samples[i].intensity = readBlocking();
				}else{
					readBlocking();
					readBlocking();
					readBlocking();
				}
			}
		}
	}

	return true;
}

uint8_t CommandStream::readBlocking(){
	while(stream->available() == 0){}

	return stream->read();
}

void CommandStream::flush(){
	while(stream->available() > 0){
		stream->read();
	}
}

uint8_t CommandStream::nextByteFromBuffer(){
	if(bufferIdx >= MAX_CMD_SIZE){
		Logger::getGlobal()->error("BUFFER OVER");
		return 0;
	}else{
		return commandBuffer[bufferIdx++];
	}
}

void CommandStream::playBite(uint8_t id){
	long now = millis();
	long startTime = now;

	long sampleIdx = 0;
	Sample lastSample;
	lastSample.phone = 255;
	lastSample.pitch = 0;
	lastSample.intensity = 0;

	while(sampleIdx < soundBite->sampleCount){
		now = millis();

		long delta = now - startTime;
		sampleIdx = int(delta / soundBite->period);
		if(sampleIdx >= soundBite->sampleCount){
			break;
		}

		Sample sample = soundBite->samples[sampleIdx];

		if(sample != lastSample){
			if(sample.phone < 255 && sample.intensity > 0){
				grid->enable(sample.phone, sample.intensity, sample.pitch);
			}

			lastSample = sample;
		}
	}
	grid->disableAll();
}
