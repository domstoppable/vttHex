import sys
import pkg_resources
import wave, audioop
import math

from praatio import tgio

phoneLayout = ['B', 'D', 'G', 'HH', 'DH', None, 'P', 'T', 'K', 'TH', 'F', None, 'M', 'N', 'SH', 'S', 'V', 'W', 'Y', 'NG', 'CH', 'ZH', 'Z', 'L', 'R', 'ER', 'JH', 'AH', 'AO', 'AA', 'AW', 'UW', 'UH', 'OW', 'OY', 'AX', 'IY', 'EY', 'IH', 'EH', 'AE', 'AY', ]
vowels = ['AA','AE','AH','AO','AW','AY','EH','ER','EY','IY','OW','OY']

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

		while self.idx < len(self.records)-1 and self.accumulatedTime >= self.records[self.idx].time:
			self.idx += 1

		return self.records[self.idx]

	def isDone(self):
		return self.idx >= len(self.records)-1

	def reset(self):
		self.idx = 0
		self.accumulatedTime = 0

class SignalPlayer():
	def open(self, filename):
		textGridFile = findAsset(f'MBOPP/audio/{filename}.TextGrid')
		textgrid = tgio.openTextgrid(textGridFile)

		phonegrid = textgrid.tierDict['phones'].entryList
		self.phoneSeries = TimeSeries()
		for phoneRecord in phonegrid:
			(start, stop, label) = phoneRecord
			self.phoneSeries.addData(start, label)
		self.phoneSeries.addData(stop, None)

		pitchFile = findAsset(f'MBOPP/audio/{filename}.f0.csv')
		self.pitchSeries = TimeSeries()
		with open(pitchFile) as csvFile:
			for line in csvFile.readlines():
				(timestamp, pitch, confidence) = [float(x) for x in line.split('   ')]
				self.pitchSeries.addData(timestamp, (pitch, confidence))

		windowSize = 0.050
		wavFile = findAsset(f'MBOPP/audio/{filename}.wav')
		wav = wave.open(wavFile)
		if wav.getsampwidth() == 2:
			zero = 0
			maxValue = 2**15
		else:
			zero = 128
			maxValue = 255

		frames = wav.readframes(wav.getnframes())
		framesPerWindow = int(wav.getframerate() * windowSize * wav.getsampwidth())

		pad = zero.to_bytes(length=wav.getsampwidth(), byteorder='little') * math.ceil(framesPerWindow/4)
		paddedFrames = pad + frames + pad

		self.intensitySeries = TimeSeries()
		samples = int(len(frames)/2)
		for i in range(samples):
			start = i*2
			window = paddedFrames[start:start+framesPerWindow]
			intensity = audioop.rms(window, wav.getsampwidth())
			intensity /= maxValue

			self.intensitySeries.addData(i*(1/wav.getframerate()), intensity)

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
		while not (self.phoneSeries.isDone() or self.pitchSeries.isDone() or self.intensitySeries.isDone()):
			yield self.update(period)
