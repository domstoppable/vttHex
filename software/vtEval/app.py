import sys
import subprocess
import csv

from PySide2 import QtCore, QtGui, QtWidgets

from . import ui
from .participant import Participant

class VtEvalController():
	def __init__(self):
		self.app = QtWidgets.QApplication()
		self.setupGui()

	def setupGui(self):
		self.mainWindow = ui.MainWindow()
		self.mainWindow.resetRequested.connect(self.resetMainWindow)
		self.mainWindow.evalRequested.connect(self.onEvalRequested)

	def resetMainWindow(self):
		if self.mainWindow is not None:
			self.mainWindow.hide()

		self.setupGui()
		self.mainWindow.show()

	def onEvalRequested(self, evalName, facilitator, participant, condition, device):
		proc = subprocess.Popen(
			[
				sys.executable, '-m', f'vtEval.{evalName.lower()}',
				'--facilitator', facilitator,
				'--pid', participant.id,
				'--condition', condition,
				'--device', device.systemLocation(),
			],
			text=True
		)

		execDialog = ui.ExecutionDialog(proc=proc, textDescription=evalName, parent=self.mainWindow)
		execDialog.exec_()

	def exec_(self):
		self.mainWindow.show()
		self.app.exec_()

def run():
	app = VtEvalController()
	app.exec_()
