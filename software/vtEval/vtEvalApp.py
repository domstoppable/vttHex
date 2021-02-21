import sys

from PySide2 import QtCore, QtGui, QtWidgets

import argparse
import argparseqt.gui

from . import serial

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
		self.window.setStyleSheet('font-size: 24pt')
		self.window.setContentsMargins(200, 50, 200, 50)

		self.dataLogger = None
		self.device = None

	def initialize(self, arguments):
		raise Exception(f'{self.app.applicationName()} is not configured!')

	def onStarted(self):
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
		while self.window.layout().count() > 0:
			widget = self.window.layout().takeAt(0).widget()
			widget.setParent(None)

		self.currentStateWidget = self.widgetStack.pop(0)
		self.window.layout().addWidget(self.currentStateWidget)
		self.currentStateWidget.finished.connect(lambda: self.onStateWidgetFinished(self.currentStateWidget))
		self.currentStateWidget.onStarted()

	def execute(self):
		parser = argparse.ArgumentParser(description=self.app.applicationName())

		parser.add_argument('--facilitator', type=str)
		parser.add_argument('--pid', type=str)
		parser.add_argument('--condition', type=str)
		parser.add_argument('--device', type=str)

		self.arguments = argparseqt.groupingTools.parseIntoGroups(parser)

		if None in self.arguments.values():
			dialog = argparseqt.gui.ArgDialog(parser)
			dialog.setValues(self.arguments)
			dialog.exec_()

			if dialog.result() == QtWidgets.QDialog.Accepted:
				self.arguments = dialog.getValues()
			else:
				sys.exit(1)

		self.device = serial.SerialDevice(self.arguments['device'])
		self.initialize(self.arguments)
		self.widgetStack.append(KeyPromptWidget(name='finished', text='<center>You are finished!<br/><br/>Please let the facilitator know.</center>', dismissKey=QtCore.Qt.Key_F4))
		self.window.showFullScreen()
		QtCore.QTimer.singleShot(0, self.onStarted)
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
