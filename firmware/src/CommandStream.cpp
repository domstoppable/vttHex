#include "CommandStream.h"
#include "Logger.h"

uint8_t CMD_PAYLOAD_SIZES[NUM_COMMANDS] = {
	0,
	0,
	1,
	1,
	1,
	1,
	3,
	0,
	9,
	1
};

void CommandStream::update(){
	if(stream == nullptr){
		return;
	}

	if(!flushToLatestCommand()){
		return;
	}

	char msg[45];
	byte cmd = nextByte();

	if(cmd == 255 || cmd == 0){
		// NOP
	}else if(cmd == CMD_CALIBRATE){
		grid->calibrate();
	}else if(cmd == CMD_ACTUATOR_ENABLE){
		byte cellID = nextByte();
		sprintf(msg, "%02d Enable", cellID);
		Logger::getGlobal()->debug(msg);

		grid->enable(cellID, 255, 0);
	}else if(cmd == CMD_ACTUATOR_DISABLE){
		byte cellID = nextByte();
		sprintf(msg, "%02d Disable", cellID);
		Logger::getGlobal()->debug(msg);

		grid->disable(cellID);
	}else if(cmd == CMD_PITCH){
		byte pitch = nextByte();
		display->showText("Freq");
	}else if(cmd == CMD_COMBINED_SIGNAL){
		byte phone = nextByte();
		byte pitch = nextByte();
		byte intensity = nextByte();

		if(phone != 255){
			grid->enable(phone, intensity, pitch);
			sprintf(msg, " %02d ON     %03d Pitch  %03d Volume ", phone, pitch, intensity);
			display->showText(msg);
		}
	}else if(cmd == CMD_STOP){
		grid->disableAll();
		display->showText("");
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

		sprintf(msg, "S-Bite in  %03d samples %03d period", sampleCount, period);
		Logger::getGlobal()->debug(msg);

		soundBites[id].init(period, sampleCount);
		for(int i=0; i<sampleCount; i++){
			soundBites[id].samples[i].phone = readBlocking();
			soundBites[id].samples[i].pitch = readBlocking();
			soundBites[id].samples[i].intensity = readBlocking();
		}
		stream->println("Bite received");
	}else if(cmd == CMD_PLAY_BITE){
		stream->println("Play SoundBite");
		display->showText("Play clip");
		playBite(nextByte());
	}else{
		Logger::getGlobal()->debug("???");
		stream->println(cmd);
	}
}

bool CommandStream::flushToLatestCommand(){
	if(stream->available() == 0){
		return false;
	}

	bufferIdx = 0;
	commandBuffer[0] = 255;
	int commands = 0;
	while(stream->available() > 0){
		byte header = readBlocking();
		if(header != CMD_HEADER){
			stream->print("out of sync "); stream->println(header);
			return false;
		}

		byte cmd = readBlocking();
		if(cmd > NUM_COMMANDS){
			stream->print("Unknown command "); stream->println(cmd);
			return false;
		}

		commandBuffer[0] = cmd;
		for(int payloadIdx=0; payloadIdx<CMD_PAYLOAD_SIZES[cmd]; payloadIdx++){
			commandBuffer[payloadIdx+1] = readBlocking();
		}
		commands++;
		if(cmd == CMD_SOUNDBITE){
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
	char msg[45];
	long startTime = millis();
	long now = startTime;

	long sampleIdx = 0;
	Sample lastSample;
	while(sampleIdx < soundBites[id].sampleCount){
		long delta = millis() - startTime;
		sampleIdx = int(delta / soundBites[id].period);

		Sample sample = soundBites[id].samples[sampleIdx];
		if(sample != lastSample){
			grid->enable(sample.phone, sample.intensity, sample.pitch);

			/*
			sprintf(msg, " %02d ON     %03d Pitch  %03d Volume ", sample.phone, sample.pitch, sample.intensity);
			display->showText(msg);
			*/
			lastSample = sample;
		}
	}
	grid->disableAll();

	sprintf(msg, "/SoundBite %d", id);
	stream->println(msg);
}