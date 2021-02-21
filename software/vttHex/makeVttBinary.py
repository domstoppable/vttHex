import sys, os
import pathlib
from praatio import tgio
import csv
import wave
import struct
import math
import audioop
from tqdm import tqdm

from vttHex.tools import SignalPlayer, formatSignalAsBytes


'''
Format
	Header
		Byte      Description
		0:2       VTT
		3         File format version
		4         Flags
                      b00000001 = WAV included
		5:9       # bytes for written text
		10:14     # bytes for phonetic transcription
		15:19     # sample count
		20        Sample period (in ms)
	Data
		21:x      written text
		x+1:y     phonetic transcription
		y+1:z     samples
					phone, pitch, intensity
		z+1:END   WAV file
'''

# run with python3 makeVttBinary ./*.wav
# expects .wav, .f0.csv, in same folder, .TextGrid in `grids/` subfolder

#def asSequence(phoneSeries, pitchSeries, intensitySeries, period):
#	while not (phoneSeries.isDone() or pitchSeries.isDone() or intensitySeries.isDone()):
#		yield update(period)

def makeVttBinary(inFile):
	inFile = pathlib.Path(inFile)
	folder = inFile.parent

	name = inFile.stem
	#progressBar.set_description(name)

	# check for constituent files
	wavFile = inFile
	pitchFile = pathlib.Path(folder/(name+'.f0.csv'))
	textGridFile = pathlib.Path(folder/'grids'/(name+'.TextGrid'))

	filesOk = True
	for f in [wavFile, pitchFile, textGridFile]:
		if not f.exists():
			print('Missing constituent file:', f)
			filesOk = False

	if not filesOk:
		return

	# Load text data
	tg = tgio.openTextgrid(str(textGridFile))
	transcriptions = { 'written': '', 'phonetic': ''}
	for tierName in ['words', 'phones']:
		intervals = tg.tierDict[tierName].entryList
		textParts = [interval.label for interval in intervals]
		transcriptions[tierName] = ' '.join(textParts)

	# Load time-series data
	period = 1 # milliseconds

	signalPlayer = SignalPlayer()
	signalPlayer.open(name, folder)
	samples = signalPlayer.asSequence(period/1000)
	samplesAsBytes = [formatSignalAsBytes(a,b,c) for a,b,c in samples]
	flattendSamples = [y for x in samplesAsBytes for y in x]

	# Pack data
	wordCharCount = len(transcriptions['words'])
	phoneCharCount = len(transcriptions['phones'])
	sampleByteCount = len(flattendSamples)

	structFormat = '3s'                         # magic bytes
	structFormat += 'B'                         # file format version
	structFormat += 'I'                         # flags (no WAV)
	structFormat += 'I'                         # size of written text
	structFormat += 'I'                         # size of phonetic text
	structFormat += 'I'                         # sample count
	structFormat += 'I'                         # sample period
	structFormat += str(wordCharCount) + 's'    # written text
	structFormat += str(phoneCharCount) + 's'   # phonetic text
	structFormat += str(sampleByteCount) + 'B'  # samples

	data = [
		b'VTT',                                 # magic bytes
		0x0,                                    # file format version
		0x0,                                    # flags (no WAV)
		len(transcriptions['words']),           # size of written text
		len(transcriptions['phones']),          # size of phonetic text
		int(sampleByteCount/3),                 # sample count
		period,                                 # sample period
		transcriptions['words'].encode(),       # written text
		transcriptions['phones'].encode(),      # phonetic text
		*flattendSamples                        # samples
	]

	packedData = struct.pack(structFormat, *data)

	# Write file
	with open(name + '.vtt', 'wb') as outputFile:
		outputFile.write(packedData)


if __name__ == '__main__':
	from multiprocessing import Pool

	with Pool() as pool:
		pool.map(makeVttBinary, sys.argv[1:])
