# MeetingScribe

> **One-line pitch**: *Drop a meeting video in your terminal and get back a clean, speaker-labelled transcript plus Markdown notes — all with free, open-source models you can run locally in under an hour.*

---

## Features (v0.1)

| Feature | Status | Notes |
|---------|--------|-------|
| High-quality multilingual transcription (OpenAI Whisper) | ✅ | Runs on CPU or GPU |
| Automatic speaker diarization (custom MFCC+clustering) | ✅ | Distinguishes *who* spoke |
| Markdown export with timestamps | ✅ | Saves to `results/transcript.md` |
| One-command CLI (`python main.py <video>`) | ✅ | Creates a `results/` folder |
| Meeting notes generation via Claude | ✅ | `--summarize` flag, requires `ANTHROPIC_API_KEY` |
| Publish notes to Anytype | ✅ | `--anytype` flag, requires `ANYTYPE_KEY` |
| Key-frame extraction for slide changes (LMSKE) | ⏳ | Planned v0.2 |

---

## Quick Start (~15 min)

> **Prereqs**: Python 3.10+, `ffmpeg` (≥ 4.2).

```bash
# 1. Clone & enter
git clone https://github.com/JuanLara18/Meeting-Scribe.git
cd Meeting-Scribe

# 2. Create env & install deps
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r config/requirements.txt

# 3. Run on a sample video
python main.py path/to/meeting.mp4
```

Output:

```
results/
├── transcript.md        # speaker-segmented Markdown
├── transcript.json      # raw structured data
└── audio.wav            # extracted audio (for debugging)
```

When `--summarize` is used, an additional file is created:

```
results/
└── meeting_notes.md     # AI-generated meeting notes
```

---

## Usage

```bash
python main.py [-h] [--output OUTPUT] [--lang LANG] [--model MODEL] [--verbose] [--summarize] [--anytype] VIDEO_PATH
```

| Argument | Default | Description |
|----------|---------|-------------|
| `VIDEO_PATH` | *(required)* | Path to input video (`.mp4`, `.mkv`, `.mov`) |
| `--output`, `-o` | `results/` | Output folder for transcript files |
| `--lang` | auto-detect | ISO-639-1 language code (e.g. `en`, `es`) |
| `--model` | `base` | Whisper model size (see table below) |
| `--verbose`, `-v` | off | Enable debug logging |
| `--summarize` | off | Generate meeting notes via Claude (requires `ANTHROPIC_API_KEY`) |
| `--anytype` | off | Publish notes to Anytype (requires `ANYTYPE_KEY`) |

### Whisper Models

| Model | Parameters | Speed | Accuracy |
|-------|-----------|-------|----------|
| `tiny` | 39M | Fastest | Low |
| `base` | 74M | Fast | Good (default) |
| `small` | 244M | Medium | Better |
| `medium` | 769M | Slow | High |
| `large-v2` | 1550M | Slowest | Highest |
| `large-v3` | 1550M | Slowest | Highest |
| `large-v3-turbo` | 809M | Fast | High |

### Examples

```bash
# Spanish audio, medium model
python main.py reunión.mp4 --lang es --model medium

# Generate meeting notes with Claude
python main.py meeting.mp4 --summarize

# Full pipeline: transcribe + summarize + publish to Anytype
python main.py meeting.mp4 --summarize --anytype

# Custom output folder with verbose logging
python main.py meeting.mp4 --output ~/transcripts/ --verbose
```

---

## Project Structure

```
Meeting-Scribe/
├── main.py              # orchestrates the end-to-end pipeline
├── processing/
│   ├── audio.py         # audio extraction (ffmpeg)
│   ├── transcribe.py    # Whisper wrapper
│   ├── diarize.py       # custom speaker diarization
│   └── merge.py         # align speakers + text
├── utils/
│   ├── markdown.py      # export helpers
│   ├── summarize.py     # Claude meeting notes generator
│   └── anytype.py       # Anytype publisher
├── config/
│   └── requirements.txt
├── scripts/
│   ├── setup.py
│   ├── whisper_install.py
│   └── test_components.py
└── results/             # auto-created
```

---

## Technology Stack

| Layer | Tool | Why |
|-------|------|-----|
| **ASR** | [OpenAI Whisper](https://github.com/openai/whisper) | State-of-the-art, MIT license, offline |
| **Diarization** | Custom MFCC + agglomerative clustering | No cloud/HuggingFace dependencies |
| **Media** | [`ffmpeg`](https://ffmpeg.org/) | Battle-tested extraction |
| **Summarization** | Claude (claude-sonnet-4-6) | High-quality meeting notes |
| **Publishing** | [Anytype](https://anytype.io/) | Local-first note management |

---

## How it Works (Flow Diagram)

```
           video.mp4
                │
      ┌─────────▼─────────┐
      │ 1. ffmpeg extract │──► audio.wav
      └─────────┬─────────┘
                │
  ┌─────────────▼─────────────┐
  │ 2. Whisper ASR → segments │
  └─────────────┬─────────────┘
                │
  ┌─────────────▼─────────────┐
  │ 3. MFCC+cluster diarize   │
  └─────────────┬─────────────┘
                │
  ┌─────────────▼─────────────┐
  │   4. Merge text+speakers  │
  └─────────────┬─────────────┘
                │
  ┌─────────────▼─────────────┐
  │ 5. Export Markdown & JSON │
  └─────────────┬─────────────┘
                │
  ┌─────────────▼─────────────┐  (optional --summarize)
  │ 6. Claude meeting notes   │
  └─────────────┬─────────────┘
                │
  ┌─────────────▼─────────────┐  (optional --anytype)
  │ 7. Publish to Anytype     │
  └───────────────────────────┘
```

---

## Roadmap

1. **v0.2** – Key-frame extraction → embed screenshots in Markdown.
2. **v0.3** – Local LLM summariser → bullet goals, action items.
3. **v1.0** – Real-time streaming mode & simple web UI (FastAPI + React).

---

## License

MIT — free for personal & commercial projects. Attribution welcome but not required.
