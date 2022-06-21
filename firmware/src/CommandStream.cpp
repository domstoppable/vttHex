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
		byte cmd = nextByte();

		bool doFlush = false;

		if(cmd == 255 || cmd == 0){
			// NOP
		}else if(cmd == CMD_CALIBRATE){
			grid->calibrate();
			sendOk();

		}else if(cmd == CMD_CELL_ENABLE){
			byte cellID = nextByte();
			sprintf(msg, "%02d Enable", cellID);
			Logger::getGlobal()->debug(msg);

			grid->enable(cellID, 255, 0);
			doFlush = true;
			sendOk();

		}else if(cmd == CMD_CELL_DISABLE){
			byte cellID = nextByte();
			sprintf(msg, "%02d Disable", cellID);
			Logger::getGlobal()->debug(msg);

			grid->disable(cellID);
			doFlush = true;
			sendOk();

		}else if(cmd == CMD_PULSE_ACTUATOR){
			sendOk();

			byte actuatorID = nextByte();

			display->showText(FACE_VIBING);
			long startTime = now;
			long duration = 500l;
			while(now-startTime < duration){
				now = millis();
				float elapsed = (float)(now-startTime)/(float)duration;
				elapsed = min(max(elapsed, 0.0f), 1.0f);
				byte intensity = 255*(1.0f-abs(elapsed*2.0f - 1.0f));
				grid->setActuatorIntensity(actuatorID, intensity);
			}

			doFlush = true;

		}else if(cmd == CMD_SET_ACTUATOR_INT){
			byte actuatorID = nextByte();
			byte intensity = nextByte();

			grid->setActuatorIntensity(actuatorID, intensity);
			if(intensity > 0){
				strcpy(face, FACE_VIBING);
			}
			doFlush = true;
			sendOk();

		}else if(cmd == CMD_PITCH){
			//@TODO: implement pitch changing
			//byte pitch = nextByte();
			nextByte();
			sendOk();

		}else if(cmd == CMD_COMBINED_SIGNAL){
			byte phone = nextByte();
			byte pitch = nextByte();
			byte intensity = nextByte();

			if(phone != 255){
				display->showText("\n    ^  ^\n   ~~~~~~");
				grid->enable(phone, intensity, pitch);
			}
			sendOk();

		}else if(cmd == CMD_STOP){
			grid->disableAll();
			doFlush = true;
			sendOk();

		}else if(cmd == CMD_SOUNDBITE){
			uint8_t id = nextByte();

			uint32_t period = 0;
			for(int i=0; i<4; i++){
				uint8_t b = nextByte();
				period += b << (i*8);
			}

			uint32_t sampleCount = 0;
			for(int i=0; i<4; i++){
				uint8_t b = nextByte();
				sampleCount += b << (i*8);
			}

			soundBites[id].init(period, sampleCount);
			for(int i=0; i<sampleCount; i++){
				soundBites[id].samples[i].phone = readBlocking();
				soundBites[id].samples[i].pitch = readBlocking();
				soundBites[id].samples[i].intensity = readBlocking();
			}
			sendOk();

		}else if(cmd == CMD_PLAY_BITE){
			sendOk();
			display->showText(FACE_VIBING);
			playBite(nextByte());
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

	if(now - lastPing > 1000l){
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
		byte header = readBlocking();
		if(header != CMD_HEADER){
			stream->print("out of sync "); stream->println(header);
			return false;
		}

		byte cmd = readBlocking();
		commandBuffer[0] = cmd;
		for(int payloadIdx=0; payloadIdx<CMD_PAYLOAD_SIZES[cmd]; payloadIdx++){
			commandBuffer[payloadIdx+1] = readBlocking();
		}

		if(cmd == CMD_SOUNDBITE){
			// return now so that calling function can read the rest of the soundbite
			// @TODO: move that logic into here?
			return true;
		}
	}

	return true;
}

byte CommandStream::readBlocking(){
	while(stream->available() == 0){}

	return stream->read();
}

void CommandStream::flush(){
	while(stream->available() > 0){
		stream->read();
	}
}

byte CommandStream::nextByte(){
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

	while(sampleIdx < soundBites[id].sampleCount){
		now = millis();

		long delta = now - startTime;
		sampleIdx = int(delta / soundBites[id].period);
		if(sampleIdx >= soundBites[id].sampleCount){
			break;
		}

		Sample sample = soundBites[id].samples[sampleIdx];

		if(sample != lastSample){
			if(sample.phone < 255 && sample.intensity > 0){
				grid->enable(sample.phone, sample.intensity, sample.pitch);
			}

			lastSample = sample;
		}
	}
	grid->disableAll();
}
