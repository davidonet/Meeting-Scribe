#!/bin/sh

source .venv/bin/activate
#!/bin/sh

source .venv/bin/activate
python ~/src/Meeting-Scribe/main.py --model large-v3-turbo --lang fr --summarize --anytype "$1"
deactivate
