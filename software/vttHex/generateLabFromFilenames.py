import sys
import pathlib
import re
from tqdm import tqdm

expr = re.compile('[FfMm][12]-?(.*)')
progressBar = tqdm(sys.argv[1:])
for filename in progressBar:
	progressBar.set_description(filename)
	filePath = pathlib.Path(filename)

	result = expr.match(filePath.stem)
	if result:
		word = result.groups()[0]
		outputFile = filePath.parent / (filePath.stem + '.lab')

		print('Writing', word, 'to', str(outputFile))

		with outputFile.open('w') as labFile:
			labFile.write(f'{word}\n')
	else:
		print('Could not match', filename)
