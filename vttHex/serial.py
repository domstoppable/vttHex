import time
import serial

from . import tools

CMD_HEADER           = 0x00
CMD_CALIBRATE        = 0x01
CMD_ACTUATOR_ENABLE  = 0x02
CMD_ACTUATOR_DISABLE = 0x03
CMD_BASE_FREQUENCY   = 0x04

phoneIndexLookup = {phone:idx for (idx,phone) in enumerate(tools.phoneLayout)}

class SerialComms():
	def __init__(self):
		self.sent = False

	def open(self, port, baud):
		self.serialObj = serial.Serial()
		self.serialObj.port = port
		self.serialObj.baudrate = baud

		self.serialObj.open()
		self.sendCalibrate()

	def sendCalibrate(self):
		msg = bytearray([CMD_HEADER, CMD_CALIBRATE, 255])
		self._send(msg)

	def sendPhoneState(self, phone, enabled):
		self.sendCellState(phoneIndexLookup[phone], enabled)

	def sendCellState(self, cellID, enabled):
		msg = bytearray([
			CMD_HEADER,
			CMD_ACTUATOR_ENABLE if enabled else CMD_ACTUATOR_DISABLE,
			cellID
		])
		self._send(msg)

		self.sent = True

	def _send(self, msg):
		print('Send:', msg)
		self.serialObj.write(msg)

	def readLines(self):
		lines = []
		while self.serialObj.inWaiting() > 0:
			lines.append(self.serialObj.readline().decode()[:-2])

		return lines
