import pkg_resources

phoneLayout = ['B', 'D', 'G', 'HH', 'DH', None, 'P', 'T', 'K', 'TH', 'F', None, 'M', 'N', 'SH', 'S', 'V', 'W', 'Y', 'NG', 'CH', 'ZH', 'Z', 'L', 'R', 'ER', 'JH', 'AH', 'AO', 'AA', 'AW', 'UW', 'UH', 'OW', 'OY', 'AX', 'IY', 'EY', 'IH', 'EH', 'AE', 'AY', ]
vowels = ['AA','AE','AH','AO','AW','AY','EH','ER','EY','IY','OW','OY']

def findAsset(*resourceParts):
	resource = '/'.join(['assets'] + list(resourceParts))
	return pkg_resources.resource_filename(__name__, resource)

class PhonePlayer():
	def open(self, filename):
		from praatio import tgio

		self.textgrid = tgio.openTextgrid(filename)
		self.phonegrid = self.textgrid.tierDict['phones'].entryList

		self.idx = 0
		self.accumulatedTime = 0

	def update(self, delta):
		self.accumulatedTime += delta
		done = False

		actions = []

		while not done and self.idx < len(self.phonegrid):
			start, stop, label = self.phonegrid[self.idx]
			label = label[:2]

			pop = False
			if self.accumulatedTime > start:
				actions.append({'phone': label, 'enable': True})
				pop = True
			if self.accumulatedTime > stop:
				actions.append({'phone': label, 'enable': False})
				pop = True

			if pop:
				self.idx += 1
			else:
				done = True


		if self.idx >= len(self.phonegrid):
			actions.append(None)

		#print(f'{actions = }')
		return actions