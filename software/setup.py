#!/usr/bin/env python

from setuptools import setup

setup(
	name='vtEval',
	version='0.1',
	description='-',
	author='Dominic Canare',
	author_email='dom@dominiccanare.com',
	url='https://dominiccanare.com/',
	packages=[
		'vtEval', 'vtEval.prosody', 'vtEval.phonemes', 'vtEval.integration',
	],
	package_data={
		'vtEval': ['assets/*'],
		'vtEval.prosody': ['assets/video/*', 'assets/vtt/*', 'assets/sentences.csv'],
		'vtEval.phonemes': ['assets/vtt/*', 'assets/src/*.wav'],
		'vtEval.integration': ['assets/vtt/*', 'assets/wav/*.wav']
	},
	install_requires=[ ],
)
