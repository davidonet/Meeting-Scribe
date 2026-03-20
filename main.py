# main.py
# ───────────────────────────────────────────────────────────────────
# Orchestrates the full pipeline: extract audio, transcribe speech,
# diarize speakers, merge segments, and export results to JSON/Markdown.

import os
import sys
import argparse
import logging

from dotenv import load_dotenv
load_dotenv()
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple

from processing.audio import AudioExtractor
from processing.transcribe import WhisperTranscriber, WhisperCPUTranscriber, GroqTranscriber
from processing.diarize import SpeakerDiarizer
from processing.merge import SegmentMerger
from utils.markdown import MarkdownExporter
from utils.summarize import MeetingSummarizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

class MeetingScribe:
    """
    Orchestrates the end-to-end pipeline:
      1) Extract audio from video
      2) Transcribe audio
      3) Diarize speakers
      4) Merge segments
      5) Export Markdown & JSON
      6) Summarize with Claude (optional)
    """

    def __init__(
        self,
        video_path: str,
        output_folder: str = "results/",
        language: str = None,
        whisper_model: str = "base",
        transcription_backend: str = "mlx",
        summarize: bool = False,
        summarize_only: bool = False,
        summarize_backend: str = "mlx",
        context_file: Optional[str] = None,
    ):
        """
        Args:
          video_path    – path to input video file (.mp4/.mkv/.mov)
          output_folder – where transcript.json and .md will be created
          language      – ISO-639-1 code to force ASR language (None=auto)
          whisper_model          – one of ["tiny","base","small","medium","large-v3","large-v3-turbo"]
          transcription_backend  – "mlx" for local MLX Whisper, "groq" for Groq API
          summarize              – generate meeting notes
          summarize_backend      – "mlx" for local model, "claude" for Anthropic API
          context_file           – path to a context .md file for summarization (default: contexts/default.md)
        """
        self.video_path = video_path
        self.output_folder = output_folder
        self.language = language
        self.whisper_model = whisper_model
        self.transcription_backend = transcription_backend
        self.summarize = summarize or summarize_only
        self.summarize_only = summarize_only
        self.summarize_backend = summarize_backend
        self.context_file = context_file
        self.logger = logging.getLogger(__name__)
        
        # Ensure output folder ends with a slash for path consistency
        if not self.output_folder.endswith("/") and not self.output_folder.endswith("\\"):
            self.output_folder += "/"
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Set paths for outputs
        self.audio_path = os.path.join(self.output_folder, "audio.wav")
        self.ogg_path = os.path.join(self.output_folder, "audio.ogg")
        self.transcript_json = os.path.join(self.output_folder, "transcript.json")
        self.transcript_md = os.path.join(self.output_folder, "transcript.md")
        self.summary_md = os.path.join(self.output_folder, "meeting_notes.md")
        
        # Validate inputs
        if self.summarize_only:
            if not os.path.isfile(self.transcript_md):
                raise FileNotFoundError(f"Transcript not found: {self.transcript_md}. Run full pipeline first.")
        else:
            if not os.path.isfile(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            valid_models = ["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo"]
            if whisper_model not in valid_models:
                raise ValueError(f"Invalid model: {whisper_model}. Must be one of {valid_models}")

    def run(self) -> None:
        """
        Execute full pipeline.
        Steps 2 (transcription) and 3 (diarization) run in parallel —
        transcription uses GPU/Groq API while diarization uses CPU,
        so they don't contend for the same resource.
        Raises exception on any step failure.
        """
        self.logger.info(f"Starting MeetingScribe pipeline for {self.video_path}")
        self.logger.info(f"Output folder: {self.output_folder}")

        try:
            notes = None

            if self.summarize_only:
                # Skip steps 1-5, jump straight to summarization
                self.logger.info(f"Summarize-only mode: using existing {self.transcript_md}")
                notes = self._summarize()
            else:
                # Step 1: Extract audio from video
                wav_path = self._extract_audio()

                # Steps 2 & 3: Transcribe and diarize in parallel
                self.logger.info("Steps 2 & 3: Transcribing and diarizing in parallel")
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future_transcript = executor.submit(self._transcribe, wav_path)
                    future_diarization = executor.submit(self._diarize, wav_path)
                    transcript = future_transcript.result()
                    diarization = future_diarization.result()

                # Step 4: Merge transcript and speaker info
                merged = self._merge(transcript, diarization)

                # Step 5: Export results to Markdown and JSON
                self._export(merged)

                # Step 6: Summarize with Claude (optional)
                if self.summarize:
                    notes = self._summarize()

            self.logger.info("✓ Pipeline completed successfully")
            self.logger.info(f"📄 Results saved to {self.transcript_md} and {self.transcript_json}")
            if notes:
                self.logger.info(f"📝 Meeting notes saved to {self.summary_md}")
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            raise

    def _extract_audio(self) -> str:
        """
        Extracts audio from the video.
        - Always produces a WAV file (needed for diarization).
        - Also produces an OGG/Opus file when using the Groq transcription backend.

        Returns:
          path to extracted .wav file (16 kHz, mono)
        """
        self.logger.info("Step 1: Extracting audio from video")

        try:
            extractor = AudioExtractor()
            wav_path = extractor.extract(
                video_path=self.video_path,
                target_wav=self.audio_path,
                sample_rate=16000,
                mono=True,
            )
            self.logger.info(f"WAV audio extracted to {wav_path}")

            if self.transcription_backend == "groq":
                if os.path.splitext(self.video_path)[1].lower() == ".ogg":
                    self.logger.info("Input is already OGG — skipping conversion")
                    self.ogg_path = self.video_path
                else:
                    extractor.extract_ogg(
                        video_path=self.video_path,
                        target_ogg=self.ogg_path,
                        sample_rate=16000,
                    )

            return wav_path
        except Exception as e:
            self.logger.error(f"Audio extraction failed: {str(e)}")
            raise RuntimeError(f"Audio extraction failed: {str(e)}")

    def _transcribe(self, wav_path: str) -> Dict[str, Any]:
        """
        Args:
          wav_path – path to .wav file from _extract_audio() (used for MLX)
        Returns:
          Whisper transcript dict with segments & timestamps
        """
        self.logger.info("Step 2: Transcribing audio with Whisper")
        self.logger.info(
            f"Backend: {self.transcription_backend}, model: {self.whisper_model}, "
            f"language: {self.language or 'auto-detect'}"
        )

        try:
            if self.transcription_backend == "groq":
                transcriber = GroqTranscriber(
                    model_size=self.whisper_model,
                    language=self.language,
                )
                transcript = transcriber.transcribe(self.ogg_path)
            elif self.transcription_backend == "whisper":
                transcriber = WhisperCPUTranscriber(
                    model_size=self.whisper_model,
                    language=self.language,
                    verbose=True,
                )
                transcript = transcriber.transcribe(wav_path)
            else:
                transcriber = WhisperTranscriber(
                    model_size=self.whisper_model,
                    language=self.language,
                    verbose=True,
                )
                transcript = transcriber.transcribe(wav_path)

            segment_count = len(transcript.get("segments", []))
            self.logger.info(f"Transcription complete with {segment_count} segments")

            if segment_count > 0:
                total_duration = transcript["segments"][-1]["end"]
                total_words = len(transcript["text"].split())
                self.logger.info(f"Total duration: {total_duration:.2f}s, Word count: {total_words}")

            return transcript
        except Exception as e:
            self.logger.error(f"Transcription failed: {str(e)}")
            raise RuntimeError(f"Transcription failed: {str(e)}")

    def _diarize(self, wav_path: str) -> List[Dict[str, Any]]:
        """
        Args:
          wav_path – same .wav file
        Returns:
          list of diarization segments, each with:
            - speaker: str
            - start: float (secs)
            - end: float   (secs)
        """
        self.logger.info("Step 3: Diarizing speakers")
        
        try:
            diarizer = SpeakerDiarizer(device="cpu")  # 'cuda' could be used for GPU
            diarization = diarizer.diarize(wav_path)
            
            # Get some basic stats about the diarization
            speaker_count = len(set(s["speaker"] for s in diarization))
            segment_count = len(diarization)
            
            self.logger.info(f"Diarization complete with {speaker_count} speakers, {segment_count} segments")
            
            return diarization
        except Exception as e:
            self.logger.error(f"Diarization failed: {str(e)}")
            raise RuntimeError(f"Diarization failed: {str(e)}")

    def _merge(self, transcript: Dict[str, Any], diarization: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Align transcript segments with speaker turns.
        Args:
          transcript   – output of _transcribe()
          diarization  – output of _diarize()
        Returns:
          list of merged segments:
            [{
              "speaker": "...",
              "start": 12.34,
              "end":   15.67,
              "text":  "…"
            }, …]
        """
        self.logger.info("Step 4: Merging transcript with speaker diarization")
        
        try:
            merger = SegmentMerger(
                max_gap=0.5,     # Half-second tolerance for non-overlapping segments
                min_overlap=0.1  # 100ms minimum overlap to associate speech with speaker
            )
            
            merged = merger.merge(
                transcript_segments=transcript["segments"],
                diarization_segments=diarization
            )
            
            # Get some insights about the merged data
            speaker_stats = {}
            for seg in merged:
                speaker = seg.get("speaker", "UNKNOWN")
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {"count": 0, "duration": 0.0}
                speaker_stats[speaker]["count"] += 1
                speaker_stats[speaker]["duration"] += (seg["end"] - seg["start"])
            
            self.logger.info(f"Merge complete with {len(merged)} segments")
            for speaker, stats in speaker_stats.items():
                self.logger.info(f"  {speaker}: {stats['count']} segments, {stats['duration']:.1f}s")
            
            return merged
        except Exception as e:
            self.logger.error(f"Merge failed: {str(e)}")
            raise RuntimeError(f"Merge failed: {str(e)}")

    def _export(self, merged: List[Dict[str, Any]]) -> None:
        """
        Writes:
          - results/transcript.json (raw merged list)
          - results/transcript.md   (Markdown with headers per minute)
        """
        self.logger.info("Step 5: Exporting results to Markdown and JSON")
        
        try:
            exporter = MarkdownExporter(
                output_md=self.transcript_md,
                output_json=self.transcript_json
            )
            
            # Export JSON first (raw data)
            exporter.export_json(merged)
            
            # Export Markdown (formatted for humans)
            exporter.export_markdown(merged, block_minutes=1)
            
            self.logger.info(f"Export complete: {self.transcript_json} and {self.transcript_md}")
        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}")
            raise RuntimeError(f"Export failed: {str(e)}")

    def _summarize(self) -> str:
        """
        Read the exported Markdown transcript and generate meeting notes.

        For the MLX backend, runs in a fresh subprocess so that Whisper's
        Metal GPU memory is fully released before the larger summarization
        model is loaded.

        Returns:
          The generated meeting notes as a Markdown string.
        """
        self.logger.info(f"Step 6: Generating meeting notes ({self.summarize_backend})")

        try:
            if self.summarize_backend == "mlx":
                return self._summarize_mlx_subprocess()

            with open(self.transcript_md, "r", encoding="utf-8") as f:
                transcript_text = f.read()

            summarizer = MeetingSummarizer(backend=self.summarize_backend, context_file=self.context_file)
            notes = summarizer.summarize(transcript_text)

            with open(self.summary_md, "w", encoding="utf-8") as f:
                f.write(notes)

            self.logger.info(f"Meeting notes saved to {self.summary_md}")
            return notes
        except Exception as e:
            self.logger.error(f"Summarization failed: {str(e)}")
            raise RuntimeError(f"Summarization failed: {str(e)}")

    def _summarize_mlx_subprocess(self) -> str:
        """
        Spawn a fresh Python process for MLX summarization.

        Whisper's model weights remain referenced in mlx_whisper's internal
        lru_cache for the lifetime of the process — mx.clear_cache() cannot
        reclaim that memory. A subprocess starts with a clean Metal heap, so
        the Llama model can load without competing with Whisper.
        """
        import subprocess

        project_root = os.path.dirname(os.path.abspath(__file__))
        context_arg = f", context_file={repr(self.context_file)}" if self.context_file else ""
        script = (
            f"import sys; sys.path.insert(0, {repr(project_root)})\n"
            f"from utils.summarize import MeetingSummarizer\n"
            f"with open({repr(self.transcript_md)}, encoding='utf-8') as f:\n"
            f"    text = f.read()\n"
            f"s = MeetingSummarizer(backend='mlx'{context_arg})\n"
            f"notes = s.summarize(text)\n"
            f"with open({repr(self.summary_md)}, 'w', encoding='utf-8') as f:\n"
            f"    f.write(notes)\n"
        )

        self.logger.info("Launching subprocess for MLX summarization (releases Whisper GPU memory)")
        result = subprocess.run([sys.executable, "-c", script])

        if result.returncode != 0:
            raise RuntimeError(f"MLX summarization subprocess failed (exit code {result.returncode})")

        self.logger.info(f"Meeting notes saved to {self.summary_md}")
        with open(self.summary_md, "r", encoding="utf-8") as f:
            return f.read()

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MeetingScribe: Convert meeting videos to speaker-labelled transcripts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "video_path",
        nargs="?",
        default=None,
        help="Path to input video file (.mp4, .mkv, .mov). Not required with --summarize-only."
    )
    
    parser.add_argument(
        "--output", "-o",
        default="results/",
        help="Output folder for transcript files"
    )
    
    parser.add_argument(
        "--lang",
        default=None,
        help="ISO-639-1 language code (None=auto-detect)"
    )
    
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo"],
        help="Whisper model size"
    )
    
    import platform
    default_transcription = "mlx" if platform.machine() == "arm64" else "whisper"

    parser.add_argument(
        "--transcription-backend",
        default=default_transcription,
        choices=["mlx", "whisper", "groq"],
        dest="transcription_backend",
        help="Transcription backend: 'mlx' for Apple Silicon (default on arm64), 'whisper' for OpenAI Whisper CPU (default on Intel), 'groq' for Groq API"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Generate meeting notes from the transcript"
    )

    parser.add_argument(
        "--summarize-only",
        action="store_true",
        dest="summarize_only",
        help="Skip transcription, only regenerate meeting notes from existing transcript.md"
    )

    parser.add_argument(
        "--backend",
        default="mlx",
        choices=["mlx", "claude", "groq"],
        help="Summarization backend: 'mlx' for local model (default), 'claude' for Anthropic API, 'groq' for Groq API (Mistral)"
    )

    parser.add_argument(
        "--context",
        default=None,
        help="Path to a context .md file for summarization (default: contexts/default.md)"
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.summarize_only and not args.video_path:
        print("Error: video_path is required unless --summarize-only is used.")
        return 1

    try:
        scribe = MeetingScribe(
            video_path=args.video_path,
            output_folder=args.output,
            language=args.lang,
            whisper_model=args.model,
            transcription_backend=args.transcription_backend,
            summarize=args.summarize,
            summarize_only=args.summarize_only,
            summarize_backend=args.backend,
            context_file=args.context,
        )
        
        scribe.run()
        return 0  # Success exit code
    except FileNotFoundError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 2  # File not found exit code
    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 3  # Invalid input exit code
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1  # General error exit code


if __name__ == "__main__":
    sys.exit(main())