from pathlib import Path
import csv

from . import tools

def loadCSV(f):
	data = []
	with open(tools.findAsset(f), 'r') as csvFile:
		reader = csv.DictReader(csvFile)
		for row in reader:
			data.append(row)

	return data

def loadSentences(sentenceType):
	sentences = loadCSV(f'MBOPP/{sentenceType}-sentences.csv')
	for sentence in sentences:
		id = sentence['ID']
		sentence['filename'] = f'{sentenceType}{id}_'+'pitch{pitch}_time{time}'
		if 'Start' in sentence:
			sentence['desc'] = ' '.join([sentence['Start'], sentence['Focus 1'], sentence['Focus 2']])
		else:
			sentence['desc'] = sentence['Early Start'].replace(',', '')


	return sentences

def _checkForAlignments(sentenceList):
	transcriptFolder = Path(tools.findAsset(f'MBOPP/audio/'))

	for sentence in sentenceList:
		for inc in increments:
			files = [
				sentence['filename'].format(pitch=inc, time=inc),
				sentence['filename'].format(pitch=50, time=inc),
				sentence['filename'].format(pitch=inc, time=50),
			]
			for f in files:
				name = Path(f).stem
				labFile = transcriptFolder / f'{name}.lab'
				if not labFile.exists():
					with labFile.open('w') as labFileHandle:
						print('creating', labFile)
						print(sentence['desc'].upper(), file=labFileHandle)

def checkForAlignments():
	_checkForAlignments(focusSentences)
	_checkForAlignments(phraseSentences)

focusSentences = loadSentences('focus')
phraseSentences = loadSentences('phrase')

increments = list(range(0, 101, 5))
for x in [45, 50, 55]:
	increments.remove(x)


if __name__ == '__main__':
	print('Checking for alignments...')
	checkForAlignments()
