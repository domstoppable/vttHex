import re
from pathlib import Path

pattern = re.compile(r'[MW]\d(A.{1,2}A)7M.WAV')
for f in Path('.').glob('*.WAV'):
	match = pattern.match(f.name)
	outFile = Path(f.stem + '.lab')
	with outFile.open('w') as output:
		print(match.groups(1)[0], file=output)