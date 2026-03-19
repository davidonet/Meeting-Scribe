# MeetingScribe

> Drop a meeting recording (or record live) into your terminal and get back a clean, speaker-labelled transcript plus structured meeting notes — fully offline with local models, or blazing-fast with cloud APIs. fork from https://github.com/JuanLara18/Meeting-Scribe

---

## Features

| Feature | Description |
|---------|-------------|
| **Multilingual transcription** | OpenAI Whisper (MLX on Apple Silicon, CPU on Intel, or Groq cloud API) |
| **Speaker diarization** | Custom MFCC + agglomerative clustering — no Hugging Face account required |
| **Live recording** | `transcribe.sh` records directly from your microphone (or aggregate device capturing full meeting audio) |
| **File input** | Pass any audio/video file (`.mp4`, `.mkv`, `.mov`, `.ogg`, `.m4a`, …) |
| **Meeting notes** | Structured Markdown notes (participants, summary, decisions, action items) via local MLX model, Claude, or Groq |
| **Context files** | Feed domain-specific vocabulary/instructions to the summarizer for better notes |
| **Anytype publishing** | One flag to push notes straight into your Anytype space |
| **Summarize-only mode** | Re-generate notes from an existing transcript without re-transcribing |
| **Fully offline option** | MLX transcription + MLX summarization — zero data leaves your machine |

---

## Quick Start

**Prerequisites:** Python 3.10+, `ffmpeg` ≥ 4.2

```bash
# 1. Clone
git clone https://github.com/JuanLara18/Meeting-Scribe.git
cd Meeting-Scribe

# 2. Virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Dependencies
pip install -r config/requirements.txt

# 4. Run on a file
python main.py path/to/meeting.mp4
```

Results land in `results/`:

```
results/
├── transcript.md        # speaker-labelled Markdown transcript
├── transcript.json      # raw structured data
└── audio.wav            # extracted audio (useful for debugging)
```

With `--summarize`:

```
results/
└── meeting_notes.md     # AI-generated notes with decisions & action items
```

### Environment Variables

Create a `.env` file at the project root — it is loaded automatically:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...   # --backend claude
GROQ_API_KEY=gsk_...           # --transcription-backend groq  /  --backend groq
ANYTYPE_KEY=...                # --anytype
ANYTYPE_SPACE=...              # target space (alternative to --anytype-space)
```

---

## Usage

```bash
python main.py [VIDEO_PATH] [OPTIONS]
```

### All Options

| Option | Default | Description |
|--------|---------|-------------|
| `VIDEO_PATH` | — | Audio or video file to process. Optional with `--summarize-only`. |
| `--output`, `-o` | `results/` | Folder where output files are written |
| `--lang` | auto | ISO-639-1 language code (`fr`, `en`, `es`, …). Skips auto-detection when set. |
| `--model` | `base` | Whisper model size (see table below) |
| `--transcription-backend` | `mlx` (arm64) / `whisper` (Intel) | `mlx` — Apple Silicon GPU · `whisper` — CPU · `groq` — Groq cloud API |
| `--summarize` | off | Generate meeting notes after transcription |
| `--summarize-only` | off | Skip transcription; regenerate notes from an existing `transcript.md` |
| `--backend` | `mlx` | Summarization backend: `mlx` · `claude` · `groq` |
| `--context` | `contexts/default.md` | Path to a domain context `.md` file (appended to the summarizer system prompt) |
| `--anytype` | off | Publish notes to Anytype |
| `--anytype-space` | env / auto | Anytype space ID. Falls back to `ANYTYPE_SPACE` env var, then auto-detects first space. |
| `--verbose`, `-v` | off | Debug-level logging |

### Whisper Models

| Model | Params | Speed | Quality | Best for |
|-------|--------|-------|---------|----------|
| `tiny` | 39 M | ⚡⚡⚡⚡ | ★☆☆☆ | Quick tests |
| `base` | 74 M | ⚡⚡⚡ | ★★☆☆ | Default — good balance |
| `small` | 244 M | ⚡⚡ | ★★★☆ | Better accuracy |
| `medium` | 769 M | ⚡ | ★★★★ | High accuracy |
| `large-v3` | 1550 M | 🐢 | ★★★★ | Best accuracy |
| `large-v3-turbo` | 809 M | ⚡⚡ | ★★★★ | Best accuracy / speed trade-off |

> With Groq `--transcription-backend groq`, `tiny`/`base`/`small`/`large-v3-turbo` map to `whisper-large-v3-turbo` and `medium`/`large-v2`/`large-v3` map to `whisper-large-v3` — you always get the best available Groq model.

### Usage Examples

```bash
# Local transcription (Apple Silicon, no API key)
python main.py meeting.mp4

# Specify language, bigger model
python main.py reunion.mp4 --lang fr --model large-v3-turbo

# Fast cloud transcription + local summarization
python main.py meeting.mp4 --transcription-backend groq --summarize

# Full cloud pipeline: Groq transcription + Claude notes
python main.py meeting.mp4 --transcription-backend groq \
  --summarize --backend claude

# Domain-specific notes (custom context)
python main.py meeting.mp4 --summarize --backend claude \
  --context contexts/my-project.md

# Re-generate notes without re-transcribing
python main.py --summarize-only --backend claude

# Publish to a specific Anytype space
python main.py meeting.mp4 --summarize --anytype \
  --anytype-space "your-space-id"

# Custom output folder + verbose logging
python main.py meeting.mp4 --output ~/transcripts/ --verbose
```

---

## Recording Live Meetings with `transcribe.sh`

`transcribe.sh` is a shell script that **records from your microphone** (or a system audio capture device) and pipes the result straight into the pipeline.

```bash
# Record a new meeting
./transcribe.sh

# Or use an existing file (skips recording)
./transcribe.sh path/to/recording.ogg
```

The script activates the virtual environment, records (if no file is given), runs the full pipeline, then cleans up the temporary recording.

### Capturing Full Meeting Audio with BlackHole

By default, `transcribe.sh` only captures your microphone. To also capture the remote participants' audio (Zoom, Meet, Teams, …), use **BlackHole** — a free virtual audio driver for macOS.

#### 1. Install BlackHole

```bash
brew install blackhole-2ch
# or download the installer from existingmedia.com/products/blackhole
```

#### 2. Create a Multi-Output Device

This lets your speakers and BlackHole receive audio simultaneously, so you hear the call normally while BlackHole captures it.

1. Open **Audio MIDI Setup** (`/Applications/Utilities/Audio MIDI Setup.app`)
2. Click **+** → **Create Multi-Output Device**
3. Check both **BlackHole 2ch** and your normal speakers/headphones
4. Set **Master Device** to your speakers
5. Check **Drift Correction** on BlackHole

#### 3. Create an Aggregate Device

This combines your microphone and BlackHole into a single input, so `ffmpeg` records both at once.

1. In Audio MIDI Setup, click **+** → **Create Aggregate Device**
2. Check both your **microphone** (e.g. MacBook Pro Microphone) and **BlackHole 2ch**
3. Set **Clock Source** to your microphone

#### 4. Route System Audio

Before starting your meeting:

1. Go to **System Settings → Sound → Output** → select **Multi-Output Device**
2. Your meeting audio now plays through your speakers **and** feeds into BlackHole

#### 5. Record with the Aggregate Device

Find the device index of your Aggregate Device:

```bash
ffmpeg -f avfoundation -list_devices true -i ""
```

Look for your Aggregate Device in the output (e.g. `[AVFoundation input device @ ...] [2] Aggregate Device`). Then update `transcribe.sh`:

```sh
ffmpeg -f avfoundation -i ":2" -ar 16000 -ac 1 -c:a libopus -b:a 32k "$INPUT"
#                              ^ use your Aggregate Device index
```

Now `transcribe.sh` records everything: your voice **and** all remote participants, ready for diarization.

---

## Pricing by Meeting Duration

All costs are **per meeting**, billed only when using cloud APIs. Local (`mlx`, `whisper`) backends are always free.

### Transcription

| Backend | 30 min | 60 min | 90 min |
|---------|--------|--------|--------|
| `mlx` (Apple Silicon) | **Free** | **Free** | **Free** |
| `whisper` (CPU) | **Free** | **Free** | **Free** |
| `groq` — turbo ($0.04/hr) | ~$0.02 | ~$0.04 | ~$0.06 |
| `groq` — large-v3 ($0.111/hr) | ~$0.06 | ~$0.11 | ~$0.17 |

### Summarization

Costs depend on transcript length (~130 words/min average, plus ~1 500 token output).

| Backend | 30 min | 60 min | 90 min |
|---------|--------|--------|--------|
| `mlx` (local Llama 3.1 8B) | **Free** | **Free** | **Free** |
| `groq` (~$0.10/M tokens) | < $0.01 | ~$0.01 | ~$0.02 |
| `claude` Sonnet ($3/$15 per M in/out) | ~$0.03 | ~$0.05 | ~$0.08 |

### Typical Full-Pipeline Cost

| Combination | 30 min | 60 min | 90 min | Notes |
|-------------|--------|--------|--------|-------|
| MLX + MLX | **$0.00** | **$0.00** | **$0.00** | Fully local, Apple Silicon only |
| Groq turbo + MLX | ~$0.02 | ~$0.04 | ~$0.06 | Fast transcription, free notes |
| Groq turbo + Groq | ~$0.03 | ~$0.05 | ~$0.08 | All-cloud, no local GPU needed |
| Groq turbo + Claude | ~$0.05 | ~$0.09 | ~$0.14 | Best quality notes |
| Groq large-v3 + Claude | ~$0.09 | ~$0.16 | ~$0.25 | Maximum quality |

> Groq offers a generous **free tier** (audio + LLM). Most short meetings cost nothing until you exceed the free quota.

---

## How It Works

```
  audio/video file  (or live recording via transcribe.sh)
        │
        ▼
┌───────────────────┐
│  1. Extract audio │  ffmpeg → 16 kHz mono WAV  (+OGG for Groq)
└────────┬──────────┘
         │
         ├──────────────────────────┐  (parallel)
         ▼                          ▼
┌─────────────────┐      ┌──────────────────────┐
│  2. Transcribe  │      │  3. Diarize speakers  │
│  Whisper ASR    │      │  MFCC + clustering    │
│  → text segs    │      │  → speaker turns      │
└────────┬────────┘      └──────────┬───────────┘
         │                          │
         └──────────┬───────────────┘
                    ▼
         ┌──────────────────┐
         │  4. Merge        │  align text ↔ speaker by timestamp overlap
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │  5. Export       │  transcript.md + transcript.json
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐  (--summarize)
         │  6. Summarize    │  MLX / Claude / Groq → meeting_notes.md
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐  (--anytype)
         │  7. Publish      │  Anytype local HTTP API
         └──────────────────┘
```

Steps 2 and 3 run **in parallel** — MLX/Groq uses the GPU or network while diarization runs on CPU — cutting total runtime roughly in half.

---

## Technology Stack

| Layer | Tool | Rationale |
|-------|------|-----------|
| **ASR — Apple Silicon** | [mlx-whisper](https://github.com/ml-explore/mlx-examples) | Native Metal GPU, no CUDA required |
| **ASR — Intel/other** | [openai-whisper](https://github.com/openai/whisper) | CPU fallback, same model quality |
| **ASR — cloud** | [Groq Whisper API](https://console.groq.com/) | Fastest available cloud inference |
| **Diarization** | Custom MFCC + scikit-learn agglomerative clustering | No Hugging Face, no token, no telemetry |
| **Media extraction** | [ffmpeg](https://ffmpeg.org/) | Battle-tested, handles every format |
| **Summarization — local** | [mlx-lm](https://github.com/ml-explore/mlx-examples) / Llama 3.1 8B | Fully offline, Apple Silicon GPU |
| **Summarization — cloud** | Claude Sonnet / Groq Mistral | Best quality when privacy allows |
| **Publishing** | [Anytype](https://anytype.io/) local HTTP API | Local-first note management |

### Model Selection & Privacy/Performance Trade-offs

| Need | Recommended setup |
|------|-------------------|
| Maximum privacy (nothing leaves device) | `--transcription-backend mlx --backend mlx` |
| Best speed on Apple Silicon | `--transcription-backend mlx --model large-v3-turbo` |
| No GPU / Intel Mac | `--transcription-backend whisper` |
| Fastest possible (cloud OK) | `--transcription-backend groq --model large-v3-turbo` |
| Best note quality | `--backend claude` |
| No API keys at all | `--transcription-backend mlx --backend mlx` (both local) |
| Confidential meetings | Avoid `groq` and `claude` backends — audio/transcript is sent to their servers |

### Diarization Details

The speaker diarization is a custom implementation requiring no cloud services or Hugging Face authentication:

1. **VAD** — energy-based voice activity detection (threshold 0.3)
2. **Feature extraction** — 20 MFCC + Δ + ΔΔ = 60 features/frame (25 ms frames, 10 ms shift)
3. **Clustering** — agglomerative clustering with Ward linkage
4. **Speaker count** — elbow method on distortion curve (optimal for 2–5 speakers)
5. **Post-processing** — adjacent same-speaker segments merged

Transcript segments and diarization turns are aligned by timestamp overlap (≥ 100 ms) with a 500 ms proximity fallback for edge cases.

---

## Project Structure

```
Meeting-Scribe/
├── main.py                  # Pipeline orchestrator & CLI
├── transcribe.sh            # Record + transcribe in one command
├── processing/
│   ├── audio.py             # ffmpeg wrapper (WAV + OGG extraction)
│   ├── transcribe.py        # MLX Whisper / CPU Whisper / Groq
│   ├── diarize.py           # MFCC speaker diarization
│   └── merge.py             # Align transcript + speaker turns
├── utils/
│   ├── markdown.py          # Markdown / JSON export
│   ├── summarize.py         # Meeting notes (MLX / Claude / Groq)
│   └── anytype.py           # Anytype publisher
├── contexts/                # Domain context files for summarization
│   └── default.md
├── config/
│   └── requirements.txt
└── results/                 # Auto-created output folder
```

---

## License

MIT License

Copyright (c) 2025 MeetingScribe contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
