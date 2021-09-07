import sys
import datetime
from pathlib import Path
import csv

from PySide2 import QtCore, QtGui, QtWidgets, QtMultimedia, QtMultimediaWidgets 

import argparse
import argparseqt.gui

from . import serial
from vttHex.parseVTT import loadVTTFile

def nowStamp():
	now = datetime.datetime.now()
	return now.strftime('%Y-%m-%dT%H:%M:%S') + ('-%02d' % (now.microsecond / 10000))

class VtEvalApp():
	def __init__(self, appName):
		self.app = QtWidgets.QApplication()
		self.app.setApplicationName(appName)
		self.app.aboutToQuit.connect(self.onAboutToQuit)

		self.currentStateWidget = None
		self.arguments = {}
		self.widgetStack = []

		self.window = QtWidgets.QWidget()
		self.window.setLayout(QtWidgets.QVBoxLayout())
		self.window.setStyleSheet('font-size: 18pt')
		self.window.setContentsMargins(200, 50, 200, 50)

		self.progressBar = QtWidgets.QProgressBar()
		self.window.layout().addWidget(self.progressBar)

		self.dataLogger = None
		self.device = None

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

		if len(self.widgetStack) > 0:
			self.popNextState()
		else:
			self.onStackEmptied()

	def onStackEmptied(self):
		self.app.exit()

	def popNextState(self):
		self.progressBar.setValue(self.progressBar.maximum() - len(self.widgetStack) + 1)
		while self.window.layout().count() > 1:
			widget = self.window.layout().takeAt(1).widget()
			widget.setParent(None)

		self.currentStateWidget = self.widgetStack.pop(0)
		self.window.layout().addWidget(self.currentStateWidget)
		self.currentStateWidget.finished.connect(lambda: self.onStateWidgetFinished(self.currentStateWidget))
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
		self.initialize(self.arguments)
		self.widgetStack.append(KeyPromptWidget(name='finished', text='<center>You are finished!<br/><br/>Please let the facilitator know.</center>', dismissKey=QtCore.Qt.Key_F4))
		self.window.showFullScreen()
		QtCore.QTimer.singleShot(0, self.onStarted)

		if self.arguments['simulate']:
			self.simulate()
		else:
			self.app.exec_()

class StateWidget(QtWidgets.QWidget):
	finished = QtCore.Signal()

	def __init__(self, name, parent=None):
		super().__init__(parent=parent)
		self.name = name

	def onStarted(self):
		pass

class PromptWidget(StateWidget):
	def __init__(self, name, text, parent=None):
		super().__init__(name=name, parent=parent)

		self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
		self.setLayout(QtWidgets.QVBoxLayout())
		label = QtWidgets.QLabel(text)
		label.setWordWrap(True)
		self.layout().addWidget(label)

	def showEvent(self, event):
		self.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)

class KeyPromptWidget(PromptWidget):
	def __init__(self, name, text, dismissKey=QtCore.Qt.Key_Space, parent=None):
		super().__init__(name=name, text=text, parent=parent)
		self.dismissKey = dismissKey

	def keyPressEvent(self, event):
		if event.key() == self.dismissKey:
			self.finished.emit()

class ButtonPromptWidget(PromptWidget):
	def __init__(self, name, text, buttonText='Continue', enabledDelaySeconds=5, parent=None):
		super().__init__(name=name, text=text, parent=parent)

		self.enabledDelaySeconds = enabledDelaySeconds

		self.button = QtWidgets.QPushButton(parent=self, text=buttonText)
		self.button.clicked.connect(self.finished.emit)
		self.button.setDisabled(True)

		self.layout().addWidget(self.button)
		self.setFocusProxy(self.button)

	def showEvent(self, event):
		super().showEvent(event)
		QtCore.QTimer.singleShot(self.enabledDelaySeconds*1000, lambda: self.button.setDisabled(False))

class ButtonPromptWidgetWithVideo(ButtonPromptWidget):
	def __init__(self, name, text, buttonText='Continue', enabledDelaySeconds=5, videoURL=None, videoStartDelaySeconds=0.5, parent=None):
		super().__init__(name, text, buttonText, enabledDelaySeconds, parent)

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

class DataLogger:
	def __init__(self, arguments, evalType):
		self.arguments = arguments

		now = nowStamp().replace(':', '-')
		nameBits = [now, arguments['pid'], arguments['condition'], evalType, arguments['facilitator']]
		path = Path(f'data/' + '_'.join(nameBits) + '.csv')
		path.parent.mkdir(parents=True, exist_ok=True)
		self.dataFile = path.open('w')
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
		print('log', record)

		self.csvWriter.writerow(record)
		self.dataFile.flush()

	def close(self):
		self.dataFile.close()

class Stimulus:
	def __init__(self, file, id):
		self.vtt = loadVTTFile(file)
		self.id = id

	def __repr__(self):
		return f'<{self.__class__.__name__} id={self.id} file={self.vtt.filepath}>'

