import time
from pathlib import Path

from PySide2 import QtCore, QtWidgets, QtGui, QtMultimedia

from . import ui
from . import tools
from . import mbopp_data
from . import serial

class VttHexApp(QtWidgets.QApplication):
	def __init__(self):
		super().__init__()
		self.buildWindow()
		self.signalPlayerTimer = QtCore.QTimer()
		self.signalPlayerTimer.setInterval(5)
		self.signalPlayerTimer.timeout.connect(self.updateSignalPlayer)

		self.serialTimer = QtCore.QTimer()
		self.serialTimer.setInterval(15)
		self.serialTimer.timeout.connect(self.checkForSerialMessages)

		self.signalPlayer = tools.SignalPlayer()
		self.lastTimestamp = None
		self.enabledPhone = None
		self.serial = None

	def startSerial(self):
		self.serial = serial.SerialComms()
		try:
			self.serial.open('/dev/ttyUSB0')
			self.serialTimer.start()
		except Exception as exc:
			print(exc)

	def exec(self):
		self.window.show()
		self.startSerial()
		super().exec_()

	def buildWindow(self):
		window = ui.load('main.ui')
		window.mboppControls.playClicked.connect(self.onPlayClicked)
		window.mboppControls.uploadClicked.connect(self.onUploadClicked)
		window.phoneGrid.tilePressed.connect(self.onTilePressed)
		window.phoneGrid.tileReleased.connect(self.onTileReleased)

		window.pitchSliders.setText('Pitch')
		window.pitchSliders.setRange(1, 1000)

		window.intensitySliders.setText('Intensity')
		window.intensitySliders.setRange(0, 100)

		self.window = window

	def onUploadClicked(self, filename):
		print('Play:', filename)

		wavPath = f'MBOPP/audio/{filename}.wav'
		gridPath = f'MBOPP/audio/{filename}.TextGrid'
		pitchPath = f'MBOPP/audio/{filename}.f0.csv'

		self.signalPlayer.open(filename)
		samples = list(self.signalPlayer.asSequence(period=.005))
		self.serial.sendFile(5, samples)

		self.nowPlaying = QtMultimedia.QSound(tools.findAsset(wavPath))

	def onPlayClicked(self):
		self.nowPlaying.play()
		self.serial.sendPlayBite()

	def startPlaying(self):
		self.startSignalPlayer()
		self.nowPlaying.play()

	def startSignalPlayer(self):
		self.lastTimestamp = None
		self.signalPlayerTimer.start()
		self.startTime = time.time()

	def stopSignalPlayer(self):
		self.signalPlayerTimer.stop()

		self.window.phoneGrid.clear()
		self.window.intensitySliders.setLinearValue(0)
		self.serial.sendStop()

	def checkForSerialMessages(self):
		lines = self.serial.readLines()
		for l in lines:
			print('RECV:', l)

	def updateSignalPlayer(self):
		now = time.time()
		if self.lastTimestamp is None:
			self.lastTimestamp = now
			return

		delta = now - self.lastTimestamp
		signal = self.signalPlayer.update(delta)
		(phone, pitch, intensity) = signal

		if phone is None:
			self.stopSignalPlayer()
		else:
			self.showSignal(phone, pitch, intensity)
			self.serial.sendCombinedSignal(phone, pitch[0], intensity)

		self.lastTimestamp = now

	def showSignal(self, phone, pitch, intensity):
		self.window.phoneGrid.setSinglePhone(phone)
		self.window.pitchSliders.setLinearValue(int(pitch[0]))
		self.window.intensitySliders.setLinearValue(int(intensity*100))

	def onTilePressed(self, cellID, phone):
		self.serial.sendCombinedSignal(
			cellID,
			self.window.pitchSliders.getLinearValue(),
			self.window.intensitySliders.getLinearValue()/100
		)

	def onTileReleased(self, cellID, phone):
		self.serial.sendStop()

def run():
	app = VttHexApp()
	app.exec()

if __name__ == '__main__':
	run()
