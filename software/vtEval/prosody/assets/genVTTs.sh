#!/bin/bash

PYTHON=/home/dom/.local/share/virtualenvs/software-dVETh4cj/bin/python
LOG=./log.txt

SCRIPT=`realpath -s $0`
SCRIPTPATH=`dirname $SCRIPT`

source "$SCRIPTPATH"/../../genVTTs.sh


function genLabs(){
	for f in wav/*.wav; do
		cp ../../../vttHex/assets/MBOPP/audio/$(basename "$f" .wav).lab wav/
	done
}

function doConversions(){
	date > "$LOG"

	resample src wav

	genLabs
	genGrids wav
	genF0s wav
	genLoudness wav

	genVTT wav

	echo "DONE!"
}
