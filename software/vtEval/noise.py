from PySide2 import QtCore, QtMultimedia

class FadeSound:
	def __init__(self, url):
		self.soundEffect = QtMultimedia.QSoundEffect()
		self.soundEffect.setSource(QtCore.QUrl.fromLocalFile(url))
		self.soundEffect.setLoopCount(QtMultimedia.QSoundEffect.Infinite)

		self.timer = QtCore.QTimer()
		self.timer.setInterval(10)
		self.timer.timeout.connect(self.adjust)

		self.adjustment = .025
		self.adjustmentDirection = 1

		self.fadeInMax = 1.0

	def fadeIn(self, fadeInMax=None):
		if fadeInMax is not None:
			self.fadeInMax = fadeInMax

		self.adjustmentDirection = 1
		self.soundEffect.setVolume(0)
		self.soundEffect.play()
		self.timer.start()

	def fadeOut(self):
		self.adjustmentDirection = -1
		self.timer.start()

	def adjust(self):
		volume = self.soundEffect.volume()

		fadeInComplete = self.adjustmentDirection > 0 and volume >= self.fadeInMax
		fadeOutComplete = self.adjustmentDirection < 0 and volume <= 0.0

		if fadeInComplete or fadeOutComplete:
			self.timer.stop()
		else:
			self.soundEffect.setVolume(volume + (self.adjustment * self.adjustmentDirection))

noise = None

def play(fadeInMax=1.0):
	global noise

	if noise is None:
		noise = FadeSound('vtEval/noise.wav')

	noise.fadeIn(fadeInMax)

def stop():
	global noise

	if noise is not None:
		noise.fadeOut()
