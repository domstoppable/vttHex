import time
from pathlib import Path

from PySide2 import QtCore, QtWidgets, QtGui, QtMultimedia

from . import ui
from . import tools
from . import mbopp_data
from . import serial

actuatorCells = {
	0: 0,
	1: 2,
	2: 4,
	3: 13,
	4: 15,
	5: 17,
	6: 24,
	7: 26,
	8: 28,
	9: 37,
	10: 39,
	11: 41,
}

class ThresholdsController():
	def __init__(self):
		super().__init__()
		self.buildWindow()

		self.serialTimer = QtCore.QTimer()
		self.serialTimer.setInterval(15)
		self.serialTimer.timeout.connect(self.checkForSerialMessages)

		self.serial = None

		self.actuatorReleaseTimer = QtCore.QTimer()
		self.actuatorReleaseTimer.setInterval(2000)
		self.actuatorReleaseTimer.timeout.connect(self.stopActuator)

	def start(self):
		self.window.show()
		self.startSerial()

	def startSerial(self):
		self.serial = serial.SerialComms()
		try:
			self.serial.open('/dev/ttyUSB0')
			self.serialTimer.start()
		except Exception as exc:
			print(exc)

	def buildWindow(self):
		window = QtWidgets.QWidget()
		window.setLayout(QtWidgets.QGridLayout())
		self.sliders = []

		for row in range(4):
			for column in range(3):
				actuatorID = row*3 + column
				slider = QtWidgets.QSlider(window)
				slider.setMaximum(255)
				slider.setTickPosition(slider.TickPosition.TicksBothSides)
				slider.valueChanged.connect(self._bindCallback(self.onSliderValueChanged, slider, actuatorID))

				window.layout().addWidget(slider, row, column*2+(row%2))
				self.sliders.append(slider)

		self.window = window

	def checkForSerialMessages(self):
		lines = self.serial.readLines()
		for l in lines:
			print('RECV:', l)

	def _bindCallback(self, func, *args, **kwargs):
		def callback(*cbArgs, **cbKwargs):
			return func(*args, *cbArgs, **kwargs, **cbKwargs)

		return callback

	def onSliderValueChanged(self, slider, actuatorID, value):
		cellID = actuatorCells[actuatorID]
		print('Sending', cellID, 0, value)
		self.serial.sendCombinedSignal(cellID, 0, value)
		self.actuatorReleaseTimer.start()

	def stopActuator(self):
		self.serial.sendStop()

def run():
	app = QtWidgets.QApplication()
	controller = ThresholdsController()
	controller.start()
	app.exec_()

if __name__ == '__main__':
	run()
