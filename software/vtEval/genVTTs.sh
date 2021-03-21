#!/bin/bash

PYTHON=/home/dom/.local/share/virtualenvs/software-dVETh4cj/bin/python
LOG=./log.txt


function resampleWav(){
	inputFile="$1"
	outputFile="$2"

	gst-launch-1.0 filesrc location="$inputFile" ! \
		wavparse ! \
		audioconvert ! "audio/x-raw,channels=1,format=S16LE" ! \
		audioresample ! audio/x-raw, rate=44100 ! \
		wavenc ! \
		filesink location="$outputFile.tmp.wav"

	duration=$(soxi -D $outputFile.tmp.wav)
	padLength=$(echo ".5-$duration" | bc)
	if [[ $padLength != -* ]]; then
		echo "pad needed $padLength"
		sox "$outputFile.tmp.wav" "$outputFile.tmp-pad.wav" pad $padLength
		mv "$outputFile.tmp-pad.wav" "$outputFile.tmp.wav"
	fi
	gain=$(loudgain -qo "$outputFile.tmp.wav" 2>/dev/null | tail -n 1 | cut -f 3)
	sox "$outputFile.tmp.wav" "$2" gain $gain
	rm "$outputFile.tmp.wav"
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

