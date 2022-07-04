import pickle
import sys
import datetime
from pathlib import Path
import csv
import random
import re
import logging

from PySide2 import QtCore, QtGui, QtWidgets, QtMultimedia, QtMultimediaWidgets

from universal_gamepad.eventDaemon import getGamepadDaemon
from universal_gamepad.gamepad import Button

import argparse
import argparseqt.gui

from . import serial
from .asset import locateAsset
from .ui import SerialSelector
from vttHex.parseVTT import loadVTTFile

unserializableClasses = [
	QtCore.QObject,
	QtCore.SignalInstance,
	QtMultimedia.QSoundEffect
]

gamepadButtonMap = {
	Button.SOUTH: QtCore.Qt.Key_Space,

	Button.UP: QtCore.Qt.Key_W,
	Button.LEFT: QtCore.Qt.Key_A,
	Button.DOWN: QtCore.Qt.Key_S,
	Button.RIGHT: QtCore.Qt.Key_D,
}

def isSerializable(value):
	if isinstance(value, list):
		for subValue in value:
			if not isSerializable(subValue):
				return False
		else:
			return True

	for class_ in unserializableClasses:
		if isinstance(value, class_):
			return False

	return True

def nowStamp(safeChars=False):
	now = datetime.datetime.now()
	now = now.strftime('%Y-%m-%dT%H:%M:%S') + ('-%03d' % (now.microsecond / 1000))

	if safeChars:
		now = now.replace(':', '_')

	return now

class VtEvalApp():
	def __init__(self, appName):
		self.app = QtWidgets.QApplication()
		self.app.setApplicationName(appName)
		self.app.aboutToQuit.connect(self.onAboutToQuit)
		self.app.setStyleSheet('''
			* {
				font-size: 18pt;
			}
			QAbstractButton:focus {
				background-color: #4444cc;
				color: #eee;
			}
			QAbstractButton:disabled {
				background-color: #888;
			}
		''')

		self.currentStateWidget = None
		self.arguments = {}
		self.widgetStack = []

		self.window = QtWidgets.QWidget()
		self.window.setLayout(QtWidgets.QVBoxLayout())
		self.window.setContentsMargins(100, 50, 100, 50)

		self.lastInstructionsScreen = None

		self.progressBar = QtWidgets.QProgressBar()
		self.window.layout().addWidget(self.progressBar)

		self.dataLogger = None
		self.device = None
		self.serialErrorWidget = SerialErrorWidget()
		self.serialErrorWidget.finished.connect(self.resumeFromSerialError)
		self.serialErrorWidget.deviceSelected.connect(self.connectNewDevice)

		self.gamepadDaemon = getGamepadDaemon()
		self.gamepadDaemon.gamepadConnected.connect(self.useGamepad)

	def useGamepad(self, gamepad):
		self.gamepad = gamepad
		gamepad.buttonPressed.connect(self.onGamepadButtonPressed)
		gamepad.buttonReleased.connect(self.onGamepadButtonReleased)

	def onGamepadButtonPressed(self, button):
		if button in gamepadButtonMap:
			focusedWidget = self.app.focusWidget()
			if focusedWidget is not None:
				key = gamepadButtonMap[button]
				event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, key, QtCore.Qt.NoModifier)

				self.app.postEvent(focusedWidget, event)

	def onGamepadButtonReleased(self, button):
		if button in gamepadButtonMap:
			focusedWidget = self.app.focusWidget()
			if focusedWidget is not None:
				key = gamepadButtonMap[button]
				event = QtGui.QKeyEvent(QtCore.QEvent.KeyRelease, key, QtCore.Qt.NoModifier)

				self.app.postEvent(focusedWidget, event)

	def initialize(self, arguments):
		raise Exception(f'{self.app.applicationName()} is not configured!')

	def onStarted(self):
		self.progressBar.setMaximum(len(self.widgetStack))
		self.popNextState()

	def onAboutToQuit(self):
		if self.dataLogger is not None:
			self.dataLogger.close()

	def onStateWidgetFinished(self, finishedWidget):
		try:
			finishedWidget.finished.disconnect(self.onStateWidgetFinished)
		except:
			pass

		if self.dataLogger is not None:
			self.dataLogger.logWidgetCompletion(finishedWidget)

		self.saveState()

		if len(self.widgetStack) > 0:
			self.popNextState()
		else:
			self.onStackEmptied()

	def onStackEmptied(self):
		self.app.exit()

	def popNextState(self):
		progressValue = self.progressBar.maximum() - len(self.widgetStack) + 1
		self.progressBar.setValue(progressValue)
		logging.info(f'Progress at {progressValue}/{self.progressBar.maximum()}')

		if isinstance(self.currentStateWidget, InstructionsScreen):
			self.lastInstructionsScreen = self.currentStateWidget

		while self.window.layout().count() > 1:
			widget = self.window.layout().takeAt(1).widget()
			widget.setParent(None)

		self.currentStateWidget = self.widgetStack.pop(0)
		self.window.layout().addWidget(self.currentStateWidget)
		self.currentStateWidget.finished.connect(lambda: self.onStateWidgetFinished(self.currentStateWidget))

		logging.info(f'Current widget = {self.currentStateWidget}')

		try:
			self.device.ping()
		except Exception as exc:
			self.handleSerialError()
			return

		self.currentStateWidget.onStarted()

	def parseArgs(self):
		parser = argparse.ArgumentParser(description=self.app.applicationName())

		parser.add_argument('--facilitator', type=str)
		parser.add_argument('--pid', type=str)
		parser.add_argument('--condition', type=str)
		parser.add_argument('--device', type=str)
		parser.add_argument('--simulate', action='store_true')

		self.arguments = argparseqt.groupingTools.parseIntoGroups(parser)

		if None in self.arguments.values():
			dialog = argparseqt.gui.ArgDialog(parser)
			dialog.setValues(self.arguments)
			dialog.exec_()

			if dialog.result() == QtWidgets.QDialog.Accepted:
				self.arguments = dialog.getValues()
			else:
				sys.exit(1)

	def execute(self):
		self.parseArgs()

		self.device = serial.SerialDevice(self.arguments['device'])

		self.startDataLogger()
		self.startLogger()

		if self.openState():
			logging.warning(f'Resuming from saved state {self.getSaveStatePath()}')

			if self.lastInstructionsScreen is None:
				restoredText = 'Wnen you are ready, the evaluation will immediately resume from where you left off.'
			else:
				self.widgetStack.insert(0, self.lastInstructionsScreen)
				restoredText = 'The last instructions you saw will be repeated on the next screen.'

			self.widgetStack.insert(0, ButtonPromptWidget(name='restore', text=f'<center>Your session has been restored!<br/><br/>{restoredText}<br/><br/><p style="font-size: 10pt">State file: <span style="font-family: \'Courier New\', Courier, monospace;">{self.getSaveStatePath()}</span></p></center>'))

			for widget in self.widgetStack:
				if hasattr(widget, 'stimulusBraced'):
					widget.stimulusBraced.connect(self.prepareStimulus)

				if hasattr(widget, 'stimulusTriggered'):
					widget.stimulusTriggered.connect(self.playStimulus)

		else:
			logging.info(f'Starting fresh')
			self.initialize(self.arguments)
			self.widgetStack.append(KeyPromptWidget(name='finished', text='<center>You are finished!<br/><br/>Please let the facilitator know.</center>', dismissKey=QtCore.Qt.Key_F4))

		for idx,widget in enumerate(self.widgetStack):
			logging.info(f'self.widgetStack[{idx}] = {widget}')

		self.window.showFullScreen()
		QtCore.QTimer.singleShot(0, self.onStarted)

		if self.arguments['simulate']:
			self.simulate()
		else:
			self.gamepadDaemon.start()
			self.app.exec_()

			logging.info(f'Eval ended with {len(self.widgetStack)} item(s) left')

	def startLogger(self):
		logDir = 'data/executionLogs'
		Path(logDir).mkdir(exist_ok=True)
		logPath = f'{logDir}/{self.dataLogger.baseFilename}.log'
		print(f'Starting log at {logPath}')

		logging.basicConfig(
			filename=logPath,
			encoding='utf-8',
			format='[{asctime}][{levelname:^8}][{filename:>16}:{lineno:<4}] {message}',
			style='{',
			level=logging.DEBUG
		)
		logging.info(f'Log started at = {logPath}')
		logging.info(f'Data log path  = {self.dataLogger.path}')

	def connectNewDevice(self, device):
		logging.info(f'Connect to {device}')

		self.device = serial.SerialDevice(device)
		if self.device.open():
			self.serialErrorWidget.enableButton()
			logging.info(f'Connection to {device} ok')
		else:
			self.serialErrorWidget.showError('Could not connect to device.')

	def handleSerialError(self):
		if self.serialErrorWidget.isVisible():
			return

		self.serialErrorWidget.showFullScreen()
		self.serialErrorWidget.reset()

	def resumeFromSerialError(self):
		self.serialErrorWidget.hide()
		self.currentStateWidget.onStarted()

	def prepareStimulus(self, stimulus):
		try:
			self.device.sendFile(stimulus.vtt)
		except Exception as exc:
			self.handleSerialError()

	def playStimulus(self, stimulus):
		try:
			self.device.play()
		except Exception as exc:
			self.handleSerialError()

	def openState(self):
		stateFilePath = self.getSaveStatePath()
		if stateFilePath.exists():
			state = pickle.load(stateFilePath.open('rb'))
			for key,value in state.items():
				self.__dict__[key] = value

			return True

		return False

	def saveState(self):
		stateFilePath = self.getSaveStatePath()
		if not stateFilePath.parent.exists():
			stateFilePath.parent.mkdir(exist_ok=True)

		if len(self.widgetStack) < 2:
			stateFilePath.unlink()
		else:
			state = {
				'widgetStack': self.widgetStack,
				'lastInstructionsScreen': self.lastInstructionsScreen
			}

			try:
				logging.info(f'Saving state to {stateFilePath}')
				tmpStateFilePath = (stateFilePath.parent/'tmp')
				tmpStateFile = tmpStateFilePath.open('wb')

				pickle.dump(state, tmpStateFile)
				tmpStateFile.close()

				tmpStateFilePath.replace(stateFilePath)

				logging.info(f'State saved!')
			except Exception as exc:
				logging.error(f'Failed to save state {exc}')
				try:
					tmpStateFilePath.unlink() # the file is junked, toss it
				except:
					pass

	def getSaveStatePath(self):
		evalType = self.app.applicationName().split()[0].lower()
		nameBits = [self.arguments['pid'], self.arguments['condition'], evalType]
		return Path(f'states/' + '_'.join(nameBits) + '.savestate')

class SerialErrorWidget(QtWidgets.QWidget):
	finished = QtCore.Signal()
	deviceSelected = QtCore.Signal(object)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowModality(QtCore.Qt.ApplicationModal)

		self.contents = QtWidgets.QWidget()
		self.contents.setLayout(QtWidgets.QVBoxLayout())
		self.contents.layout().setSpacing(50)
		self.contents.layout().addWidget(QtWidgets.QLabel('<h1 style="color: #900"><center>Device error!</center></h1>', self))
		self.contents.layout().addWidget(QtWidgets.QLabel('<center>There was an error communicating with the device. Please alert the researcher!</center>', self))

		self.serialSelector = SerialSelector(self)
		self.serialSelector.selectionChanged.connect(self.onDeviceSelected)

		self.contents.layout().addWidget(self.serialSelector)

		self.messageLabel = QtWidgets.QLabel(self)
		self.messageLabel.setText('test test test test')
		self.contents.layout().addWidget(self.messageLabel)

		self.button = QtWidgets.QPushButton(parent=self, text='Return')
		self.button.clicked.connect(self.finished.emit)
		self.button.setEnabled(False)
		self.button.setStyleSheet('QPushButton { padding: 15px }')

		self.contents.layout().addWidget(self.button)

		self.setLayout(QtWidgets.QVBoxLayout())
		self.centeredContainer = CenteredContainer()
		self.layout().addWidget(self.centeredContainer)
		self.centeredContainer.setWidget(self.contents)

	def onDeviceSelected(self, device):
		if device is not None:
			self.deviceSelected.emit(device)

	def reset(self):
		self.messageLabel.setText('')
		self.button.setEnabled(False)

	def showError(self, message):
		self.messageLabel.setText(f'<center>{message}</center>')
		self.messageLabel.setStyleSheet('QLabel { color: #A00; font-weight: bold; } ')
		logging.error(f'Serial device error: {message}')

	def enableButton(self):
		self.messageLabel.setText('<center>Connected!</center>')
		self.messageLabel.setStyleSheet('QLabel { color: #090; font-weight: bold; } ')
		self.button.setEnabled(True)

class StateWidget(QtWidgets.QWidget):
	finished = QtCore.Signal()

	def __init__(self, name, parent=None):
		super().__init__(parent=parent)
		self.name = name

	def onStarted(self):
		pass

	def __getstate__(self):
		props = self.__dict__.keys()

		data = {}
		for key,value in self.__dict__.items():
			if key == '__METAOBJECT__':
				continue

			if isSerializable(value):
				data[key] = self.__dict__[key]

		return data

	def __setstate__(self, state):
		self.__dict__.update(state)

class InstructionsScreen:
	pass

class PromptWidget(StateWidget):
	def __init__(self, name, text, parent=None):
		super().__init__(name=name, parent=parent)

		self.text = text

		self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
		self.setLayout(QtWidgets.QVBoxLayout())
		label = QtWidgets.QLabel(text)
		label.setWordWrap(True)
		self.layout().addWidget(label)

class KeyPromptWidget(PromptWidget):
	def __init__(self, name, text, dismissKey=QtCore.Qt.Key_Space, parent=None):
		super().__init__(name=name, text=text, parent=parent)
		self.dismissKey = dismissKey

	def keyPressEvent(self, event):
		if event.key() == self.dismissKey:
			self.finished.emit()

	def __repr__(self):
		text = self.text.replace('\n', '\\n')
		return f'<{self.__class__.__name__}(name={self.name}, text={text}, dismissKey={self.dismissKey})>'

	def __setstate__(self, state):
		self.__init__(state['name'], state['text'], state['dismissKey'])

class ButtonPromptWidget(PromptWidget):
	def __init__(self, name, text, buttonText='Continue', enabledDelaySeconds=5, parent=None):
		super().__init__(name=name, text=text, parent=parent)

		self.buttonText = buttonText
		self.enabledDelaySeconds = enabledDelaySeconds

		self.button = QtWidgets.QPushButton(parent=self, text=buttonText)
		self.button.clicked.connect(self.onButtonClicked)
		self.button.setDisabled(True)
		self.button.setStyleSheet('QPushButton { padding: 15px }')

		self.layout().addWidget(self.button)
		self.setFocusProxy(self.button)

	def showEvent(self, event):
		super().showEvent(event)
		QtCore.QTimer.singleShot(self.enabledDelaySeconds*1000, self.onDelayFinished)

	def onDelayFinished(self):
		self.button.setDisabled(False)
		self.button.setFocus()

	def onButtonClicked(self):
		self.setDisabled(True) # prevent double clicks
		self.finished.emit()

	def __repr__(self):
		text = self.text.replace('\n', '\\n')
		buttonText = self.buttonText.replace('\n', '\\n')
		return f'<{self.__class__.__name__}(name={self.name}, text={text}, buttonText={buttonText}, enabledDelaySeconds={self.enabledDelaySeconds})>'

	def __setstate__(self, state):
		self.__init__(state['name'], state['text'], state['buttonText'], state['enabledDelaySeconds'])

class TextInstructionsScreen(ButtonPromptWidget, InstructionsScreen):
	pass

class ButtonPromptWidgetWithVideo(ButtonPromptWidget, InstructionsScreen):
	def __init__(self, name, text, buttonText='Continue', enabledDelaySeconds=5, videoURL=None, videoStartDelaySeconds=0.5, parent=None):
		super().__init__(name, text, buttonText, enabledDelaySeconds, parent)

		self.videoURL = videoURL
		self.videoStartDelaySeconds = videoStartDelaySeconds

		self.widgetContainer = QtWidgets.QWidget()
		self.widgetContainer.setLayout(QtWidgets.QVBoxLayout())
		self.widgetContainer.setStyleSheet('QWidget { border: 10px solid #000; background: #000; }')

		self.videoWidget = QtMultimediaWidgets.QVideoWidget(self)
		self.widgetContainer.layout().addWidget(self.videoWidget)

		self.playButton = QtWidgets.QPushButton(self)
		self.playButton.setText('Replay video')
		self.playButton.clicked.connect(self.replayVideo)

		self.layout().insertWidget(0, self.widgetContainer)
		self.layout().insertWidget(1, self.playButton)

		self.mediaPlayer = QtMultimedia.QMediaPlayer()
		self.mediaPlayer.setVideoOutput(self.videoWidget)

		self.playlist = QtMultimedia.QMediaPlaylist()
		self.playlist.addMedia(videoURL)
		self.mediaPlayer.setPlaylist(self.playlist)

		self.videoDelaySeconds = videoStartDelaySeconds

	def replayVideo(self):
		self.mediaPlayer.stop()
		self.mediaPlayer.play()

	def showEvent(self, event):
		super().showEvent(event)
		QtCore.QTimer.singleShot(self.videoStartDelaySeconds*1000, self.replayVideo)

	def hideEvent(self, event):
		super().hideEvent(event)
		self.mediaPlayer.stop()

	def keyPressEvent(self, keyEvent):
		super().keyPressEvent(keyEvent)

		if keyEvent.key() == QtCore.Qt.Key_W:
			self.playButton.setFocus()

		elif keyEvent.key() == QtCore.Qt.Key_S:
			self.button.setFocus()

	def __setstate__(self, state):
		self.__init__(state['name'], state['text'], state['buttonText'], state['enabledDelaySeconds'], state['videoURL'], state['videoStartDelaySeconds'])

class CenteredContainer(QtWidgets.QWidget):
	def __init__(self, widget=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setLayout(QtWidgets.QGridLayout(self))
		spacer = QtWidgets.QWidget(self)
		spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
		self.layout().addWidget(spacer, 0, 0)

		spacer = QtWidgets.QWidget(self)
		spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
		self.layout().addWidget(spacer, 2, 2)

		if widget is not None:
			self.setWidget(widget)

	def setWidget(self, widget):
		self.layout().addWidget(widget, 1, 1)

class SoundCollectionButton(QtWidgets.QPushButton):
	def __init__(self, text, collection=None, *args, **kwargs):
		super().__init__(*args, **kwargs)

		if collection is None:
			collection = []

		self.setText(text)
		self.sounds = list(collection)
		self.clicked.connect(self.onClicked)
		self.soundIdx = -1

	def addSound(self, sound):
		self.sounds.append(sound)

	def onClicked(self):
		self.soundIdx = (self.soundIdx + 1) % len(self.sounds)

		soundFile = self.sounds[self.soundIdx]
		self.soundEffect = QtMultimedia.QSoundEffect()
		self.soundEffect.setSource(QtCore.QUrl.fromLocalFile(str(soundFile)))
		self.soundEffect.play()

		logging.info(f'Play sound {soundFile}')

class ButtonPromptWidgetWithSoundBoard(ButtonPromptWidget, InstructionsScreen):
	def __init__(self, name, text, buttonText='Continue', enabledDelaySeconds=0, sounds=None, buttonsPerRow=4, parent=None):
		super().__init__(name, text, buttonText, enabledDelaySeconds, parent)

		if sounds is None:
			return

		self.sounds = sounds
		self.buttonsPerRow = buttonsPerRow

		self.widgetContainer = QtWidgets.QWidget()
		self.widgetContainer.setLayout(QtWidgets.QGridLayout())
		self.widgetContainer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
		soundCollections = {}
		for idx,stimulus in enumerate(sounds):
			if stimulus.id not in soundCollections:
				soundCollections[stimulus.id] = []

			soundCollections[stimulus.id].append(stimulus.file)

		for idx,(stimID,collection) in enumerate(soundCollections.items()):
			random.shuffle(collection)
			button = SoundCollectionButton(stimID, collection, parent=self)
			button.setMinimumSize(125, 75)
			button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
			self.widgetContainer.layout().addWidget(button, int(idx/buttonsPerRow), idx%buttonsPerRow)

		centeredContainer = CenteredContainer(self.widgetContainer, parent=self)
		self.layout().insertWidget(1, centeredContainer)
		self.layout().insertStretch(0)
		self.layout().insertStretch(2)
		self.layout().insertStretch(4)

	def showEvent(self, event):
		super().showEvent(event)

		firstButton = self.widgetContainer.layout().itemAt(0).widget()
		QtCore.QTimer.singleShot(10, firstButton.setFocus)

	def keyPressEvent(self, event):
		super().keyPressEvent(event)

		newFocusIndex = navigateGridLayout(self.widgetContainer, event)
		if newFocusIndex > -1:
			self.lastFocusedButtonIdx = newFocusIndex
		else:
			if event.key() == QtCore.Qt.Key_W:
				self.widgetContainer.layout().itemAt(self.lastFocusedButtonIdx).widget().setFocus()

			elif event.key() == QtCore.Qt.Key_S:
				self.button.setFocus()

	def __setstate__(self, state):
		self.__init__(state['name'], state['text'], state['buttonText'], state['enabledDelaySeconds'], state['sounds'], state['buttonsPerRow'])

class DataLogger:
	def __init__(self, arguments, evalType):
		self.arguments = arguments

		now = nowStamp().replace(':', '-')
		nameBits = [now, arguments['pid'], arguments['condition'], evalType, arguments['facilitator']]

		self.baseFilename = '_'.join(nameBits)
		self.path = Path(f'data/{self.baseFilename}.csv')
		self.path.parent.mkdir(parents=True, exist_ok=True)

		self.dataFile = self.path.open('w')
		self.csvWriter = csv.DictWriter(
			self.dataFile,
			fieldnames=self.getFieldNames(),
			extrasaction='ignore'
		)
		self.csvWriter.writeheader()

	def getFieldNames(self):
		return ['timestamp', 'pid', 'condition', 'facilitator', 'event', 'item', 'selection', 'stimulus', 'stimfile']

	def buildRecord(self, finishedWidget):
		record = dict(self.arguments)

		record['timestamp'] = nowStamp()
		record['event'] = 'finished'
		record['item'] = finishedWidget.name
		if hasattr(finishedWidget, 'selection') and hasattr(finishedWidget, 'stimulus'):
			record['selection'] = finishedWidget.selection
			record['stimulus'] = finishedWidget.stimulus.id
			record['stimfile'] = finishedWidget.stimulus.vtt.filepath.name

		return record

	def logWidgetCompletion(self, finishedWidget):
		record = self.buildRecord(finishedWidget)
		logging.info(f'Logging record {record}')

		self.csvWriter.writerow(record)
		self.dataFile.flush()

	def close(self):
		self.dataFile.close()

class FileStimulus:
	def __init__(self, file, id):
		self.file = file
		self.id = id

	def __repr__(self):
		return f'<{self.__class__.__name__} id={self.id} file={self.file}>'

class Stimulus(FileStimulus):
	def __init__(self, file, id):
		super().__init__(file, id)

		self.vtt = loadVTTFile(file)

def navigateGridLayout(containerWidget, keyEvent):
	focusedWidget = QtWidgets.QApplication.instance().focusWidget()

	layout = containerWidget.layout()
	focusedIdx = layout.indexOf(focusedWidget)
	newFocusIdx = -1

	if focusedIdx > -1:
		if keyEvent.key() == QtCore.Qt.Key_W:
			newFocusIdx = focusedIdx - layout.columnCount()

		elif keyEvent.key() == QtCore.Qt.Key_A:
			if focusedIdx % layout.columnCount() > 0:
				newFocusIdx = focusedIdx - 1

		elif keyEvent.key() == QtCore.Qt.Key_S:
			newFocusIdx = focusedIdx + layout.columnCount()

		elif keyEvent.key() == QtCore.Qt.Key_D:
			if focusedIdx % layout.columnCount() < layout.columnCount() - 1:
				newFocusIdx = focusedIdx + 1

	if newFocusIdx > -1 and newFocusIdx < layout.count():
		layout.itemAt(newFocusIdx).widget().setFocus()
	else:
		newFocusIdx = -1

	return newFocusIdx

class GhostButton(QtWidgets.QToolButton):
	def __init__(self, text=None, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.setText(text)
		sp_retain = self.sizePolicy()
		sp_retain.setRetainSizeWhenHidden(True)
		self.setSizePolicy(sp_retain)

	def focusOutEvent(self, event):
		super().focusOutEvent(event)
		self.hide()
