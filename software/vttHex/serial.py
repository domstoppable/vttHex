import time
import serial
import socket

from . import tools

CMD_HEADER           = 0x00
CMD_CALIBRATE        = 0x01
CMD_ACTUATOR_ENABLE  = 0x02
CMD_ACTUATOR_DISABLE = 0x03
CMD_PITCH            = 0x04
CMD_INTENSITY        = 0x05
CMD_COMBINED_SIGNAL  = 0x06
CMD_STOP             = 0x07
CMD_SOUNDBITE        = 0x08
CMD_PLAY_BITE        = 0x09

minIntensity = 144

class StreamComms():
	def __init__(self, stream=None):
		self.lastCombination = (0,0,0)
		self.stream = stream

	def sendFile(self, period, samples):
		lenAsBytes = len(samples).to_bytes(length=2, byteorder='little')
		msg = bytearray([ CMD_HEADER, CMD_SOUNDBITE, period, *lenAsBytes ])
		self._send(msg)
		for sample in samples:
			sampleAsBytes = tools.formatSignalAsBytes(sample[0], sample[1][0], sample[2])

			self._send(sampleAsBytes)

	def sendPlayBite(self):
		msg = bytearray([ CMD_HEADER, CMD_PLAY_BITE ])
		self._send(msg)

	def sendCalibrate(self):
		msg = bytearray([CMD_HEADER, CMD_CALIBRATE])
		self._send(msg)

	def sendPhoneState(self, phone, enabled):
		self.sendCellState(tools.phoneIndexLookup[phone], enabled)

	def sendCellState(self, cellID, enabled):
		msg = bytearray([
			CMD_HEADER,
			CMD_ACTUATOR_ENABLE if enabled else CMD_ACTUATOR_DISABLE,
			cellID
		])
		self._send(msg)

	def sendCombinedSignal(self, phoneOrCellID, pitch, intensity):
		thisCombo = (phoneOrCellID, pitch, intensity)
		if self.lastCombination == thisCombo:
			return
		else:
			self.lastCombination = thisCombo

		msg = bytearray([
			CMD_HEADER,
			CMD_COMBINED_SIGNAL,
			*tools.formatSignalAsBytes(phoneOrCellID, pitch, intensity)
		])
		self._send(msg)

	def sendStop(self):
		self.lastCombination = (0,0,0)
		msg = bytearray([
			CMD_HEADER,
			CMD_STOP,
		])
		self._send(msg)

	def _send(self, msg):
		try:
			self.stream.write(msg)
		except Exception as exc:
			print('EXCEPTION', exc)

	def readLines(self):
		lines = []
		while self.stream.inWaiting() > 0:
			lines.append(self.stream.readline().decode()[:-2])

		return lines

class SerialComms(StreamComms):
	def open(self, port, baud=115200):
		self.serialObj = serial.Serial()
		self.serialObj.port = port
		self.serialObj.baudrate = baud
		self.serialObj.open()

		self.stream = self.serialObj

class TcpComms(SerialComms):
	def open(self, host, port=1234):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((host, port))
		self.socket.setblocking(False)

		self.stream = self.socket

	def readLines(self):
		return []

	def _send(self, msg):
		try:
			self.stream.sendall(msg)
		except Exception as exc:
			print('EXCEPTION', exc)




def bytesToReadable(byteArray):
	readable = ''
	for i in range(len(byteArray)):
		readable += byteArray[i:i+1].hex() + ' '

	return readable[:-1]
