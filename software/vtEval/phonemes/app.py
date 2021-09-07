import datetime
import re
import time
import random
import csv
from enum import Enum, auto
from pathlib import Path

from PySide2 import QtCore, QtGui, QtWidgets

from vtEval.vtEvalApp import *
from vtEval import serial, noise

instructions = {
	'intro': '''<html>
			<h1>Phoneme Evaluation</h1>
			<p>This evaluation is separated into two parts to measure your perception of consonants and vowels. Both parts follow a similar structure:</p>
			<ul>
				<li>A short, one-syllable word will be vibrated on your arm.</li>
				<li>Your task is to select the word on the screen which matches the vibrated word. If you are uncertain, guess.</li>
			</ul>
			<p>Opportunities for breaks will be provided as you proceed.</p>
			<hr/>
			<p>Click the button below when you are ready to begin the first part of this evaluation. More instructions will be provided on the next screen.</p>
		</html>''',
	'vowels': '''<html>
			<h2>Vowels</h2>
			<p>For this part of the evaluation, one of several possible words will be vibrated on your arm. Each of the words begin with an <em>h</em> sound and end with a <em>d</em> sound - they differ only on the vowel between the <em>h</em> and the <em>d</em>.</p>
			<p>The words are presented in a random order and will be repeated. The options are also randomized, so pay attention to what's on each button before you make each selection. If you are uncertain, guess.
			<hr/>
			<p>Multiple auditory samples of each of the words are available below. This is your only opportunity to familiarize yourself with the differences between the vowel sounds.</p>
			<hr/>
			<p>If you have any questions, please ask them now. Otherwise, click the <strong>Continue</strong> button below when you are ready to begin.</p>
		</html>''',
	'consonants': '''<html>
			<h2>Consonants</h2>
			<p>For this part of the evaluation, one of several possible words will be vibrated on your arm. Each of the words begins and ends with an <em>ah</em> sound - they differ only on the consonant in the middle.</p>
			<p>The words are presented in a random order and will be repeated. The options are also randomized, so pay attention to what's on each button before you make each selection. If you are uncertain, guess.
			<hr/>
			<p>Multiple auditory samples of each of the words are available below. This is your only opportunity to familiarize yourself with the differences between the vowel sounds.</p>
			<hr/>
			<p>If you have any questions, please ask them now. Otherwise, click the <strong>Continue</strong> button below when you are ready to begin.</p>
		</html>'''
}

stimPath = Path('vtEval/phonemes/audio')

phoneToHumanMap = {
	'AW': 'hAWEd',
	'AE': 'hAd',
	'UH': 'hUd',
	'AH': 'hOd',
	'EH': 'hEAd',
	'ER': 'hERd',
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

		horizontalCount = 3
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
		noise.play()
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
		noise.stop()

	def onChoiceMade(self, option):
		self.selection = option
		self.finished.emit()

class PhonemeEvalApp(VtEvalApp):
	def __init__(self):
		super().__init__('Phoneme Evaluation')

		(self.consonants, self.consonantSet) = self.loadConsonants()
		(self.vowels, self.vowelSet) = self.loadVowels()

	def simulate(self):
		isPostTest = self.arguments['condition'] == 'Post-test'
		targetRates = {
			'c': 3/9,
			'v': 3/9,
		}

		for w in self.widgetStack:
			if isinstance(w, AFCWidget):
				consonantOrVowel = w.name[0]
				if not isPostTest or random.random() > targetRates[consonantOrVowel]:
					w.selection = random.choice(w.options)
				else:
					w.selection = w.stimulus.id

			self.dataLogger.logWidgetCompletion(w)

	def initialize(self, arguments):
		stack = [
			ButtonPromptWidget('instructions', instructions['intro']),
		]

		sounds = self.loadConsonants('src', FileStimulus)[0]
		sounds.sort(key=lambda x: str(x))
		consonantStack = [
			ButtonPromptWidgetWithSoundBoard('instructions', instructions['consonants'], sounds=sounds)
		]
		for idx,stim in enumerate(self.consonants):
			options = self.makeRandomSubset(self.consonantSet, stim.id)

			stimWidget = AFCWidget(f'consonant-{idx:03}', stim, options)
			stimWidget.stimulusBraced.connect(self.prepareStimulus)
			stimWidget.stimulusTriggered.connect(self.playStimulus)
			consonantStack.append(stimWidget)

		consonantStack.insert(
			int(len(consonantStack)/2),
			ButtonPromptWidget('break', '<center>Time for a break!<br/><br/>Press the button below when you are ready to continue with consonants.</center>')
		)

		sounds = self.loadVowels('src', FileStimulus)[0]
		sounds.sort(key=lambda x: str(x))
		vowelStack = [
			ButtonPromptWidgetWithSoundBoard('instructions', instructions['vowels'], sounds=sounds)
		]
		for idx,stim in enumerate(self.vowels):
			options = self.makeRandomSubset(self.vowelSet, stim.id)

			stimWidget = AFCWidget(f'vowel-{idx:03}', stim, options)
			stimWidget.stimulusBraced.connect(self.prepareStimulus)
			stimWidget.stimulusTriggered.connect(self.playStimulus)
			vowelStack.append(stimWidget)

		vowelStack.insert(
			int(len(vowelStack)/2),
			ButtonPromptWidget('break', '<center>Time for a break!<br/><br/>Press the button below when you are ready to continue with vowels.</center>')
		)

		# counterbalance consonants vs vowels order presentation
		if int(arguments['pid']) % 2 == 0:
			stack += consonantStack + vowelStack
		else:
			stack += vowelStack + consonantStack

		self.widgetStack = stack
		self.dataLogger = DataLogger(arguments, 'phonemes')

	def makeRandomSubset(self, fullSet, correctOption, size=9):
		options = list(fullSet)
		options.remove(correctOption)
		random.shuffle(options)
		options = options[:size-1]

		options.insert(random.randint(0, size-1), correctOption)

		return options


	def _loadStimuliFromFolder(self, pattern, folder, stimClass):
		path = stimPath/folder

		uniqueSet = set()
		stims = []

		for f in list(path.glob('*.*')):
			match = pattern.match(str(f.stem))
			if match is None:
				continue

			phone = match.group(1)
			phone = phoneToHumanMap[phone.upper()]
			stims.append(stimClass(f, phone))

			uniqueSet.add(phone)

		random.shuffle(stims)
		return (stims, sorted(list(uniqueSet)))

	def loadConsonants(self, folder='vtt', stimClass=Stimulus):
		pattern = re.compile(r'[MW][1-5]A(.{1,2})A7M')
		return self._loadStimuliFromFolder(pattern, folder, stimClass)

	def loadVowels(self, folder='vtt', stimClass=Stimulus):
		pattern = re.compile(r'[mw][0-9]{2}(.*)')
		return self._loadStimuliFromFolder(pattern, folder, stimClass)

	def prepareStimulus(self, stimulus):
		self.device.sendFile(stimulus.vtt)

	def playStimulus(self, stimulus):
		self.device.play()

def run():
	app = PhonemeEvalApp()
	app.execute()
