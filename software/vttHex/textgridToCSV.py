import sys, os
import textgrids
import csv

for arg in sys.argv[1:]:
	name, ext = os.path.splitext(arg)
	with open(name + '.TextGrid.csv', 'w', newline='') as csvFile:
		print(csvFile.name)
		writer = csv.DictWriter(csvFile, fieldnames=['tier', 'text', 'xmin', 'xmax', 'nostress'])
		writer.writeheader()

		grid = textgrids.TextGrid(arg)
		for tierName, tier in grid.items():
			for interval in tier:
				row = dict(interval.__dict__)
				row['tier'] = tierName
				row['nostress'] = row['text'].rstrip('1234567890')
				writer.writerow(row)
