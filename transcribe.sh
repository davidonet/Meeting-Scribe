#!/bin/sh

source .venv/bin/activate

OUTPUT="${2:-results/}"

if [ -n "$1" ]; then
    # Use the provided audio/video file
    INPUT="$1"
else
    # Record from microphone
    INPUT="$OUTPUT/output.ogg"
    ffmpeg -f avfoundation -i ":1" -ar 16000 -ac 1 -c:a libopus -b:a 32k "$INPUT"
    RECORDED=1
fi

python ~/dev/Meeting-Scribe/main.py "$INPUT" --output "$OUTPUT" --model large-v3 --lang fr --transcription-backend groq --summarize --backend claude

if [ "$RECORDED" = "1" ] && [ $? -eq 0 ]; then
    rm "$INPUT"
fi

deactivate
