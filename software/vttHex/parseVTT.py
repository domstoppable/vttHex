import struct
import pathlib
import tools

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
	def __init__(self, fileVersion, flags, samplePeriod, writtenText, phoneticText, rawSamples):
		self.fileVersion = fileVersion
		self.flags = flags
		self.samplePeriod = samplePeriod
		self.writtenText = writtenText
		self.phoneticText = phoneticText
		self.samples = []
		for idx in range(0, len(rawSamples), 3):
			self.samples.append(dict(zip(sampleFields, rawSamples[idx:idx+3])))

	def getPhoneticSampleString(self):
		phones = self.getPhoneticSamples()
		result = ''
		lastPhone = None
		for phoneIdx in phones:
			if phoneIdx < len(tools.phoneLayout):
				phone = tools.phoneLayout[phoneIdx]
			else:
				phone = ' '

			if phone == lastPhone and lastPhone != ' ':
				result += '-'
			else:
				result += phone

			lastPhone = phone

		return result.strip()

	def getPhoneticSamples(self):
		return [x['phone'] for x in self.samples]

	def getPitchSamples(self):
		return [x['pitch'] for x in self.samples]

	def getIntensitySamples(self):
		return [x['intensity'] for x in self.samples]


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
	bytes = pathlib.Path(filename).read_bytes()
	return loadVTTBytes(bytes)




if __name__ == '__main__':
	import sys
	vttFile = loadVTTFile(sys.argv[1])

	print(f'File version  : {vttFile.fileVersion}')
	print(f'Flags         : {vttFile.flags}')
	print(f'Sample count  : {len(vttFile.samples)}')
	print(f'Sample period : {vttFile.samplePeriod}')
	print(f'Written text  : {vttFile.writtenText}')
	print(f'Phonetic text : {vttFile.phoneticText}')
	print(f'Preview       : {vttFile.getPhoneticSampleString()}')
