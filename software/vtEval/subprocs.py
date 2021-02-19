import itertools
from itertools import permutations

procs = [
	'phonemes',
	'prosody',
	'integration',
]

procCombos = list(permutations(procs))

def orderedByPID(pid):
	return procCombos[int(pid) % len(procCombos)]