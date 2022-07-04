import struct
import pathlib

from . import tools
from . import serial

fixedHeaderFormat = '3s' # magic bytes
fixedHeaderFormat += 'B' # file format version
fixedHeaderFormat += 'I' # flags (no WAV)
fixedHeaderFormat += 'I' # size of written text
fixedHeaderFormat += 'I' # size of phonetic text
fixedHeaderFormat += 'I' # sample count
fixedHeaderFormat += 'I' # sample period

fixedHeaderFields = ('magicBytes', 'version', 'flags', 'writtenTextSize', 'phoneticTextSize', 'sampleCount', 'samplePeriod')
sampleFields = ('phone', 'pitch', 'intensity')

class VTTFile:
	def __init__(self, fileVersion, flags, samplePeriod, writtenText, phoneticText, rawSamples, filepath=None):
		self.fileVersion = fileVersion
		self.flags = flags
		self.samplePeriod = samplePeriod
		self.writtenText = writtenText
		self.phoneticText = phoneticText
		self.sampleCount = int(len(rawSamples)/3)
		self.samples = rawSamples
		self.filepath = filepath

		self.sampleDicts = None

	def getSamplesAsDicts(self):
		if self.sampleDicts is None:
			self.sampleDicts = []
			for idx in range(0, len(self.samples), 3):
				self.sampleDicts.append(dict(zip(sampleFields, self.samples[idx:idx+3])))

		return self.sampleDicts

	def getPhoneticSampleString(self):
		phones = self.getPhoneticSamples()
		result = ''
		lastPhone = None
		silencePhone = '·'
		for phoneIdx in phones:
			if phoneIdx < len(tools.phoneLayout):
				phone = tools.phoneLayout[phoneIdx]
			else:
				phone = silencePhone

			if phone == lastPhone and phone != silencePhone:
				result += '='
			else:
				result += phone

			lastPhone = phone

		return result

	def getDuration(self):
		return self.sampleCount * self.samplePeriod

	def getPhoneticSamples(self):
		return [x['phone'] for x in self.getSamplesAsDicts()]

	def getPitchSamples(self):
		return [x['pitch'] for x in self.getSamplesAsDicts()]

	def getIntensitySamples(self):
		return [x['intensity'] for x in self.getSamplesAsDicts()]

	def __repr__(self):
		return f'<{self.__class__.__name__}({self.filepath})'

class StructBuffer:
	def __init__(self, bytes):
		self.buffer = bytes
		self.pointer = 0

	def read(self, format, fieldNames=None):
		data = struct.unpack_from(format, self.buffer, self.pointer)
		self.pointer += struct.calcsize(format)

		if fieldNames is not None:
			data = dict(zip(fieldNames, data))

		return data

def loadVTTBytes(bytes):
	buffer = StructBuffer(bytes)

	header = buffer.read(fixedHeaderFormat, fixedHeaderFields)
	writtenText = buffer.read(f'{header["writtenTextSize"]}s')[0].decode('ascii')
	phoneticText = buffer.read(f'{header["phoneticTextSize"]}s')[0].decode('ascii')

	sampleBytes = buffer.read(f'{3*header["sampleCount"]}B')

	return VTTFile(
		header['version'],
		header['flags'],
		header['samplePeriod'],
		writtenText,
		phoneticText,
		sampleBytes
	)

def loadVTTFile(filename):
	filepath = pathlib.Path(filename)
	bytes = filepath.read_bytes()
	vtt = loadVTTBytes(bytes)
	vtt.filepath = filepath

	return vtt

if __name__ == '__main__':
	import sys
	import argparse
	import time

	parser = argparse.ArgumentParser()
	parser.add_argument('--device')
	parser.add_argument('vtt_files', nargs='+')

	args = parser.parse_args()

	device = None
	if args.device is not None:
		device = serial.SerialComms()
		device.open(args.device)

	for filename in args.vtt_files:
		vttFile = loadVTTFile(filename)
		print(f'{filename}')
		print(f'	File version  : {vttFile.fileVersion}')
		print(f'	Flags         : {vttFile.flags}')
		print(f'	Sample count  : {len(vttFile.samples)}')
		print(f'	Sample period : {vttFile.samplePeriod}')
		print(f'	Written text  : {vttFile.writtenText}')
		print(f'	Phonetic text : {vttFile.phoneticText}')
		print(f'	Preview       : {vttFile.getPhoneticSampleString()}')

		if args.device is not None:
			duration = vttFile.getDuration() / 1000
			samples = [vttFile.samples[i:i+3] for i in range(0, len(vttFile.samples), 3)]
			print('Sending', filename, 'to', args.device, '...')

			device.sendFile(vttFile.samplePeriod, samples)
			time.sleep(duration/2)
			print('Play', filename)
			device.sendPlayBite()

			time.sleep(duration + .25)

			#print('Received:')
			#for line in device.readLines():
			#	print(line)
