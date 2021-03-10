#!/bin/bash

PYTHON=/home/dom/.local/share/virtualenvs/software-dVETh4cj/bin/python
LOG=./log.txt


function resampleWav(){
	gst-launch-1.0 filesrc location="$1" ! \
		wavparse ! \
		audioconvert ! \
		rganalysis ! rgvolume ! rglimiter ! \
		audioconvert ! "audio/x-raw,channels=1,format=S16LE" ! \
		audioresample ! audio/x-raw, rate=44100 ! \
		wavenc ! \
		filesink location="$2"
}

function resample(){
	echo "Resampling from $1 to $2..."

	src="$1"
	target="$2"

	mkdir "$target" 2>&1

	for f in "$src"/*.[Ww][Aa][Vv]; do
		resampleWav "$f" "$target/$(basename "$f")" >> "$LOG" 2>&1
	done
}

function genGrids(){
	echo "Generating TextGrids"

	WAV_DIR="$1"
	LEX_FILE=./lexicon.txt
	MFA=~/code/montreal-forced-aligner
	GRID_DIR=$WAV_DIR/grids

	mkdir $GRID_DIR >> "$LOG" 2>&1
	"$MFA/bin/mfa_align" -v -q -j 16 -d "$WAV_DIR" "$LEX_FILE" english "$GRID_DIR" >> "$LOG" 2>&1
	mv "$GRID_DIR"/*/*.TextGrid "$GRID_DIR"
	cat "$WAV_DIR/oovs_found.txt" >> "$LOG" 2>&1
	cat "$WAV_DIR/oovs_found.txt" 2>/dev/null
}

function genF0s(){
	echo "Generating pitch CSVs"
	p=$(pwd)
	cd "$1"
	~/code/FCN-f0/run.sh >> "$LOG" 2>&1
	cd "$p"
}

function genLoudness(){
	echo "Generating loudness CSVs"
	"$PYTHON" -m vttHex.calcLoudness "$1"/*.[Ww][Aa][Vv] >> "$LOG" 2>&1
}

function genVTT(){
	echo "Generate VTT"

	"$PYTHON" ~/code/vttHex/software/vttHex/makeVttBinary.py "$1"/*.[Ww][Aa][Vv] >> "$LOG" 2>&1
	mkdir vtt >> "$LOG" 2>/dev/null
	mv *.vtt vtt/
}

