import math
from functools import partial

from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtUiTools import QUiLoader, loadUiType

from . import tools
from . import mbopp_data

loader = QUiLoader()
loader.setWorkingDirectory(tools.findAsset('.'))

def findClosest(value, values):
	closestValue = None
	minDistance = None

	for v in values:
		distance = abs(value - v)
		if minDistance is None or distance < minDistance:
			minDistance = distance
			closestValue = v

	return closestValue

class HexTile(QtWidgets.QWidget):
	def __init__(self, child, parent=None):
		super().__init__(parent=parent)

		self.polygon = QtGui.QPolygonF()
		self.child = child

		if child is not None:
			self.child.setParent(self)

	def makeHex(self, radiusAdjust=0):
		scale = [
			self.width()/2 + radiusAdjust,
			self.height()/2 + radiusAdjust - 1.5,
		]
		points = []
		for i in range(6):
			angle = i * math.tau / 6
			x = self.width()/2 + math.sin(angle) * scale[0]
			y = self.height()/2 + math.cos(angle) * scale[1]

			points.append(QtCore.QPoint(x, y))

		return QtGui.QPolygon(points)

	def resizeEvent(self, event):
		self.setMask(QtGui.QRegion(self.makeHex()))
		if self.child is not None:
			self.child.resize(self.size())

class HexGrid(QtWidgets.QWidget):
	def __init__(self, parent=None, rows=3, columns=3):
		super().__init__(parent=parent)

		self.tiles = []

		self.rowCount = rows
		self.colCount = columns

	def resizeEvent(self, event):
		self.tileWidth = self.width() / (self.colCount+.5)
		self.tileHeight = (self.height() / self.rowCount)

		scale = [self.tileWidth/2, self.tileHeight/2]

		for i,child in enumerate(self.tiles):
			if child is None:
				continue

			r = int(i/self.colCount)
			c = i % self.colCount

			child.resize(self.tileWidth, self.tileHeight)
			center = self.getCenter(r, c)
			child.move(
				center[0] - child.width()/2,
				center[1] - child.height()/2
			)

	def paintEvent(self, event):
		painter = QtGui.QPainter(self)
		pen = painter.pen()
		pen.setWidth(3)

		hexShape = None
		for i,hexTile in enumerate(self.tiles):
			if hexTile.child is None:
				continue

			r = int(i/self.colCount)
			c = i % self.colCount

			'''
			if i in [0,2,4,13,15,17,24,26,28,37,39,41]:
				pen.setWidth(7)
			else:
				pen.setWidth(2)
			painter.setPen(pen)
			'''

			center = self.getCenter(r, c)
			if hexShape is None:
				hexShape = hexTile.makeHex(2)

			painter.translate(center[0] - self.tileWidth/2, center[1]- self.tileHeight/2)
			painter.drawPolygon(hexShape)
			painter.resetTransform()

	def getCenter(self, r, c):
		return (2-r%2)*self.tileWidth/2 + c*self.tileWidth, (.5+r)*self.tileHeight

	def addWidget(self, child):
		self.tiles.append(HexTile(child, self))

class PhoneButton(QtWidgets.QPushButton):
	def __init__(self, phone, parent=None):
		super().__init__(phone, parent)
		self.phone = phone
		self.highlightColor = QtGui.QColor(0, 200, 200)
		self.setActive = self.setDown

	def paintEvent(self, event):
		super().paintEvent(event)

		if self.isDown():
			painter = QtGui.QPainter(self)

			radius = 50

			pen = painter.pen()
			pen.setWidth(10)
			pen.setColor(self.highlightColor)
			painter.setPen(pen)
			painter.drawEllipse(
				(self.width()-radius)/2, (self.height()-radius)/2,
				radius, radius
			)

class PhoneGrid(HexGrid):
	pressed = QtCore.Signal(object)

	def __init__(self, parent=None):
		columns = 6
		super().__init__(parent=parent, rows=math.ceil(len(tools.phoneLayout) / columns), columns=columns)

		self.buttons = {}
		for phone in tools.phoneLayout:
			button = PhoneButton(phone, self)
			button.pressed.connect(partial(self.pressed.emit, phone))

			self.buttons[phone] = button
			self.addWidget(button)

		self.resize(700, 650)

	def setPhoneEnabled(self, phone, enabled):
		self.buttons[phone].setActive(enabled)

class MBOPPControls(QtWidgets.QWidget):
	playClicked = QtCore.Signal(str)

	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self.form = load('MBOPP/mbopp.ui')
		self.setLayout(QtWidgets.QHBoxLayout())
		self.layout().addWidget(self.form)
		self.form.setParent(self)

		self.increments = list(range(0, 101, 5))
		for x in [45, 50, 55]:
			self.increments.remove(x)

		self._onProsodyTypeChanged()

		self.form.focusButton.clicked.connect(self._onProsodyTypeChanged)
		self.form.phraseButton.clicked.connect(self._onProsodyTypeChanged)

		self.form.pitchButton.clicked.connect(self._onConditionTypeChanged)
		self.form.pitchAndTimeButton.clicked.connect(self._onConditionTypeChanged)
		self.form.timeButton.clicked.connect(self._onConditionTypeChanged)

		self.form.pitchSlider.valueChanged.connect(self._onPitchChanged)
		self.form.timeSlider.valueChanged.connect(self._onTimeChanged)

		self.form.playButton.clicked.connect(self._onPlayClicked)

	def _onPlayClicked(self):
		prosodyType = self.getProsodyType()
		pitch = self.form.pitchSlider.value()
		time = self.form.timeSlider.value()

		sentenceInfo = self.form.phraseSelector.currentData()
		filename = sentenceInfo['filename'].format(pitch=pitch, time=time)
		self.playClicked.emit(filename)

	def getConditionMode(self):
		if self.form.pitchButton.isChecked():
			return 'pitch'
		if self.form.pitchAndTimeButton.isChecked():
			return 'combined'
		if self.form.timeButton.isChecked():
			return 'time'

	def _onConditionTypeChanged(self):
		mode = self.getConditionMode()

		self.form.pitchSlider.setEnabled(mode in ('pitch', 'combined'))
		self.form.timeSlider.setEnabled(mode in ('time', 'combined'))

		if not self.form.pitchSlider.isEnabled():
			self.form.pitchSlider.setValue(50)
		else:
			self._onPitchChanged(self.form.pitchSlider.value())

		if not self.form.timeSlider.isEnabled():
			self.form.timeSlider.setValue(50)
		else:
			self._onTimeChanged(self.form.timeSlider.value())

		if mode == 'combined':
			self.form.timeSlider.setValue(self.form.pitchSlider.value())

	def _onProsodyTypeChanged(self):
		self.form.phraseSelector.clear()

		if self.getProsodyType() == 'focus':
			for sentence in mbopp_data.focusSentences:
				self.form.phraseSelector.addItem(sentence['ID'] + ' - ' + sentence['desc'], sentence)
		elif self.getProsodyType() == 'phrase':
			for sentence in mbopp_data.phraseSentences:
				self.form.phraseSelector.addItem(sentence['ID'] + ' - ' + sentence['desc'], sentence)

	def getProsodyType(self):
		if self.form.focusButton.isChecked():
			return 'focus'
		elif self.form.phraseButton.isChecked():
			return 'phrase'

	def _onPitchChanged(self, pitch):
		if self.form.pitchSlider.isEnabled():
			pitch = findClosest(pitch, self.increments)
			self.form.pitchSlider.setValue(pitch)

			if self.getConditionMode() == 'combined':
				self.form.timeSlider.setValue(pitch)

	def _onTimeChanged(self, time):
		if self.form.timeSlider.isEnabled():
			time = findClosest(time, self.increments)
			self.form.timeSlider.setValue(time)

			if self.getConditionMode() == 'combined':
				self.form.pitchSlider.setValue(time)

	def isValid(self):
		prosodyType = self.getProsodyType()
		phrase = self.form.phraseSelector.currentText()
		pitch = self.form.pitchSlider.value()
		time = self.form.timeSlider.value()

		return not None in (prosodyType, phrase, pitch, time)

loader.registerCustomWidget(HexGrid)
loader.registerCustomWidget(PhoneGrid)
loader.registerCustomWidget(MBOPPControls)

def load(uiFile):
	return loader.load(tools.findAsset(uiFile))


if __name__ == '__main__':
	def onPress(phone):
		print('Pressed:', phone)

	app = QtWidgets.QApplication()
	#w = PhoneGrid([None] + list('abcdefghijklmnopqrstuvwxyzasdfasdf'))
	#w.pressed.connect(onPress)
	#w.show()

	def onPlay(*args):
		print('Play', *args)
	w = MBOPPControls()
	w.playClicked.connect(onPlay)
	w.show()
	app.exec_()

