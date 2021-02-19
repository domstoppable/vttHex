class Participant():
	def __init__(self, id, name):
		self.id = id
		self.name = name

	def __lt__(self, b):
		return repr(self) < repr(b)

	def __repr__(self):
		try:
			return f'{int(self.id):04} - {self.name}'
		except:
			return f'{self.id} - {self.name}'