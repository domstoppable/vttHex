import time
import serial

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

phoneIndexLookup = {phone:idx for (idx,phone) in enumerate(tools.phoneLayout)}

minIntensity = 200

class SerialComms():
	def open(self, port, baud=115200):
		self.serialObj = serial.Serial()
		self.serialObj.port = port
		self.serialObj.baudrate = baud

		self.serialObj.open()
		self.lastCombination = (0,0,0)

	def sendFile(self, period, samples):
		lenAsBytes = len(samples).to_bytes(length=2, byteorder='little')
		msg = bytearray([ CMD_HEADER, CMD_SOUNDBITE, period, *lenAsBytes ])
		self._send(msg)
		for sample in samples:
			sampleAsBytes = self._formatSignalAsBytes(sample[0], sample[1][0], sample[2])

			self._send(sampleAsBytes)

	def sendPlayBite(self):
		msg = bytearray([ CMD_HEADER, CMD_PLAY_BITE ])
		self._send(msg)

	def sendCalibrate(self):
		msg = bytearray([CMD_HEADER, CMD_CALIBRATE])
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

	def sendCombinedSignal(self, phoneOrCellID, pitch, intensity):
		thisCombo = (phoneOrCellID, pitch, intensity)
		if self.lastCombination == thisCombo:
			return
		else:
			self.lastCombination = thisCombo

		msg = bytearray([
			CMD_HEADER,
			CMD_COMBINED_SIGNAL,
			*self._formatSignalAsBytes(phoneOrCellID, pitch, intensity)
		])
		self._send(msg)

	def _formatSignalAsBytes(self, phoneOrCellID, pitch, intensity):
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

		pitch = int(255 * (pitch / 1000))
		intensity = int((255-minIntensity) * intensity + minIntensity)

		return bytearray([ cellID, pitch, intensity ])

	def sendStop(self):
		self.lastCombination = (0,0,0)
		msg = bytearray([
			CMD_HEADER,
			CMD_STOP,
		])
		self._send(msg)

	def _send(self, msg):
		try:
			self.serialObj.write(msg)
		except Exception as exc:
			print('EXCEPTION', exc)

	def readLines(self):
		lines = []
		while self.serialObj.inWaiting() > 0:
			lines.append(self.serialObj.readline().decode()[:-2])

		return lines

def bytesToReadable(byteArray):
	readable = ''
	for i in range(len(byteArray)):
		readable += byteArray[i:i+1].hex() + ' '

	return readable[:-1]
