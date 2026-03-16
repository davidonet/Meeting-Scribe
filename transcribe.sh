#!/bin/sh

source .venv/bin/activate
python ~/dev/Meeting-Scribe/main.py "$1" --model large-v3-turbo --lang fr --summarize --backend mlx
deactivate
