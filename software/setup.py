#!/usr/bin/env python

from setuptools import setup

setup(
	name='vttHex',
	version='0.1',
	description='-',
	author='Dominic Canare',
	author_email='dom@dominiccanare.com',
	url='https://dominiccanare.com/',
	packages=[
		'vttHex',
		'vtEval', 'vtEval.prosody', 'vtEval.phonemes', 'vtEval.integration',
	],
	install_requires=[ ],
)