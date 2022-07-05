from datetime import datetime, timedelta
import csv
import uuid
import random

now = datetime.now()

with open('aux-data/training-lexicon.csv') as trainingListFile:
	reader = csv.DictReader(trainingListFile)
	stimList = [f'{row["stimulus"]}.vtt' for row in reader]

fields = ['Timestamp', 'PID', 'Level', 'Stimulus', 'Ok', 'LevelAttemptGuid', 'Filename']
for idx in range(6):
	sessionTime = now + timedelta(hours=idx)

	pid = f'8{idx:03}'
	filename = f'StimulusLog-{pid}-FAKEHASH-{sessionTime.strftime("%Y.%m.%d-%H.%M.%S")}'

	print(f'Generating {filename} for PID={pid}...')
	with open(f'data/training/{filename}.csv', 'w') as outputFile:
		outputCSV = csv.DictWriter(outputFile, fieldnames=fields)
		outputCSV.writeheader()

		record = {
			'PID': pid,
			'Level': 'FAKE-LEVEL',
			'Ok': 1,
			'Filename': filename,
			'Timestamp': None,
			'LevelAttemptGuid': None,
			'Stimulus': None,
		}

		for week in range(random.randint(5,7)):
			for session in range(3):
				sessionTime += timedelta(days=random.randint(1,3))
				for level in range(random.randint(4,6)):
					record['LevelAttemptGuid'] = uuid.uuid4().hex
					sessionTime += timedelta(minutes=random.randint(0,1))

					for stim in random.choices(stimList, k=random.randint(40,60)):
						sessionTime += timedelta(seconds=random.randint(1,10))

						record['Timestamp'] = sessionTime.isoformat()
						record['Stimulus'] = stim

						outputCSV.writerow(record)
