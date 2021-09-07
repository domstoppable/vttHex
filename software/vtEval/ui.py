import csv
import re

from PySide2 import QtCore, QtGui, QtWidgets

from .vtEvalApp import locateAsset
from .participant import Participant
from . import subprocs
from . import serial

def centerWindow(window):
	screenCenter = QtWidgets.QDesktopWidget().availableGeometry().center()
	windowCenter = window.rect().center()
	window.move(screenCenter - windowCenter)

class MainWindow(QtWidgets.QWidget):
	resetRequested = QtCore.Signal()
	evalRequested = QtCore.Signal(str, str, Participant, str, serial.SerialInfo)

	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self.setWindowTitle('Vibey Transcribey Eval')
		self.setLayout(QtWidgets.QVBoxLayout())

		participants = self.loadParticipants()

		form = QtWidgets.QWidget()
		form.setLayout(QtWidgets.QFormLayout())

		self.facilitatorBox = QtWidgets.QComboBox(parent=self)
		form.layout().addRow('Facilitator', self.facilitatorBox)
		facilitators = self.loadFacilitators()
		self.facilitatorBox.addItem('')
		for facilitator in facilitators:
			self.facilitatorBox.addItem(facilitator['name'])

		self.participantBox = ComboWithAddButton(
			addNewDialogClass=AddNewParticipantDialog,
			options=participants,
			parent=self
		)
		self.participantBox.itemAdded.connect(self.onParticipantAdded)
		self.participantBox.selectionChanged.connect(self.onParticipantSelected)
		form.layout().addRow('Participant', self.participantBox)

		self.serialBox = SerialSelector(parent=self)
		form.layout().addRow('Device', self.serialBox)

		self.conditionBox = RadioList(['Pre-test', 'Post-test'])
		form.layout().addRow('Condition', self.conditionBox)

		self.evalButtons = ButtonList()
		self.evalButtons.clicked.connect(self.onEvalClicked)

		self.layout().addWidget(form)
		self.layout().addWidget(self.evalButtons)

		# Buttons
		buttonBox = QtWidgets.QWidget()
		buttonBox.setLayout(QtWidgets.QHBoxLayout())

		self.resetButton = QtWidgets.QPushButton('Reset', parent=self)
		self.resetButton.clicked.connect(self.resetRequested.emit)
		buttonBox.layout().addWidget(self.resetButton)

		self.layout().addWidget(buttonBox)

	def onParticipantAdded(self, newParticipant):
		participants = self.loadParticipants()

		# check for dup
		duplicates = []
		for participant in participants:
			if participant.id == newParticipant.id:
				duplicates.append(participant)

		if len(duplicates) > 0:
			duplicates.append(newParticipant)
			duplicates = sorted(duplicates)

			listHtml = ''
			for participant in duplicates:
				listHtml += f'<li>{participant}</li>'

			msg = f'''
				<html>
					Some participants are using the same ID {participant.id}
					<ul>{listHtml}</ul>
				</html>'''
			QtWidgets.QMessageBox.warning(self, 'Add Participant', msg)

		# sort in participant
		participants.append(newParticipant)
		participants = sorted(participants)

		# save to disk
		with open(locateAsset('participants.csv'), 'w', newline='') as csvfile:
			fieldnames = ['id', 'name']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

			writer.writeheader()
			for participant in participants:
				writer.writerow(participant.__dict__)

	def onParticipantSelected(self, participant):
		self.evalButtons.clearOptions()
		if participant is not None:
			orderedEvals = subprocs.orderedByPID(participant.id)
			orderedEvals = [x.title() for x in orderedEvals]

			self.evalButtons.addOptions(orderedEvals)

			self.setTabOrder(self.facilitatorBox, self.participantBox)
			self.setTabOrder(self.participantBox, self.serialBox)
			self.setTabOrder(self.serialBox, self.conditionBox)
			self.setTabOrder(self.conditionBox, self.evalButtons)
			self.setTabOrder(self.evalButtons, self.resetButton)
			self.setTabOrder(self.resetButton, self.facilitatorBox)

	def onEvalClicked(self, evalName):
		device = self.serialBox.currentData()
		facilitator = self.facilitatorBox.currentText()
		participant = self.participantBox.currentData()
		condition = self.conditionBox.text()

		values = [device, facilitator, participant, condition]
		if '' in values or None in values:
			QtWidgets.QMessageBox.warning(self, 'Run Eval', 'You are missing a selection :(')
			return
		else:
			confirmed = QtWidgets.QMessageBox.question(
				self, 'Run Eval',
				f'''
					<html>
						<p>You are about to run the following eval:</p>
						<br/>
						<table>
							<tr><td>Facilitator </td><td><strong>{facilitator}</strong></td></tr>
							<tr><td>Participant </td><td><strong>{participant}</strong></td></tr>
							<tr><td>Condition </td><td><strong>{condition}</strong></td></tr>
							<tr><td>Evaluation </td><td><strong>{evalName}</strong></td></tr>
							<tr><td colspan="2">&nbsp;</td></tr>
							<tr><td>Device </td><td><strong>{device}</strong></td></tr>
						</table>
					</html>
				''',
				buttons=QtWidgets.QMessageBox.StandardButton.Abort|QtWidgets.QMessageBox.StandardButton.Ok
			)
			if confirmed == QtWidgets.QMessageBox.StandardButton.Ok:
				self.evalRequested.emit(evalName, facilitator, participant, condition, device)

	def show(self):
		super().show()
		centerWindow(self)

	def loadParticipants(self):
		participants = []
		try:
			with open(locateAsset('participants.csv'), newline='') as csvfile:
				reader = csv.DictReader(csvfile)
				for row in reader:
					participants.append(Participant(row['id'], row['name']))
		except Exception as exc:
			print(f'Error while reading participants: {exc}')

		return sorted(participants)

	def loadFacilitators(self):
		facilitators = []
		with open(locateAsset('facilitators.csv'), newline='') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				facilitators.append(row)

		return facilitators

class ComboWithButton(QtWidgets.QWidget):
	buttonClicked = QtCore.Signal()
	selectionChanged = QtCore.Signal(object)

	def __init__(self, options=[], buttonText='?', parent=None):
		super().__init__(parent=parent)

		self.setLayout(QtWidgets.QHBoxLayout())

		self.combo = QtWidgets.QComboBox(self)
		self.resort(options)
		self.combo.currentIndexChanged.connect(lambda idx: self.selectionChanged.emit(self.combo.itemData(idx)))

		self.button = QtWidgets.QToolButton(parent=self)
		self.button.setText(buttonText)
		self.button.clicked.connect(lambda checked: self.buttonClicked.emit())

		self.layout().addWidget(self.combo)
		self.layout().addWidget(self.button)

		self.layout().setStretch(0, 1)
		self.layout().setStretch(1, 0)
		self.layout().setContentsMargins(0, 0, 0, 0)

		self.setFocusProxy(self.combo)

	def resort(self, items=None):
		if items is None:
			items = []
			for i in range(0, self.combo.count()):
				items.append(self.combo.itemData(i))

		items = sorted(items, key=lambda item:str(item))
		selected = self.combo.currentData()
		self.combo.clear()

		for idx,item in enumerate(items):
			self.combo.addItem(repr(item), item)
			if item == selected:
				self.combo.setCurrentIndex(idx)

		if selected is None:
			self.combo.setCurrentIndex(-1)

	def currentData(self):
		return self.combo.currentData()

class SerialSelector(ComboWithButton):
	def __init__(self, parent=None):
		super().__init__(options=serial.availablePorts(), buttonText='↺', parent=parent)

		self.buttonClicked.connect(self.refresh)
		self.selectPreferred()

	def refresh(self):
		self.resort(serial.availablePorts())
		if self.combo.currentIndex() < 0:
			self.selectPreferred()

	def selectPreferred(self):
		for idx in range(self.combo.count()):
			info = self.combo.itemData(idx)
			if hasattr(info, 'isPreferred') and info.isPreferred():
				self.combo.setCurrentIndex(idx)
class ComboWithAddButton(ComboWithButton):
	itemAdded = QtCore.Signal(object)

	def __init__(self, addNewDialogClass, options=[], parent=None):
		super().__init__(options=options, buttonText='+', parent=parent)
		self.addNewDialogClass = addNewDialogClass

		self.buttonClicked.connect(self.getNewValue)

	def getNewValue(self):
		dialog = self.addNewDialogClass()
		dialogResult = dialog.exec_()

		if dialogResult == QtWidgets.QDialog.Accepted:
			data = dialog.getValue()

			self.combo.addItem(repr(data), data)
			self.combo.setCurrentIndex(self.combo.count()-1)
			self.itemAdded.emit(data)

			self.resort()

class AddNewParticipantDialog(QtWidgets.QDialog):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setWindowTitle('Add Participant')

		self.setLayout(QtWidgets.QVBoxLayout())

		form = QtWidgets.QWidget()
		form.setLayout(QtWidgets.QFormLayout())

		self.pidBox = QtWidgets.QLineEdit(parent=self)
		self.pidBox.editingFinished.connect(self.onPIDedited)
		form.layout().addRow('Participant', self.pidBox)

		self.nameBox = QtWidgets.QLineEdit(parent=self)
		form.layout().addRow('Name', self.nameBox)

		self.layout().addWidget(form)

		cancelButton = QtWidgets.QPushButton('Cancel')
		cancelButton.clicked.connect(self.reject)

		okButton = QtWidgets.QPushButton('Add')
		okButton.setDefault(True)
		okButton.clicked.connect(self.onOkPressed)

		buttonContainer = QtWidgets.QWidget(self)
		buttonContainer.setLayout(QtWidgets.QHBoxLayout())
		buttonContainer.layout().addWidget(cancelButton)
		buttonContainer.layout().addWidget(okButton)

		self.layout().addWidget(buttonContainer)

	def onOkPressed(self):
		if self.pidBox.text() == '' or self.nameBox.text() == '':
			QtWidgets.QMessageBox.warning(self, 'Add Participant', 'Blank fields are not allowed')
		else:
			self.accept()

	def onPIDedited(self):
		try:
			text = self.pidBox.text()

			pid = int(re.sub(r'[^0-9]', '', text))
			formatted = f'{pid:04}'
			if text != formatted:
				self.pidBox.setText(formatted)
		except:
			self.pidBox.undo()

	def getValue(self):
		return Participant(self.pidBox.text(), self.nameBox.text())

class EvalConfirmation(QtWidgets.QDialog):
	def __init__(self, parent=None):
		super().__init__(self)

class RadioList(QtWidgets.QWidget):
	def __init__(self, options=[], parent=None):
		super().__init__(parent=parent)
		self.setLayout(QtWidgets.QHBoxLayout())

		self.group = QtWidgets.QButtonGroup()

		if len(options) > 0:
			for option in options:
				button = QtWidgets.QRadioButton(option, self)
				self.group.addButton(button)
				self.layout().addWidget(button)

			self.setFocusProxy(self.group.buttons()[0])

	def text(self):
		button = self.group.checkedButton()
		if button is not None:
			return button.text()

class ButtonList(QtWidgets.QWidget):
	clicked = QtCore.Signal(str)

	def __init__(self, options=[], parent=None):
		super().__init__(parent=parent)
		self.setLayout(QtWidgets.QVBoxLayout())

		self.group = QtWidgets.QButtonGroup()
		self.addOptions(options)

	def addOption(self, option):
		button = QtWidgets.QPushButton(option, self)
		self.group.addButton(button)
		self.layout().addWidget(button)

		button.clicked.connect(lambda checked=None, option=option: self.clicked.emit(option))
		self.setFocusProxy(button)

	def addOptions(self, options):
		if len(options) > 0:
			for option in options:
				self.addOption(option)

			self.setFocusProxy(self.group.buttons()[0])

	def clearOptions(self):
		while self.layout().count() > 0:
			button = self.layout().takeAt(0).widget()
			self.group.removeButton(button)
			button.setParent(None)

class ExecutionDialog(QtWidgets.QDialog):
	def __init__(self, proc, textDescription, parent=None):
		super().__init__(parent=parent)
		self.proc = proc

		self.setWindowTitle('VT Sub Process Monitor')
		self.setLayout(QtWidgets.QVBoxLayout())
		self.setMinimumSize(200, 200)
		self.resize(400, 200)

		self.label = QtWidgets.QLabel(text=f'<html>⏳ Running {textDescription} evaluation…', parent=self)
		self.label.setAlignment(QtCore.Qt.AlignCenter)

		self.layout().addWidget(self.label)

		self.pollHandle = QtCore.QTimer(parent=self)
		self.pollHandle.setInterval(500)
		self.pollHandle.timeout.connect(self.pollProcess)

	def exec_(self):
		self.startPollingTimer = QtCore.QTimer.singleShot(1000, self.pollHandle.start)
		super().exec_()

	def pollProcess(self):
		if self.proc is not None:
			code = self.proc.poll()

			if code is not None:
				self.pollHandle.stop()

				text = self.label.text() + '<br/>'
				if code == 0:
					text += '<font color="#0c0">😺 Process completed normally</font><br/><br/>This window will automatically close.'
					self.acceptTimer = QtCore.QTimer.singleShot(5000, self.accept)
				else:
					text += f'<font color="#c00">❌ Process completed with <b>error code {code}</b></font>'

				self.label.setText(text)
				self.label.resize(self.minimumSizeHint())

	def closeEvent(self, event):
		if self.proc.poll() is None:
			response = QtWidgets.QMessageBox.question(
				self,
				'Kill sub-process?',
				'The process is still running. Would you like to kill it?',
				QtWidgets.QMessageBox.StandardButton.Cancel|QtWidgets.QMessageBox.StandardButton.Yes|QtWidgets.QMessageBox.StandardButton.No,
				QtWidgets.QMessageBox.StandardButton.Cancel
			)

			if response == QtWidgets.QMessageBox.StandardButton.Cancel:
				event.ignore()
			elif response == QtWidgets.QMessageBox.StandardButton.Yes:
				self.proc.terminate()
				event.accept()
			elif response == QtWidgets.QMessageBox.StandardButton.No:
				event.accept()
