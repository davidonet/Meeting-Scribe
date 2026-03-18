#!/bin/sh

source .venv/bin/activate

if [ -n "$1" ]; then
    # Use the provided audio/video file
    INPUT="$1"
else
    # Record from microphone
    INPUT="./results/output.ogg"
    ffmpeg -f avfoundation -i ":1" -ar 16000 -ac 1 -c:a libopus -b:a 32k "$INPUT"
    RECORDED=1
fi

python ~/dev/Meeting-Scribe/main.py "$INPUT" --model large-v3 --lang fr --transcription-backend groq --summarize --backend claude --anytype --anytype-space "bafyreiahdzaiqt3wbc54zla2uwwyiyeb75vawvxl3z3bwhglqugbwnnvem.tq8dnszek5g3"

if [ "$RECORDED" = "1" ]; then
    rm "$INPUT"
fi

deactivate
