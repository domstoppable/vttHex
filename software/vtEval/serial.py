from enum import IntEnum

from PySide2 import QtCore, QtSerialPort
from vttHex.parseVTT import loadVTTFile, VTTFile

class SerialCommand(IntEnum):
	HEADER           = 0x00
	CALIBRATE        = 0x01
	ACTUATOR_ENABLE  = 0x02
	ACTUATOR_DISABLE = 0x03
	PITCH            = 0x04
	INTENSITY        = 0x05
	COMBINED_SIGNAL  = 0x06
	STOP             = 0x07
	SOUNDBITE        = 0x08
	PLAY_BITE        = 0x09

preferredDevice = {
	'vendorID': 4292,
	'productID': 60000
}

def getPortInfoByLocation(systemLocation):
	for p in availablePorts():
		if p.systemLocation() == systemLocation:
			return p

def availablePorts():
	return [SerialInfo(d) for d in QtSerialPort.QSerialPortInfo.availablePorts()]

class SerialInfo(QtSerialPort.QSerialPortInfo):
	def isPreferred(self):
		isPreferredVendor = self.vendorIdentifier() == preferredDevice['vendorID']
		isPreferredProduct = self.productIdentifier() == preferredDevice['productID']

		return isPreferredVendor and isPreferredProduct

	def __repr__(self):
		return f'{self.manufacturer()} - {self.description()} [{self.portName()}]'

def formatPacket_PlayBite(soundBiteID=0):
	return bytearray([ SerialCommand.HEADER, SerialCommand.PLAY_BITE, soundBiteID ])

def formatPacket_SoundBite(vttFile, soundBiteID=0):
	if not isinstance(vttFile, VTTFile):
		vttFile = loadVTTFile(filename)

	lenAsBytes = vttFile.sampleCount.to_bytes(length=4, byteorder='little')
	periodAsBytes = vttFile.samplePeriod.to_bytes(length=4, byteorder='little')

	return bytearray([
		SerialCommand.HEADER, SerialCommand.SOUNDBITE,
		soundBiteID,
		*periodAsBytes, *lenAsBytes,
		*vttFile.samples
	])

class SerialError(Exception):
	def __init__(self, message, qtError):
		super().__init__(message)
		self.qtError = qtError

class SerialDevice():
	def __init__(self, pathOrSerialInfo):
		if not isinstance(pathOrSerialInfo, SerialInfo):
			pathOrSerialInfo = getPortInfoByLocation(pathOrSerialInfo)

		self.port = QtSerialPort.QSerialPort(pathOrSerialInfo)
		self.port.setBaudRate(115200)

	def open(self):
		return self.port.open(QtCore.QIODevice.ReadWrite)

	def close(self):
		self.port.close()

	def playFile(self, vttFile):
		self.send(formatPacket_SoundBite(vttFile))
		self.send(formatPacket_PlayBite())

	def sendFile(self, vttFile):
		self.send(formatPacket_SoundBite(vttFile))

	def play(self):
		self.send(formatPacket_PlayBite())

	def send(self, bytes):
		if not self.port.isOpen():
			self.open()
			if self.port.error() != QtSerialPort.QSerialPort.SerialPortError.NoError:
				raise SerialError('Failed to open port', self.port.error())

		print(f'Send {len(bytes)} bytes', bytes[:32], '...' if len(bytes) > 32 else '')
		self.port.write(bytes)
		if self.port.error() != QtSerialPort.QSerialPort.SerialPortError.NoError:
			raise SerialError('Failed to write to port', self.port.error())
