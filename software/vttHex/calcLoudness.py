import sys

from pathlib import Path
import wave
import csv

import numpy as np
import scipy
from mosqito.functions.shared.load import load
from mosqito.functions.loudness_zwicker.comp_loudness import comp_loudness

#from vttHex.tools import SignalPlayer, formatSignalAsBytes

def calcLoudness(wavPath, resampleTo=None):
	signal, fs = load(False, wavPath, calib = 2 * 2**0.5)
	loudness = comp_loudness(False, signal, fs, field_type='free')

	N = loudness['values']
	if resampleTo is not None:
		N = scipy.signal.resample(N, sampleCount)

	return N

def makeLoudnessCSV(path):
	sampleRate = 0
	with wave.open(path, "rb") as wavFile:
		sampleRate = wavFile.getframerate()
		frameCount = wavFile.getnframes()
		duration = frameCount/sampleRate

	path = Path(path)
	try:
		loudness = calcLoudness(str(path))
	except Exception as exc:
		print(f'Loudness calc failed for {path.name}', exc)
		return

	frameTime = duration / len(loudness)

	outputPath = path.parent/(path.stem+'.loudness.csv')
	with open(outputPath, 'w') as outputFile:
		csvWriter = csv.writer(outputFile)
		csvWriter.writerow(['time', 'loudness'])

		for i,l in enumerate(loudness):
			csvWriter.writerow([i*frameTime,l])

	print('Wrote', outputPath.name)

if __name__ == '__main__':
	from multiprocessing import Pool

	with Pool() as pool:
		pool.map(makeLoudnessCSV, sys.argv[1:])
