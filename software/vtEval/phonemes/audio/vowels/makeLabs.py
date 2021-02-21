import re
from pathlib import Path

hillenbrandToArpabet = {
	'aw':'AA',
	'ae':'AE',
	'uh':'AH',
	'ah':'AO',
	'eh':'EH',
	'er':'ER',
	'ei':'EY',
	'ih':'IH',
	'iy':'IY',
	'oa':'OW',
	'oo':'UH',
	'uw':'UW',
}

pattern = re.compile(r'[mw]\d\d(..).wav')
for f in Path('.').glob('*.wav'):
	match = pattern.match(f.name)
	outFile = Path(f.stem + '.lab')
	with outFile.open('w') as output:
		v = match.groups(1)[0]
		v = hillenbrandToArpabet[v]
		print(f'H{v}D', file=output)
