import traceback, sys
import json

from flask import Flask

import score_backend

app = Flask(__name__)

@app.route('/api/scores/')
def get_scores():
	scores = sorted(score_backend.scores, key=lambda item: int(item['score']), reverse=True)
	return json.dumps({'scores': scores})

@app.route('/api/score/<int:user_id>/<int:score>/<int:checksum>', methods=['POST'])
def update_score(user_id, score, checksum):
	try:
		validateChecksum = score % (user_id+7)
		if validateChecksum != checksum:
			return 'error', 400

		score_backend.set_score(user_id, score)
		return ''
	except:
		print('Error', file=sys.stderr)
		traceback.print_stack()

		return 'error', 500
