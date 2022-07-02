import datetime
import re
import time
import random
import csv
from enum import Enum, auto
from pathlib import Path

from PySide2 import QtCore, QtGui, QtWidgets, QtMultimedia

from vtEval.vtEvalApp import *
from vtEval import serial, noise

instructions = '''<html>
	<h1>Perceptual Integration</h1>
	<p>In this evaluation, you will be presented with a syllable as a sound to your ears and, simultaneously, as a vibration on your arm.</p>
	<p>After the syllable is played, click the button which matches what you heard. The buttons change every time, so pay attention to what's on each button before you make a selection. If you are uncertain, make a guess.</p>
	<hr/>
	<p>If you have any questions, please ask them now. Otherwise, click the <strong>Continue</strong> button below when you are ready to begin.</p>
</html>'''

stimPairResponseOptions = {
	('Ba', 'Da'): ['Ba', 'Da', 'Ga', 'Pa'],
	('Ba', 'Ga'): ['Ba', 'Ga', 'Da', 'Ma'],
	('Ba', 'Ka'): ['Ba', 'Ka', 'Ga', 'Da'],
	('Ba', 'Na'): ['Ba', 'Na', 'Ga', 'Da'],
	('Ba', 'Ta'): ['Ba', 'Ta', 'Pa', 'Da'],
	('Ma', 'Ga'): ['Ma', 'Ga', 'Na', 'Ba'],
	('Ma', 'Ta'): ['Ma', 'Ta', 'Na', 'La'],
	('Pa', 'Da'): ['Pa', 'Da', 'Ka', 'Ta'],
	('Pa', 'Ga'): ['Pa', 'Ga', 'Ka', 'Ta'],
	('Pa', 'Ka'): ['Pa', 'Ka', 'Da', 'Ta'],
	('Pa', 'Na'): ['Pa', 'Na', 'Ka', 'Ta'],
	('Pa', 'Ta'): ['Pa', 'Ta', 'Da', 'Ka'],
}

class StimPair(Stimulus):
	phoneNamePattern = re.compile(r'[fm]_(.a)_TK*')
	sounds = {}

	def __init__(self, wavFile, vttFile):
		self.wavFile = wavFile
		self.vttFile = vttFile

		if not self.wavFile in StimPair.sounds:
			sound = QtMultimedia.QSoundEffect()
			sound.setSource(QtCore.QUrl.fromLocalFile(str(self.wavFile)))
			StimPair.sounds[self.wavFile] = sound

		self.sound = StimPair.sounds[self.wavFile]

		self.id = str(self)
		super().__init__(vttFile, str(self))

	@staticmethod
	def getPhone(filename):
		return StimPair.phoneNamePattern.match(filename.stem).groups(1)[0]

	def getAudiblePhone(self):
		return StimPair.getPhone(self.wavFile)

	def getTactilePhone(self):
		return StimPair.getPhone(self.vttFile)

	def getResponseOptions(self):
		audible = self.getAudiblePhone()
		tactile = self.getTactilePhone()

		return stimPairResponseOptions[(audible, tactile)]

	def __repr__(self):
		return f'{self.getAudiblePhone()}-{self.getTactilePhone()}'

class AFCWidget(StateWidget):
	stimulusBraced = QtCore.Signal(object)
	stimulusTriggered = QtCore.Signal(object)

	def __init__(self, name, stimPair, parent=None):
		super().__init__(name=name, parent=parent)

		self.delayBeforeStimulus = 1000
		self.delayAfterStimulus = 750

		self.stimulus = stimPair
		self.selection = None

		self.setLayout(QtWidgets.QVBoxLayout())
		self.label = QtWidgets.QLabel(parent=self)
		self.label.setAlignment(QtCore.Qt.AlignCenter)
		self.label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.layout().addWidget(self.label)

		horizontalCount = 2
		self.buttonContainer = QtWidgets.QWidget()
		self.buttonContainer.setLayout(QtWidgets.QGridLayout())
		self.buttonContainer.layout().setSpacing(20)

		buttonPositions = [(0,1), (1,0), (1,2), (2,1)]

		self.options = list(self.stimulus.getResponseOptions())
		random.shuffle(self.options)
		for idx,opt in enumerate(self.options):
			row,col = buttonPositions[idx]

			button = QtWidgets.QPushButton(parent=self, text=opt)
			button.clicked.connect(lambda _=None, opt=opt: self.onChoiceMade(opt))
			button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			self.buttonContainer.layout().addWidget(button, row, col)

		self.orButton = GhostButton('✣')
		self.buttonContainer.layout().addWidget(self.orButton, 1, 1, QtCore.Qt.AlignCenter)

		self.layout().addWidget(self.buttonContainer)

	def onStarted(self):
		noise.play()
		self.buttonContainer.setDisabled(True)

		QtCore.QTimer.singleShot(self.delayBeforeStimulus, self.playStimulus)
		self.stimulusBraced.emit(self.stimulus)

	def playStimulus(self):
		self.label.setText('🔊\n{{ 🖐 }}')
		self.stimulusTriggered.emit(self.stimulus)

		QtCore.QTimer.singleShot(1500, self.onStimulusDone)

	def onStimulusDone(self):
		self.label.setText('')
		QtCore.QTimer.singleShot(self.delayAfterStimulus, self.enableButtons)

	def enableButtons(self):
		self.label.setText('Make a selection')
		self.buttonContainer.setDisabled(False)

		noise.stop()
		self.orButton.setFocus()

	def onChoiceMade(self, option):
		self.selection = option
		self.finished.emit()

	def keyPressEvent(self, event):
		super().keyPressEvent(event)

		buttonToKeyMap = [
			QtCore.Qt.Key_W,
			QtCore.Qt.Key_A,
			QtCore.Qt.Key_D,
			QtCore.Qt.Key_S,
		]

		if event.key() in buttonToKeyMap:
			idx = buttonToKeyMap.index(event.key())
			self.buttonContainer.layout().itemAt(idx).widget().setFocus()

class IntegrationDataLogger(DataLogger):
	def getFieldNames(self):
		return super().getFieldNames() + ['audibleFile', 'options']

	def buildRecord(self, finishedWidget):
		record = super().buildRecord(finishedWidget)

		if hasattr(finishedWidget, 'stimulus'):
			record['audibleFile'] = finishedWidget.stimulus.wavFile.name

		if hasattr(finishedWidget, 'options'):
			record['options'] = '|'.join(finishedWidget.options)

		return record

class IntegrationEvalApp(VtEvalApp):
	def __init__(self):
		super().__init__('Integration Evaluation')

		self.stimSets = []

		for audibleFile in Path(locateAsset('wav')).glob('*.wav'):
			speakerID = int(audibleFile.stem[7:9])
			audiblePhone = StimPair.getPhone(audibleFile)

			for tactileFile in Path(locateAsset('vtt')).glob(f'*TK0{speakerID}.vtt'):
				tactilePhone = StimPair.getPhone(tactileFile)

				token = (audiblePhone, tactilePhone)
				if token in stimPairResponseOptions:
					self.stimSets.append(StimPair(audibleFile, tactileFile))

		random.shuffle(self.stimSets)

	def simulate(self):
		isPostTest = self.arguments['condition'] == 'Post-test'

		for w in self.widgetStack:
			if isinstance(w, AFCWidget):
				if not isPostTest:
					# on the pre-test, we'll pick the auditory stim at least 90%
					if random.random() < .9:
						w.selection = w.stimulus.id[:2]
					else:
					# on all other trials, we'll pick randomly
						w.selection = random.choice(w.options)
				else:
					# on the post-test, we'll pick the auditory stim at least 85%
					if random.random() < .9:
						w.selection = w.stimulus.id[:2]
					else:
					# on all other trials, we'll pick an integrated option
						nonIntegratedOptions = w.stimulus.id.split('-')
						integratedOptions = list(w.options)
						for opt in nonIntegratedOptions:
							integratedOptions.remove(opt)

						w.selection = random.choice(integratedOptions)

			self.dataLogger.logWidgetCompletion(w)

	def initialize(self, arguments):
		self.widgetStack.append(ButtonPromptWidget('instructions', instructions))

		tactileAuditoryStack = []
		for idx,stimPair in enumerate(self.stimSets):
			stimWidget = AFCWidget(f'tactileAuditoryStack-{idx:03}', stimPair)
			stimWidget.stimulusBraced.connect(self.prepareStimulus)
			stimWidget.stimulusTriggered.connect(self.playStimulus)
			tactileAuditoryStack.append(stimWidget)

		breakWidget = ButtonPromptWidget('break', '<center>Time for a break!<br/><br/>Press the button below when you are ready to continue.</center>')

		self.widgetStack += tactileAuditoryStack
		self.dataLogger = IntegrationDataLogger(arguments, 'integration')

	def playStimulus(self, stimulus):
		stimulus.sound.play()
		super().playStimulus(stimulus)

def run():
	app = IntegrationEvalApp()
	app.execute()
