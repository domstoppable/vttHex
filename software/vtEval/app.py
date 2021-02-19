import sys
import subprocess
import csv

from PySide2 import QtCore, QtGui, QtWidgets

from . import ui
from .participant import Participant

class VtEvalApp():
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

	def onEvalRequested(self, facilitator, pid, condition, evalName):
		proc = subprocess.Popen(
			[
				sys.executable, '-m', f'vtEval.{evalName.lower()}',
				'--facilitator', facilitator,
				'--pid', pid,
				'--condition', condition.lower()
			],
			text=True
		)

		print(f'{facilitator} is running {pid}\'s {condition} for {evalName}')
		execDialog = ui.ExecutionDialog(proc=proc, textDescription=evalName, parent=self.mainWindow)
		execDialog.exec_()

	def exec_(self):
		self.mainWindow.show()
		self.app.exec_()

def run():
	app = VtEvalApp()
	app.exec_()
