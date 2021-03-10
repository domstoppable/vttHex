#!/bin/bash

PYTHON=/home/dom/.local/share/virtualenvs/software-dVETh4cj/bin/python
LOG=./log.txt

SCRIPT=`realpath -s $0`
SCRIPTPATH=`dirname $SCRIPT`

source "$SCRIPTPATH"/../../genVTTs.sh

function doConversions(){
	date > "$LOG"
	resample src wav

	genGrids wav
	genLoudness wav
	genF0s wav

	genVTT wav

	echo "DONE!"
}
