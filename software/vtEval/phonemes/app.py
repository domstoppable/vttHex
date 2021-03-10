import datetime
import re
import time
import random
import csv
from enum import Enum, auto
from pathlib import Path

from PySide2 import QtCore, QtGui, QtWidgets

from vtEval.vtEvalApp import *
from vtEval import serial

instructions = '''<html>
	<h1>Phoneme Evaluation</h1>
	<p>Amet magni dolor ea repellat illo quis expedita sint. Omnis ea eum perspiciatis culpa maiores voluptatem repudiandae perspiciatis. Adipisci delectus voluptate dolorem aut qui hic sunt dolor. Autem dolores doloribus autem exercitationem dicta molestiae quibusdam. Ab in provident iure eveniet voluptatum voluptatum aut.</p>
	<p>Eius provident magni voluptas tenetur reprehenderit qui consequatur. Ipsa nihil cupiditate id qui. Consequatur unde fugiat tenetur est harum provident deleniti.</p>
	<p>In harum delectus eligendi pariatur vero ab. Reprehenderit porro optio dicta rem quibusdam quidem fugiat et. Voluptatem dolorum sequi enim non molestiae consequatur velit. Quis modi dolorum vero sint facilis. Ab quam repellat velit voluptatem earum. Nisi sint voluptatem esse iusto voluptas.</p>
	<p>Cupiditate est consequuntur deleniti dolorem eos. Beatae vel qui quas sed impedit iusto eaque. Exercitationem laborum repudiandae voluptatum et veniam qui non quod. Sunt necessitatibus et sed voluptate nulla sunt vero et. Aperiam eligendi tempore exercitationem adipisci.</p>
	<br/>
	<center>Click the button below when you are ready to begin.</center></p>
</html>'''

stimPath = Path('vtEval/phonemes/audio')

phoneToHumanMap = {
	'AW': 'hAWEd',
	'AE': 'hAd',
	'UH': 'hUd',
	'AH': 'hOd',
	'EH': 'hEAd',
	'ER': 'hEARd',
	'EI': 'hAYEd',
	'IH': 'hId',
	'IY': 'hEEd',
	'OA': 'hOEd',
	'OO': 'hOOd',
	'UW': 'whO\'d',
	'B' : 'aBa',
	'CH': 'aCHa',
	'D' : 'aDa',
	'DH': 'aTHa',
	'F' : 'aFa',
	'G' : 'aGa',
	'J' : 'aJa',
	'K' : 'aKa',
	'L' : 'aLa',
	'M' : 'aMa',
	'N' : 'aNa',
	'P' : 'aPa',
	'R' : 'aRa',
	'S' : 'aSa',
	'SH': 'aSHa',
	'T' : 'aTa',
	'V' : 'aVa',
	'W' : 'aWa',
	'Y' : 'aYa',
	'Z' : 'aZa',
}

class AFCWidget(StateWidget):
	stimulusBraced = QtCore.Signal(object)
	stimulusTriggered = QtCore.Signal(object)

	def __init__(self, name, stimulus, options, parent=None):
		super().__init__(name=name, parent=parent)

		self.delayBeforeStimulus = 1000
		self.delayAfterStimulus = 750

		self.stimulus = stimulus
		self.options = options
		self.selection = None

		self.setLayout(QtWidgets.QVBoxLayout())
		self.label = QtWidgets.QLabel(parent=self)
		self.label.setAlignment(QtCore.Qt.AlignCenter)
		self.label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.layout().addWidget(self.label)

		horizontalCount = 5
		self.buttonContainer = QtWidgets.QWidget()
		self.buttonContainer.setDisabled(True)
		self.buttonContainer.setLayout(QtWidgets.QGridLayout())
		self.buttonContainer.layout().setSpacing(20)
		for idx,opt in enumerate(self.options):
			row = int(idx / horizontalCount)
			col = idx % horizontalCount

			button = QtWidgets.QPushButton(parent=self, text=opt)
			button.clicked.connect(lambda _=None, opt=opt: self.onChoiceMade(opt))
			button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			self.buttonContainer.layout().addWidget(button, row, col)

		self.layout().addWidget(self.buttonContainer)

	def showEvent(self, event):
		QtCore.QTimer.singleShot(self.delayBeforeStimulus, self.playStimulus)
		self.stimulusBraced.emit(self.stimulus)

	def playStimulus(self):
		self.label.setText('{{ 🖐 }}')
		self.stimulusTriggered.emit(self.stimulus)

		QtCore.QTimer.singleShot(500, self.onStimulusDone)

	def onStimulusDone(self):
		self.label.setText('')
		QtCore.QTimer.singleShot(self.delayAfterStimulus, self.enableButtons)

	def enableButtons(self):
		self.label.setText('Make a selection')
		self.buttonContainer.setDisabled(False)

	def onChoiceMade(self, option):
		self.selection = option
		self.finished.emit()
class PhonemeEvalApp(VtEvalApp):
	def __init__(self):
		super().__init__('Phoneme Evaluation')

		self.loadConsonants()
		self.loadVowels()

	def initialize(self, arguments):
		stack = [
			ButtonPromptWidget('instructions', instructions),
		]

		consonantStack = []
		for idx,stim in enumerate(self.consonants):
			stimWidget = AFCWidget(f'consonant-{idx:03}', stim, self.consonantSet)
			stimWidget.stimulusBraced.connect(self.prepareStimulus)
			stimWidget.stimulusTriggered.connect(self.playStimulus)
			consonantStack.append(stimWidget)

		vowelStack = []
		for idx,stim in enumerate(self.vowels):
			stimWidget = AFCWidget(f'vowel-{idx:03}', stim, self.vowelSet)
			stimWidget.stimulusBraced.connect(self.prepareStimulus)
			stimWidget.stimulusTriggered.connect(self.playStimulus)
			vowelStack.append(stimWidget)

		breakWidget = ButtonPromptWidget('break', '<center>Time for a break!<br/><br/>Press the button below when you are ready to continue.</center>')

		# counterbalance consonants vs vowels order presentation
		if int(arguments['pid']) % 2 == 0:
			stack += consonantStack + [breakWidget] + vowelStack
		else:
			stack += vowelStack + [breakWidget] + consonantStack

		self.widgetStack = stack
		self.dataLogger = DataLogger(arguments, 'phonemes')

	def _loadStimuliFromFolder(self, pattern):
		path = stimPath/'vtt'

		uniqueSet = set()
		stims = []

		for f in list(path.glob('*.vtt')):
			match = pattern.match(str(f.stem))
			if match is None:
				continue

			phone = match.group(1)
			phone = phoneToHumanMap[phone.upper()]
			stims.append(Stimulus(f, phone))

			uniqueSet.add(phone)

		random.shuffle(stims)
		return (stims, sorted(list(uniqueSet)))

	def loadConsonants(self):
		pattern = re.compile(r'[MW][1-5]A(.{1,2})A7M')
		(self.consonants, self.consonantSet) = self._loadStimuliFromFolder(pattern)

	def loadVowels(self):
		pattern = re.compile(r'[mw][0-9]{2}(.*)')
		(self.vowels, self.vowelSet) = self._loadStimuliFromFolder(pattern)

	def prepareStimulus(self, stimulus):
		self.device.sendFile(stimulus.vtt)

	def playStimulus(self, stimulus):
		self.device.play()

def run():
	app = PhonemeEvalApp()
	app.execute()
