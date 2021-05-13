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
	1,
	2
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

	display->showText("\n    >  <\n   \\____/");

	bool doFlush = false;

	if(cmd == 255 || cmd == 0){
		// NOP
	}else if(cmd == CMD_CALIBRATE){
		grid->calibrate();
	}else if(cmd == CMD_CELL_ENABLE){
		byte cellID = nextByte();
		sprintf(msg, "%02d Enable", cellID);
		Logger::getGlobal()->debug(msg);

		grid->enable(cellID, 255, 0);
		doFlush = true;
	}else if(cmd == CMD_CELL_DISABLE){
		byte cellID = nextByte();
		sprintf(msg, "%02d Disable", cellID);
		Logger::getGlobal()->debug(msg);

		grid->disable(cellID);
		doFlush = true;
	}else if(cmd == CMD_SET_ACTUATOR_INT){
		byte actuatorID = nextByte();
		byte intensity = nextByte();

		grid->setActuatorIntensity(actuatorID, intensity);
		sprintf(msg, " %02d ON %03d ", actuatorID, intensity);
		display->showText(msg);
		doFlush = true;
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
		doFlush = true;
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

			//sprintf(msg, "S %d = % 3d % 3d % 3d", i, soundBites[id].samples[i].phone, soundBites[id].samples[i].pitch, soundBites[id].samples[i].intensity);
			//stream->println(msg);
		}
		stream->println("Bite received");

		//sprintf(msg, "S-Bite in  %03d samples %03d period", sampleCount, period);
		//Logger::getGlobal()->debug(msg);

	}else if(cmd == CMD_PLAY_BITE){
		stream->println("Play SoundBite");

		display->showText("\n    ^  ^\n   ~~~~~~");
		playBite(nextByte());
		display->showText("\n    O  O\n   \\____/");
		doFlush = true;
	}else{
		sprintf(msg, "??? %d", cmd);
		Logger::getGlobal()->debug(msg);
		display->showText("\n    ?  ?\n   ??????");
	}

	if(doFlush){
		flush();
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
//	int phoneList[255];
//	int phoneListIdx = 0;

	char msg[45];
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
//		delta *= 0.5f;
		sampleIdx = int(delta / soundBites[id].period);
		if(sampleIdx >= soundBites[id].sampleCount){
			break;
		}

		Sample sample = soundBites[id].samples[sampleIdx];
//		char msg[255];
//		sprintf(msg, "SAMPLE % 3d, % 3d, % 3d", sample.phone, sample.pitch, sample.intensity);
//		stream->println(msg);

		if(sample != lastSample){

			if(sample.phone != lastSample.phone){
				if(sample.phone != 255){
//					phoneList[phoneListIdx++] = sample.phone;
//					char msg[45] = "";
//					sprintf(msg, "Play clip\n% 3d\n% 3d", sample.phone, sample.intensity);
//					display->showText(msg);
//					stream->println(msg);
				}
			}

			if(sample.phone < 255 && sample.intensity > 0){
				grid->enable(sample.phone, sample.intensity, sample.pitch);
			}

			lastSample = sample;
		}
	}
	grid->disableAll();

/*
	for(int i=0; i<phoneListIdx; i++){
		sprintf(msg, "phones[%d] = %d", i, phoneList[i]);
		display->showText(msg);
		delay(1000);
	}
*/

//	sprintf(msg, "/SoundBite %d", id);
//	stream->println(msg);
}

/*
26  jh
39  eh
23  l
36  iy
0   b
36  iy
13  n

Jelly bean
*/