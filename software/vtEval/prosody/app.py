import sys
import re
import time
import random
import csv

from enum import Enum, auto
from pathlib import Path

from PySide2 import QtCore, QtGui, QtWidgets

from vtEval.vtEvalApp import *
from vtEval import serial, noise
from vttHex.parseVTT import loadVTTFile

instructions = {
	'intro': '''<html>
			<h1>Prosody Evaluation</h1>
			<p>This evaluation is separated into two parts measuring your perception of different aspects of sentence structure. Both parts of this evaluation follow a similar structure:</p>
			<ul>
				<li>A sentence will appear in a box on the screen, and you will have a short time to read it silently and consider it.</li>
				<li>Two different versions of the <u>underlined</u> section of that sentence will be vibrated on your arm. One will match the <u>underlined</u> part of the sentence on the screen, the other will not. They will be similar but not identical, and they cannot be repeated.</li>
				<li>You will then be asked to select which of the two vibrations felt most like the <u>underlined</u> section of the sentence on the screen. If you are uncertain, make a guess.</li>
			</ul>
			<p>You will hear static to cover-up sounds made by the vibrations of the device. You should rely solely on the vibrating sensations themselves when making decisions.</p>
			<p>Opportunities for breaks will be provided as you proceed.</p>
			<hr/>
			<p>Click the <strong>Continue</strong> button below when you are ready to begin the first part of this evaluation. More instructions will be provided on the next screen.</p>
		</html>''',
	'focus': '''
		<html>
			<h2>Focus Evaluation</h2>
			<p>For this part of the evaluation, a sentence will appear in the box with an emphasized word as indicated with <i>ITALIC, CAPITALIZED</i> letters.</p>
			<p>When the vibration options are presented, one option will emphasize the italicized word, and the other will emphasize a different word in the sentence.</p>
			<p>You should select the vibration option which emphasizes the italicized word. If you are uncertain, make a guess.</p>
			<p>Remember, only the <u>underlined</u> section of the sentence will be vibrated, and the options cannot be repeated.</p>
			<hr/>
			<p>If you have any questions, please ask them now. Otherwise, click the button below when you are ready to begin.</p>
		</html>
		''',
	'phrase': '''
		<html>
			<h2>Phrase Boundary Evaluation</h2>
			<p>For this part of the evaluation, each sentence will contain a phrase boundary indicated by a comma, which will either be in the middle or at the end of the <u>underlined</u> section.</p>
			<p>When the vibration options are presented, one option will have the comma in the same place as the sentence in the box, and the other will have a comma in a different place.</p>
			<p>You should select the vibration option which matches the comma placement of the sentence in the box. If you are uncertain, make a guess.</p>
			<p>Remember, only the <u>underlined</u> section of the sentence will be vibrated, and the options cannot be repeated.</p>
			<hr/>
			<p>If you have any questions, please ask them now. Otherwise, click the button below when you are ready to begin.</p>
		</html>
		''',
}

sentences = {
	'focus': {},
	'phrase': {},
}
with open(locateAsset('sentences.csv'), 'r') as sentenceFile:
	reader = csv.DictReader(sentenceFile)
	for row in reader:
		sentences[row['type']][str(row['id'])] = {
			'early': row['early'],
			'late': row['late'],
		}

def getSentence(typeName, typeIdx, earlyOrLate):
	return sentences[typeName][typeIdx][earlyOrLate]

class StimPair:
	def __init__(self, typeName, typeIdx, earlyStim=None, lateStim=None):
		self.type = typeName
		self.typeIdx = typeIdx
		self.earlyStim = earlyStim
		self.lateStim = lateStim

	def getMaxDurationMS(self):
		return max(self.earlyStim.vtt.getDuration(), self.lateStim.vtt.getDuration())

class AFCWidget(StateWidget):
	stimulusBraced = QtCore.Signal(object)
	stimulusTriggered = QtCore.Signal(object)

	def __init__(self, name, stimPair, earlyOrLate, parent=None):
		super().__init__(name=name, parent=parent)

		self.delayBeforeStimulus = 0

		self.stimPair = stimPair
		self.earlyOrLate = earlyOrLate

		self.stimulus = getattr(stimPair, f'{earlyOrLate}Stim')
		self.selection = None

		self.setLayout(QtWidgets.QVBoxLayout())

		textWidgetContainer = QtWidgets.QWidget(parent=self)
		textWidgetContainer.setLayout(QtWidgets.QVBoxLayout())

		label = QtWidgets.QLabel(parent=self)
		label.setText(' ')
		label.setAlignment(QtCore.Qt.AlignCenter)
		label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		textWidgetContainer.layout().addWidget(label)

		self.sentenceLabel = QtWidgets.QLabel(parent=self)
		self.sentenceLabel.setStyleSheet('border: 3px solid #fff; background: #222; color: #ddd')
		self.sentenceLabel.setAlignment(QtCore.Qt.AlignCenter)
		self.sentenceLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		textWidgetContainer.layout().addWidget(self.sentenceLabel)

		self.promptLabel = QtWidgets.QLabel(parent=self)
		self.promptLabel.setAlignment(QtCore.Qt.AlignCenter)
		self.promptLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

		self.layout().addWidget(textWidgetContainer, stretch=2)

		self.timerProgressBar = TimerProgressBar()
		self.layout().addWidget(self.timerProgressBar)
		self.layout().setAlignment(self.timerProgressBar, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)

		self.buttonContainer = QtWidgets.QWidget()
		self.buttonContainer.setLayout(QtWidgets.QHBoxLayout())
		self.buttonContainer.layout().setSpacing(20)

		self.stims = [stimPair.earlyStim, stimPair.lateStim]
		choices = ['early', 'late']
		if random.choice([False, True]):
			self.stims = list(reversed(self.stims))
			choices = list(reversed(choices))

		self.choiceButtons = [
			self.setupButton('A', choices[0]),
			self.setupButton('B', choices[1]),
		]

		self.orButton = GhostButton(text='⇔')

		self.buttonContainer.layout().addWidget(self.choiceButtons[0])
		self.buttonContainer.layout().addWidget(self.orButton)
		self.buttonContainer.layout().addWidget(self.choiceButtons[1])

		self.layout().addWidget(self.buttonContainer, stretch=3)
		self.layout().addWidget(self.promptLabel, stretch=1)

	def setupButton(self, text, choice):
		button = QtWidgets.QPushButton(parent=self, text=text)
		button.clicked.connect(lambda _=None, text=text: self.onChoiceMade(choice))
		button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

		return button

	def onStarted(self):
		self.promptLabel.setText('')
		self.sentenceLabel.setText('')
		self.buttonContainer.setDisabled(True)

		self.steps = [
			lambda: self.showSentence(),
			lambda: self.playStim(0),
			lambda: self.prepSecondStim(),
			lambda: self.playStim(1),
			lambda: self.prepInput(),
			lambda: self.getInput()
		]
		noise.play()
		QtCore.QTimer.singleShot(self.delayBeforeStimulus, self.nextStep)

	def nextStep(self):
		step = self.steps.pop(0)
		step()

	def showSentence(self):
		sentence = getSentence(self.stimPair.type, self.stimPair.typeIdx, self.earlyOrLate)
		self.sentenceLabel.setText(sentence.replace('</u>', '</u><span style="color: #888">') + '</span>')
		self.stimulusBraced.emit(self.stims[0])

		self.userReadingTimer = QtCore.QTimer()
		self.userReadingTimer.setInterval(5000)
		self.userReadingTimer.timeout.connect(self.nextStep)
		self.userReadingTimer.setSingleShot(True)

		self.timerProgressBar.watch(self.userReadingTimer)

		self.userReadingTimer.start()

	def playStim(self, idx):
		self.choiceButtons[idx].setStyleSheet('background-color: #6cc')

		self.stimulusTriggered.emit(self.stims[idx])
		QtCore.QTimer.singleShot(self.stimPair.getMaxDurationMS() + 500, self.nextStep)

	def prepSecondStim(self):
		self.choiceButtons[0].setStyleSheet('')
		self.stimulusBraced.emit(self.stims[1])
		QtCore.QTimer.singleShot(1000, self.nextStep)

	def prepInput(self):
		self.choiceButtons[1].setStyleSheet('')
		QtCore.QTimer.singleShot(500, self.nextStep)

	def getInput(self):
		self.promptLabel.setText('Which version was a better match for the <u>underlined</u> section?')
		self.buttonContainer.setDisabled(False)
		noise.stop()
		self.orButton.setFocus()

	def onChoiceMade(self, option):
		self.selection = option
		self.finished.emit()

	def keyPressEvent(self, keyEvent):
		super().keyPressEvent(keyEvent)

		if keyEvent.key() == QtCore.Qt.Key_A:
			self.choiceButtons[0].setFocus()

		elif keyEvent.key() == QtCore.Qt.Key_D:
			self.choiceButtons[1].setFocus()

	def __setstate__(self, state):
		self.__init__(state['name'], state['stimPair'], state['earlyOrLate'])

class TimerProgressBar(QtWidgets.QProgressBar):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.observedTimer = None

		self.refreshTimer = QtCore.QTimer()
		self.refreshTimer.setInterval(1000//60)
		self.refreshTimer.timeout.connect(self.refresh)

		self.setMaximumWidth(800)
		self.setMinimumWidth(800)

		self.setTextVisible(False)
		self.setMaximum(800)

		sp_retain = self.sizePolicy()
		sp_retain.setRetainSizeWhenHidden(True)
		self.setSizePolicy(sp_retain)

	def watch(self, timer):
		self.observedTimer = timer

		self.refreshTimer.start()
		self.observedTimer.timeout.connect(self.onTimerFinished)

	def refresh(self):
		margin = 500
		maxTime = self.observedTimer.interval() - margin
		elapsedTime = self.observedTimer.interval() - self.observedTimer.remainingTime()
		value = elapsedTime / maxTime
		self.setValue(min(value, 1.0) * self.maximum())

	def onTimerFinished(self):
		self.refreshTimer.stop()
		self.setValue(self.maximum())
		self.hide()

class ProsodyEvalApp(VtEvalApp):
	def __init__(self):
		super().__init__('Prosody Evaluation')

	def simulate(self):
		isPostTest = self.arguments['condition'] == 'Post-test'

		opposites = {
			'early': 'late',
			'late': 'early'
		}

		for w in self.widgetStack:
			if isinstance(w, AFCWidget):
				if isPostTest and random.random() > 0.65:
					w.selection = w.earlyOrLate
				else:
					if random.random() > 0.5:
						w.selection = w.earlyOrLate
					else:
						w.selection = opposites[w.earlyOrLate]

			self.dataLogger.logWidgetCompletion(w)

	def initialize(self, arguments):
		focusStack = self.buildSubStack('focus')
		phraseStack = self.buildSubStack('phrase')

		self.widgetStack = [ TextInstructionsScreen('instructions', instructions['intro']) ]

		# counterbalance order of focus vs phrase boundaries
		if int(arguments['pid']) % 2 == 0:
			self.widgetStack += focusStack + phraseStack
		else:
			self.widgetStack += phraseStack + focusStack

	def startDataLogger(self):
		self.dataLogger = DataLogger(self.arguments, 'prosody')

	def buildSubStack(self, name):
		stack = []
		stimSets = self.loadStimuliFromFolder(name, 25, 75)
		choices = ['early', 'late']

		for i,stimSet in enumerate(stimSets):
			stack.append(self.makeStimWidget(name=name, stimPair=stimSet, earlyOrLate='early'))
			stack.append(self.makeStimWidget(name=name, stimPair=stimSet, earlyOrLate='late'))
			# first half will have 2x early, 2nd half will have 2x late
			if i<len(stimSets)/2:
				bonusMode = 'early'
			else:
				bonusMode = 'late'
			stack.append(self.makeStimWidget(name=name, stimPair=stimSet, earlyOrLate=bonusMode))

		random.shuffle(stack)
		for idx,stimWidget in enumerate(stack):
			stimWidget.name += f'-{idx}'

		breaks = 5
		breakEveryN = len(stack)/(breaks+1)
		for breakIdx in range(breaks,0,-1):
			pos = int(breakIdx * breakEveryN)
			breakWidget = ButtonPromptWidget('break', '<center>Time for a break!<br/><br/>Press the button below when you are ready to continue.</center>')

			stack.insert(pos, breakWidget)

		videoURL = QtCore.QUrl.fromLocalFile(locateAsset(f'video/{name}.wmv'))
		stack.insert(0, ButtonPromptWidgetWithVideo('instructions', instructions[name], videoURL=videoURL))

		return stack

	def makeStimWidget(self, name, stimPair, earlyOrLate):
		stimWidget = AFCWidget(name=name, stimPair=stimPair, earlyOrLate=earlyOrLate)
		stimWidget.stimulusBraced.connect(self.prepareStimulus)
		stimWidget.stimulusTriggered.connect(self.playStimulus)

		return stimWidget

	def loadStimuliFromFolder(self, prefix, earlyLevel, lateLevel):
		stimSets = {}

		path = Path(locateAsset('vtt'))

		pattern = re.compile(rf'{prefix}(\d\d?)_.*')

		levels = {
			'early': earlyLevel,
			'late': lateLevel
		}
		for levelName,level in levels.items():
			for f in list(path.glob(f'{prefix}*_pitch{level}_time{level}*.vtt')):
				match = pattern.match(f.stem)
				if match is None:
					continue

				stimSetID = match.groups(1)[0]
				if not stimSetID in stimSets:
					stimSets[stimSetID] = StimPair(typeName=prefix, typeIdx=stimSetID)

				setattr(stimSets[stimSetID], f'{levelName}Stim', Stimulus(f, levelName))

		stimSets = list(stimSets.values())
		random.shuffle(stimSets)
		return stimSets

def run():
	app = ProsodyEvalApp()
	app.execute()

	if len(app.widgetStack) > 0:
		sys.exit(1)
