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
		self.phonePlayerTimer = QtCore.QTimer()
		self.phonePlayerTimer.setInterval(0)
		self.phonePlayerTimer.timeout.connect(self.updatePhonePlayer)

		self.serialTimer = QtCore.QTimer()
		self.serialTimer.setInterval(15)
		self.serialTimer.timeout.connect(self.checkForSerialMessages)

		self.phonePlayer = tools.PhonePlayer()
		self.lastTimestamp = None
		self.enabledPhone = None
		self.serial = None

	def startSerial(self):
		self.serial = serial.SerialComms()
		self.serial.open('/dev/ttyUSB0', 115200)
		self.serialTimer.start()

	def exec(self):
		self.window.show()
		self.startSerial()
		super().exec_()

	def buildWindow(self):
		window = ui.load('main.ui')
		window.mboppControls.playClicked.connect(self.onPlayClicked)
		window.phoneGrid.tilePressed.connect(self.onTilePressed)
		window.phoneGrid.tileReleased.connect(self.onTileReleased)

		self.window = window

	def onPlayClicked(self, filename):
		print('Play:', filename)

		self.gridPath = f'MBOPP/audio/{filename}.TextGrid'
		self.wavPath = f'MBOPP/audio/{filename}.wav'
		self.phonePlayer.open(tools.findAsset(self.gridPath))
		self.nowPlaying = QtMultimedia.QSound(tools.findAsset(self.wavPath))
		QtCore.QTimer.singleShot(500, self.startPlaying)

	def startPlaying(self):
		self.startPhonePlayer()
		self.nowPlaying.play()

	def togglePhone(self, phone, enabled=True):
		if self.enabledPhone is not None:
			self.window.phoneGrid.setPhoneEnabled(self.enabledPhone, False)
			self.serial.sendPhoneState(self.enabledPhone, False)

		if phone is not None and phone not in ['sp', 'si']:
			if self.serial is not None:
				self.serial.sendPhoneState(phone, enabled)

			self.window.phoneGrid.setPhoneEnabled(phone, enabled)
			self.enabledPhone = phone if enabled else None
		else:
			self.enabledPhone = None

	def startPhonePlayer(self):
		self.lastTimestamp = None
		self.phonePlayerTimer.start()
		self.startTime = time.time()

	def stopPhonePlayer(self):
		self.phonePlayerTimer.stop()
		self.togglePhone(None)

	def checkForSerialMessages(self):
		lines = self.serial.readLines()
		for l in lines:
			print('RECV:', l)

	def updatePhonePlayer(self):
		now = time.time()
		if self.lastTimestamp is None:
			self.lastTimestamp = now
			return

		delta = now - self.lastTimestamp
		actions = self.phonePlayer.update(delta)
		for action in actions:
			if action is None:
				self.stopPhonePlayer()
			else:
				self.togglePhone(action['phone'], action['enable'])

		self.lastTimestamp = now

	def onTilePressed(self, cellID):
		self.serial.sendCellState(cellID, True)
		print('Pressed', cellID)

	def onTileReleased(self, cellID):
		self.serial.sendCellState(cellID, False)
		print('Released', cellID)

def run():
	app = VttHexApp()
	app.exec()

if __name__ == '__main__':
	run()
