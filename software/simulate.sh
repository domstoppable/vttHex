#!/bin/bash

CONDITIONS=( "Pre-test" "Post-test")
PARTICIPANTS=( "000" "001" "002" "003" "004" "005" )
TESTS=( "phonemes" "integration" "prosody")

for CONDITION in "${CONDITIONS[@]}"; do
	for PID in "${PARTICIPANTS[@]}"; do
		for TEST in "${TESTS[@]}"; do
			python -m "vtEval.$TEST" \
				--facilitator "simulator" \
				--pid "$PID" \
				--condition "$CONDITION" \
				--device "/dev/null" \
				--simulate &
		done
	done
done

wait $(jobs -p)
