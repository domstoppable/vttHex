import csv
import time
import pkg_resources

from pathlib import Path

scores = []

score_file = Path(pkg_resources.resource_filename(__name__, 'scores.csv'))

if score_file.exists():
	with open(score_file, mode='r') as file:
		scores = list(csv.DictReader(file))
		for idx,scoreItem in enumerate(scores):
			scores[idx]['user_id'] = int(scoreItem['user_id'])
			scores[idx]['score'] = int(scoreItem['score'])
			scores[idx]['updated'] = float(scoreItem['updated'])

def set_score(user_id, points):
	global scores

	user_id = int(user_id)
	points = int(points)

	now = time.time()

	for score in scores:
		if score['user_id'] == user_id:
			score['score'] = points
			score['updated'] = now
			break
	else:
		scores.append({
			'user_id': user_id,
			'score': points,
			'updated': now
		})

	with open(score_file, mode='w') as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=['user_id', 'score', 'updated'])
		writer.writeheader()
		for score in scores:
			writer.writerow(score)
