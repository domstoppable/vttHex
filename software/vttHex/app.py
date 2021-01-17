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

		self.paramChangeTimer = QtCore.QTimer()
		self.paramChangeTimer.setInterval(250)
		self.paramChangeTimer.setSingleShot(True)
		self.paramChangeTimer.timeout.connect(self.uploadSoundBite)

		self.useBites = True
		self.lastCellID = None
		self.stopIntensityTimer = QtCore.QTimer()
		self.stopIntensityTimer.setSingleShot(True)
		self.stopIntensityTimer.setInterval(1000)
		self.stopIntensityTimer.timeout.connect(self.onTileReleased)


	def startSerial(self, useTCP=False):
		if not useTCP:
			self.serial = serial.SerialComms()
			try:
				self.serial.open('/dev/ttyUSB0')
				self.serialTimer.start()
			except Exception as exc:
				print(exc)
		else:
			self.serial = serial.TcpComms()
			try:
				self.serial.open('192.168.0.107', 1234)
				self.serialTimer.start()
			except Exception as exc:
				print(exc)

	def exec(self):
		self.window.show()
		self.startSerial()
		self.paramChangeTimer.start()
		super().exec_()

	def buildWindow(self):
		window = ui.load('main.ui')
		window.mboppControls.playClicked.connect(self.onPlayClicked)
		window.mboppControls.parametersChanged.connect(self.onParametersChanged)
		window.phoneGrid.tilePressed.connect(self.onTilePressed)
		window.phoneGrid.tileReleased.connect(self.onTileReleased)

		window.pitchSliders.setText('Pitch')
		window.pitchSliders.setRange(1, 1000)
		window.pitchSliders.linearValueChanged.connect(self.onIntensitySliderChanged)

		window.intensitySliders.setText('Intensity')
		window.intensitySliders.setRange(0, 100)
		window.intensitySliders.linearValueChanged.connect(self.onIntensitySliderChanged)

		self.window = window

	def onIntensitySliderChanged(self, value):
		if self.lastCellID is not None:
			self.onTilePressed(self.lastCellID)
			self.stopIntensityTimer.start()


	def onParametersChanged(self, filename):
		self.paramChangeTimer.start()

	def uploadSoundBite(self):
		filename = self.window.mboppControls.getFilename()
		wavPath = f'MBOPP/audio/{filename}.wav'
		self.nowPlaying = QtMultimedia.QSound(tools.findAsset(wavPath))

		self.signalPlayer.open(filename)

		if self.useBites:
			print('Upload:', filename)
			samples = list(self.signalPlayer.asSequence(period=.005))
			self.serial.sendFile(5, samples)

	def onPlayClicked(self):
		self.nowPlaying.play()
		self.startSignalPlayer()

		if self.useBites:
			self.serial.sendPlayBite()

	def startSignalPlayer(self):
		self.lastTimestamp = None
		self.signalPlayer.reset()
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

		if self.signalPlayer.isDone():
			self.stopSignalPlayer()
		else:
			self.showSignal(phone, pitch, intensity)
			if not self.useBites:
				self.serial.sendCombinedSignal(phone, pitch[0], intensity)

		self.lastTimestamp = now

	def showSignal(self, phone, pitch, intensity):
		if phone is not None:
			self.window.phoneGrid.setSinglePhone(phone)
		self.window.pitchSliders.setLinearValue(int(pitch[0]))
		self.window.intensitySliders.setLinearValue(int(intensity*100))

	def onTilePressed(self, cellID):
		self.lastCellID = cellID
		self.serial.sendCombinedSignal(
			cellID,
			self.window.pitchSliders.getLinearValue(),
			self.window.intensitySliders.getLinearValue()/100
		)

	def onTileReleased(self, cellID=None, phone=None):
		self.serial.sendStop()

def run():
	app = VttHexApp()
	app.exec()

if __name__ == '__main__':
	run()
