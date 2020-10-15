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
	tilePressed = QtCore.Signal(int, str)
	tileReleased = QtCore.Signal(int, str)

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
		if isinstance(child, QtWidgets.QPushButton):
			self.connectButtonSignals(child, len(self.tiles)-1)

	def connectButtonSignals(self, button, id):
		button.pressed.connect(
			partial(self.tilePressed.emit, id, button.text())
		)

		button.released.connect(
			partial(self.tileReleased.emit, id, button.text())
		)

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
	pressed = QtCore.Signal(str)

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
		self.lastPhone = None

	def setPhoneEnabled(self, phone, enabled):
		phone = phone[:2]
		if phone in self.buttons:
			self.buttons[phone].setActive(enabled)

	def setSinglePhone(self, phone):
		if self.lastPhone is not None:
			self.setPhoneEnabled(self.lastPhone, False)

		self.setPhoneEnabled(phone, True)
		self.lastPhone = phone

	def clear(self):
		if self.lastPhone is not None:
			self.setPhoneEnabled(self.lastPhone, False)

class MBOPPControls(QtWidgets.QWidget):
	parametersChanged = QtCore.Signal(str)
	playClicked = QtCore.Signal()

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

		self.form.phraseSelector.currentTextChanged.connect(self._onParametersChanged)

		self.form.focusButton.clicked.connect(self._onProsodyTypeChanged)
		self.form.phraseButton.clicked.connect(self._onProsodyTypeChanged)

		self.form.pitchButton.clicked.connect(self._onConditionTypeChanged)
		self.form.pitchAndTimeButton.clicked.connect(self._onConditionTypeChanged)
		self.form.timeButton.clicked.connect(self._onConditionTypeChanged)

		self.form.pitchSlider.valueChanged.connect(self._onPitchChanged)
		self.form.timeSlider.valueChanged.connect(self._onTimeChanged)

		self.form.playButton.clicked.connect(self._onPlayClicked)

	def getProsodyType(self):
		if self.form.focusButton.isChecked():
			return 'focus'
		elif self.form.phraseButton.isChecked():
			return 'phrase'

	def getConditionMode(self):
		if self.form.pitchButton.isChecked():
			return 'pitch'
		if self.form.pitchAndTimeButton.isChecked():
			return 'combined'
		if self.form.timeButton.isChecked():
			return 'time'

	def isValid(self):
		prosodyType = self.getProsodyType()
		phrase = self.form.phraseSelector.currentText()
		pitch = self.form.pitchSlider.value()
		time = self.form.timeSlider.value()

		return not None in (prosodyType, phrase, pitch, time)

	def getFilename(self):
		prosodyType = self.getProsodyType()
		pitch = self.form.pitchSlider.value()
		time = self.form.timeSlider.value()

		sentenceInfo = self.form.phraseSelector.currentData()
		if sentenceInfo is None:
			return None

		return sentenceInfo['filename'].format(pitch=pitch, time=time)

	def _onParametersChanged(self):
		self.parametersChanged.emit(self.getFilename())

	def _onPlayClicked(self):
		self.playClicked.emit()

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

		self._onParametersChanged()

	def _onProsodyTypeChanged(self):
		self.form.phraseSelector.clear()

		if self.getProsodyType() == 'focus':
			for sentence in mbopp_data.focusSentences:
				self.form.phraseSelector.addItem(sentence['ID'] + ' - ' + sentence['desc'], sentence)
		elif self.getProsodyType() == 'phrase':
			for sentence in mbopp_data.phraseSentences:
				self.form.phraseSelector.addItem(sentence['ID'] + ' - ' + sentence['desc'], sentence)

		self._onParametersChanged()

	def _onPitchChanged(self, pitch):
		if self.form.pitchSlider.isEnabled():
			pitch = findClosest(pitch, self.increments)
			if self.form.pitchSlider.value() != pitch:
				self.form.pitchSlider.setValue(pitch)

			if self.getConditionMode() == 'combined':
				if self.form.timeSlider.value() != pitch:
					self.form.timeSlider.setValue(pitch)

		self._onParametersChanged()

	def _onTimeChanged(self, time):
		if self.form.timeSlider.isEnabled():
			time = findClosest(time, self.increments)
			if self.form.timeSlider.value() != time:
				self.form.timeSlider.setValue(time)

			if self.getConditionMode() == 'combined':
				if self.form.pitchSlider.value() != time:
					self.form.pitchSlider.setValue(time)

		self._onParametersChanged()

def log(x):
	return math.log(x)

def exp(x):
	return math.exp(x)
	return 10**x

class LinearLogSliders(QtWidgets.QWidget):
	linearValueChanged = QtCore.Signal(int)

	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self.setLayout(QtWidgets.QGridLayout())

		self.titleLabel = QtWidgets.QLabel('-', self)
		self.layout().addWidget(self.titleLabel, 0, 0, 1, -1, QtCore.Qt.AlignHCenter)
		self.layout().addWidget(QtWidgets.QLabel('Linear', self), 1, 0, 1, 1, QtCore.Qt.AlignHCenter)
		self.layout().addWidget(QtWidgets.QLabel('Log', self), 1, 1, 1, 1, QtCore.Qt.AlignHCenter)

		self.linearSlider = QtWidgets.QSlider(self)
		self.logSlider = QtWidgets.QSlider(self)

		self.layout().addWidget(self.linearSlider, 2, 0, 1, 1)
		self.layout().addWidget(self.logSlider, 2, 1, 1, 1)

		self.linearSlider.sliderMoved.connect(self.onLinearSliderMoved)
		self.logSlider.sliderMoved.connect(self.onLogSliderMoved)

	def setText(self, text):
		self.titleLabel.setText(text)

	def onLinearSliderMoved(self, value):
		self.linearValueChanged.emit(value)
		self.logSlider.setValue(100*log(value+1))

	def onLogSliderMoved(self, value):
		self.linearSlider.setValue(exp(value/100))

	def setRange(self, minimum, maximum):
		self.linearSlider.setMinimum(minimum)
		self.logSlider.setMinimum(int(log(minimum+1)*100))

		self.linearSlider.setMaximum(maximum)
		self.logSlider.setMaximum(math.ceil(log(maximum)*100))

	def setLinearValue(self, value):
		self.linearSlider.setValue(value)
		self.logSlider.setValue(100*log(value+1))

	def getLinearValue(self):
		return self.linearSlider.value()

	def getNormalizedLinearValue(self):
		valueRange = self.linearSlider.maximum() - self.linearSlider.minimum()
		return (self.linearSlider.value() - self.linearSlider.minimum()) / valueRange

loader.registerCustomWidget(HexGrid)
loader.registerCustomWidget(PhoneGrid)
loader.registerCustomWidget(MBOPPControls)
loader.registerCustomWidget(LinearLogSliders)

def load(uiFile):
	return loader.load(tools.findAsset(uiFile))


if __name__ == '__main__':
	app = QtWidgets.QApplication()
	w = MBOPPControls()
	w.show()
	app.exec_()

