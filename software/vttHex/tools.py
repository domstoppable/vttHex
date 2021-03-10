import sys
import pkg_resources
import math

phoneLayout = ['B', 'D', 'G', 'HH', 'DH', None, 'P', 'T', 'K', 'TH', 'F', None, 'M', 'N', 'SH', 'S', 'V', 'W', 'Y', 'NG', 'CH', 'ZH', 'Z', 'L', 'R', 'ER', 'JH', 'AH', 'AO', 'AA', 'AW', 'UW', 'UH', 'OW', 'OY', 'AX', 'IY', 'EY', 'IH', 'EH', 'AE', 'AY', ]
vowels = ['AA','AE','AH','AO','AW','AY','EH','ER','EY','IY','OW','OY']

phoneIndexLookup = {phone:idx for (idx,phone) in enumerate(phoneLayout)}


def mel(f):
	# O’Shaughnessy, D. (1987). Speech Communication: Human and Machine. Addison-Wesley Publishing Company.
	return 1127 * math.log(1+(f/700))

def deMel(m):
	# O’Shaughnessy, D. (1987). Speech Communication: Human and Machine. Addison-Wesley Publishing Company.
	return 700 * (math.exp(m/1127) - 1)

pitchMinHz = 30
pitchMaxHz = 260
pitchMinMel = mel(pitchMinHz)
pitchMaxMel = mel(pitchMaxHz)

def findAsset(*resourceParts):
	resource = '/'.join(['assets'] + list(resourceParts))
	return pkg_resources.resource_filename(__name__, resource)

class TimeData:
	def __init__(self, t, data):
		self.time = t
		self.data = data

class TimeSeries:
	def __init__(self, data=None):
		if data is None:
			self.records = []
		else:
			self.records = data

		self.idx = 0
		self.accumulatedTime = 0

	def addData(self, timestamp, data):
		self.records.append(TimeData(timestamp, data))

	def update(self, delta):
		self.accumulatedTime += delta

		done = False
		actions = []

		while self.idx < len(self.records)-1 and self.accumulatedTime >= self.records[self.idx+1].time:
			self.idx += 1

		return self.records[self.idx]

	def isDone(self):
		return self.idx >= len(self.records)-1

	def reset(self):
		self.idx = 0
		self.accumulatedTime = 0

class SignalPlayer():
	def open(self, filename, folder=None):
		from praatio import tgio

		if folder is None:
			textGridFile = findAsset(f'MBOPP/audio/grids/{filename}.TextGrid')
			pitchFile = findAsset(f'MBOPP/audio/{filename}.f0.csv')
			loudnessFile = findAsset(f'MBOPP/audio/{filename}.loudness.csv')
			wavFile = findAsset(f'MBOPP/audio/{filename}.wav')
			if not wavFile.exists():
				wavFile = findAsset(f'MBOPP/audio/{filename}.WAV')
		else:
			textGridFile = folder/'grids'/(filename + '.TextGrid')
			pitchFile = folder/(filename + '.f0.csv')
			loudnessFile = folder/(filename + '.loudness.csv')
			wavFile = folder/(filename + '.wav')
			if not wavFile.exists():
				wavFile = folder/(filename + '.WAV')

		textgrid = tgio.openTextgrid(textGridFile)

		phonegrid = textgrid.tierDict['phones'].entryList
		self.phoneSeries = TimeSeries()
		for phoneRecord in phonegrid:
			(start, stop, label) = phoneRecord
			self.phoneSeries.addData(start, label)
		self.phoneSeries.addData(stop, None)

		self.pitchSeries = TimeSeries()
		with open(pitchFile) as csvFile:
			for line in csvFile.readlines():
				(timestamp, pitch, confidence) = [float(x) for x in line.split('   ')]
				self.pitchSeries.addData(timestamp, (pitch, confidence))

		self.intensitySeries = TimeSeries()
		with open(loudnessFile) as csvFile:
			for idx,line in enumerate(csvFile.readlines()):
				if idx == 0:
					continue
				(timestamp, loudness) = [float(x) for x in line.split(',')]
				self.intensitySeries.addData(timestamp, loudness)

	def reset(self):
		self.phoneSeries.reset()
		self.pitchSeries.reset()
		self.intensitySeries.reset()

	def update(self, delta):
		phone = self.phoneSeries.update(delta).data
		pitch = self.pitchSeries.update(delta).data
		intensity = self.intensitySeries.update(delta).data

		return [phone, pitch, intensity]

	def isDone(self):
		return self.phoneSeries.isDone() and self.pitchSeries.isDone() and self.intensitySeries.isDone()

	def asSequence(self, period):
		yield(self.update(0))
		while not (self.phoneSeries.isDone() or self.pitchSeries.isDone() or self.intensitySeries.isDone()):
			yield self.update(period)

def formatSignalAsBytes(phoneOrCellID, pitch, intensity):
	if isinstance(phoneOrCellID, str):
		phoneOrCellID = phoneOrCellID[:2]
		if phoneOrCellID in phoneIndexLookup:
			cellID = phoneIndexLookup[phoneOrCellID[:2]]
		else:
			cellID = 255
	elif phoneOrCellID is None:
		cellID = 255
	else:
		cellID = phoneOrCellID

	if isinstance(pitch, tuple):
		pitch = pitch[0]

	# clamp pitch to 30-260 Hz
	pitch = max(pitchMinHz, min(pitchMaxHz, pitch))
	# convert to mel
	pitch = mel(pitch)
	# normalize range to 0-1
	pitch = (pitch-pitchMinMel)/(pitchMaxMel-pitchMinMel)
	# convert to byte
	pitch = int(pitch*255)
	# and clamp
	pitch = max(0, min(255, pitch))


	intensity = int(255*min(50, intensity)/50)

	return bytearray([ cellID, pitch, intensity ])
