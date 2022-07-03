import sys
import subprocess
import csv

from PySide2 import QtCore, QtGui, QtWidgets

from . import ui
from .participant import Participant

class VtEvalController():
	def __init__(self):
		self.simulateEnabled = '--simulate' in sys.argv

		self.app = QtWidgets.QApplication()
		self.setupGui()

	def setupGui(self):
		self.mainWindow = ui.MainWindow(simulateEnabled=self.simulateEnabled)
		self.mainWindow.resetRequested.connect(self.resetMainWindow)
		self.mainWindow.evalRequested.connect(self.onEvalRequested)

	def resetMainWindow(self):
		if self.mainWindow is not None:
			self.mainWindow.hide()

		self.setupGui()
		self.mainWindow.show()

	def onEvalRequested(self, evalName, facilitator, participant, condition, device):
		args = [
			sys.executable, '-m', f'vtEval.{evalName.lower()}',
			'--facilitator', facilitator,
			'--pid', participant.id,
			'--condition', condition,
			'--device', device.systemLocation(),
		]
		if self.simulateEnabled:
			args.append('--simulate')

		proc = subprocess.Popen(args, text=True)

		execDialog = ui.ExecutionDialog(proc=proc, textDescription=evalName, parent=self.mainWindow)
		execDialog.exec_()

		self.mainWindow.showButtonFeedback(proc.returncode != 0)

	def exec_(self):
		self.mainWindow.show()
		self.app.exec_()

def run():
	app = VtEvalController()
	app.exec_()
