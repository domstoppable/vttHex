#!/bin/bash

PYTHON=/home/dom/.local/share/virtualenvs/software-dVETh4cj/bin/python
LOG=./log.txt

function _resample(){
	gst-launch-1.0 filesrc location="$1" ! wavparse ! audioresample ! audio/x-raw, rate=44100 ! wavenc ! filesink location="$2"
}

function resample(){
	echo "[*    ] 1/5 - Resample"

	mkdir wav 2>&1

	for f in src/*.wav; do
		_resample "$f" "wav/$(basename "$f")" >> "$LOG" 2>&1
	done
}

function genLabs(){
	echo "[**   ] 2/5 - Generate .labs"

	for f in wav/*.wav; do
		NAME=$(basename -s .wav "$f")
		WORD=$(echo "$NAME" | cut -d "_" -f 2)
		echo "$WORD" >> "wav/$NAME.lab"
	done
}

function genGrids(){
	echo "[***  ] 3/5 - Generate TextGrids"

	MFA=~/code/montreal-forced-aligner
	WAV_DIR=wav
	LEX_FILE=./lexicon.txt
	GRID_DIR=$WAV_DIR/grids

	mkdir $GRID_DIR >> "$LOG" 2>&1
	"$MFA/bin/mfa_align" -v -q -j 16 -d "$WAV_DIR" "$LEX_FILE" english "$GRID_DIR" >> "$LOG" 2>&1
	mv "$GRID_DIR"/*/*.TextGrid "$GRID_DIR"
	rm -r "$GRID_DIR"/wav
	cat "$WAV_DIR/oovs_found.txt" >> "$LOG" 2>&1
	cat "$WAV_DIR/oovs_found.txt" 2>/dev/null
}

function genF0s(){
	echo "[**** ] 4/5 - Generate F0s"
	cd wav/
	~/code/FCN-f0/run.sh >> "$LOG" 2>&1
	cd ..
}

function genVTT(){
	echo "[*****] 5/5 - Generate VTT"

	echo "$PYTHON" ~/code/vttHex/software/vttHex/makeVttBinary.py wav/"*.wav" >> "$LOG"
	"$PYTHON" ~/code/vttHex/software/vttHex/makeVttBinary.py wav/*.wav >> "$LOG" 2>&1
	mkdir vtt >> "$LOG" 2>/dev/null
	mv *.vtt vtt/
}

function fullConvert(){
	date > "$LOG"
	resample
	genLabs
	genGrids
	genF0s
	genVTT
	echo "DONE!"
}
