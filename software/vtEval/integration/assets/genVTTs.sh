#!/bin/bash

PYTHON=/home/dom/.local/share/virtualenvs/software-dVETh4cj/bin/python
LOG=./log.txt

SCRIPT=`realpath -s $0`
SCRIPTPATH=`dirname $SCRIPT`

source "$SCRIPTPATH"/../../genVTTs.sh

function genLabs(){
	for f in wav/*.wav; do
		NAME=$(basename -s .wav "$f")
		WORD=$(echo "$NAME" | cut -d "_" -f 2)
		echo "$WORD" > "wav/$NAME.lab"
	done
}


function doConversions(){
	date > "$LOG"
	resample src wav

	genLabs
	genGrids wav
	genLoudness wav
	genF0s wav

	genVTT wav
	echo "DONE!"
}
