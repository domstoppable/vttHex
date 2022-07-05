import csv

phones = ['AA','AE','AH','AO','AW','AY','B','CH','D','DH','EH','ER','EY','F','G','HH','IH','IY','JH','K','L','M','N','NG','OW','OY','P','R','S','SH','T','TH','UH','UW','V','W','Y','Z','ZH']

lexiconFile = '/home/dom/code/vttHex/software/aux-data/'
with open(lexiconFile, 'r') as inputFile:
	with open(f'{lexiconFile}-counts.csv', 'w') as outputFile:
		dictWriter = csv.DictWriter(outputFile, fieldnames=['word','pronounciation']+phones)
		dictWriter.writeheader()

		for line in inputFile:
			print('.', end='')

			record = {phone: 0 for phone in phones}
			record['word'],record['pronounciation'] = line.strip().split(' ', 1)

			wordPhones = record['pronounciation'].replace('0', '').replace('1', '').replace('2', '').replace('3', '')
			wordPhones = wordPhones.split()
			for phone in wordPhones:
				record[phone] += 1

			dictWriter.writerow(record)

print('done')
