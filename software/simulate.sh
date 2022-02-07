#!/bin/bash

CONDITIONS=( "Pre-test" "Post-test")
PARTICIPANTS=( "8000" "8001" "8002" "8003" "8004" "8005" )
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
