# processing/transcribe.py
# ───────────────────────────────────────────────────────────────────
# Wraps MLX Whisper to convert WAV audio into timestamped text
# segments. Runs natively on Apple Silicon GPU via MLX.

import os
import json
import logging
import time
from typing import Dict, Any

import mlx_whisper

class WhisperTranscriber:
    """
    Transcribes speech from audio into text segments using MLX Whisper
    (optimized for Apple Silicon).
    """

    MODEL_MAP = {
        "tiny": "mlx-community/whisper-tiny-mlx",
        "base": "mlx-community/whisper-base-mlx",
        "small": "mlx-community/whisper-small-mlx",
        "medium": "mlx-community/whisper-medium-mlx",
        "large-v2": "mlx-community/whisper-large-v2-mlx",
        "large-v3": "mlx-community/whisper-large-v3-mlx",
        "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
    }

    def __init__(
        self,
        model_size: str = "base",
        device: str = None,  # ignored — MLX uses Metal automatically
        language: str = None,
        verbose: bool = False
    ):
        """
        Args:
          model_size – one of ["tiny","base","small","medium","large-v2","large-v3","large-v3-turbo"]
          device     – ignored (MLX always uses Apple Silicon GPU)
          language   – ISO-639-1 code to force transcription language, or None
          verbose    – True to log detailed progress
        """
        if model_size not in self.MODEL_MAP:
            logging.getLogger(__name__).warning(
                f"Invalid model size: {model_size}. Using 'base' instead."
            )
            model_size = "base"

        self.model_size = model_size
        self.model_repo = self.MODEL_MAP[model_size]
        self.language = language
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        if verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def transcribe(
        self,
        wav_path: str,
        output_json: bool = False
    ) -> Dict[str, Any]:
        """
        Run MLX Whisper on the given WAV file.

        Args:
          wav_path     – path to 16 kHz mono WAV
          output_json  – if True, save raw JSON to disk

        Returns:
          A dict with:
            {
              "text":    "full transcript",
              "segments":[
                  {"id": 0, "start":0.0, "end":2.1, "text":"Hello ..."},
                  ...
              ]
            }

        Raises:
          FileNotFoundError if wav_path missing
          RuntimeError on inference error
        """
        if not os.path.isfile(wav_path):
            raise FileNotFoundError(f"Input WAV file not found: {wav_path}")

        self.logger.info(f"Starting transcription of {wav_path}")
        self.logger.info(f"Using model: {self.model_repo}")

        transcribe_options = {}
        if self.language:
            transcribe_options["language"] = self.language

        if self.verbose:
            self.logger.debug(f"Transcription options: {transcribe_options}")

        start_time = time.time()

        try:
            result = mlx_whisper.transcribe(
                wav_path,
                path_or_hf_repo=self.model_repo,
                verbose=self.verbose,
                **transcribe_options
            )

            transcribe_time = time.time() - start_time
            self.logger.info(f"Transcription completed in {transcribe_time:.2f} seconds")

            if self.verbose:
                num_segments = len(result.get("segments", []))
                total_duration = result["segments"][-1]["end"] if num_segments > 0 else 0
                self.logger.debug(f"Generated {num_segments} segments, total duration: {total_duration:.2f}s")

            if output_json:
                json_path = os.path.splitext(wav_path)[0] + "_transcript.json"
                self._save_json(result, json_path)

            return result

        except Exception as e:
            self.logger.error(f"Transcription failed: {str(e)}")
            raise RuntimeError(f"MLX Whisper transcription failed: {str(e)}")

    def _save_json(self, result: Dict[str, Any], json_path: str) -> None:
        """Save transcription result to JSON file."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved transcript JSON to {json_path}")
        except Exception as e:
            self.logger.error(f"Failed to save JSON output: {str(e)}")


class GroqTranscriber:
    """
    Transcribes speech using the Groq Whisper API.
    Accepts OGG/Opus audio for minimal upload size and fast cloud inference.
    """

    # Maps local model names → Groq model IDs
    GROQ_MODEL_MAP = {
        "tiny":           "whisper-large-v3-turbo",
        "base":           "whisper-large-v3-turbo",
        "small":          "whisper-large-v3-turbo",
        "medium":         "whisper-large-v3",
        "large-v2":       "whisper-large-v3",
        "large-v3":       "whisper-large-v3",
        "large-v3-turbo": "whisper-large-v3-turbo",
    }

    # Groq free-tier upload limit
    FREE_TIER_LIMIT_MB = 25

    def __init__(
        self,
        model_size: str = "large-v3-turbo",
        language: str = None,
        api_key: str = None,
    ):
        """
        Args:
          model_size – maps to a Groq Whisper model (see GROQ_MODEL_MAP)
          language   – ISO-639-1 code, or None for auto-detect
          api_key    – Groq API key; falls back to GROQ_API_KEY env var
        """
        import os

        try:
            from groq import Groq
        except ImportError:
            raise ImportError(
                "groq package is required for Groq transcription. "
                "Install it with: pip install groq"
            )

        self.model_name = self.GROQ_MODEL_MAP.get(model_size, "whisper-large-v3-turbo")
        self.language = language
        self.logger = logging.getLogger(__name__)

        resolved_key = api_key or os.environ.get("GROQ_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Groq API key not found. Set the GROQ_API_KEY environment variable or pass api_key."
            )
        self._client = Groq(api_key=resolved_key)

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Send audio to Groq Whisper and return timestamped segments.

        Args:
          audio_path – path to OGG/Opus (or any Groq-supported format)

        Returns:
          Same dict format as WhisperTranscriber:
            {"text": "...", "segments": [{"id", "start", "end", "text"}, ...]}

        Raises:
          FileNotFoundError if audio_path missing
          RuntimeError on API error
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        if size_mb > self.FREE_TIER_LIMIT_MB:
            self.logger.warning(
                f"Audio file is {size_mb:.1f} MB — exceeds {self.FREE_TIER_LIMIT_MB} MB "
                "free-tier limit. Upload may fail; consider chunking."
            )

        self.logger.info(f"Transcribing with Groq ({self.model_name}): {audio_path} ({size_mb:.1f} MB)")

        start_time = time.time()
        try:
            with open(audio_path, "rb") as f:
                kwargs = dict(
                    file=(os.path.basename(audio_path), f, "audio/ogg"),
                    model=self.model_name,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )
                if self.language:
                    kwargs["language"] = self.language

                response = self._client.audio.transcriptions.create(**kwargs)

            elapsed = time.time() - start_time
            self.logger.info(f"Groq transcription completed in {elapsed:.2f}s")

            raw_segments = response.segments or []
            # Groq may return dicts or objects depending on the SDK version
            def _get(seg, key):
                return seg[key] if isinstance(seg, dict) else getattr(seg, key)

            segments = [
                {
                    "id": i,
                    "start": _get(seg, "start"),
                    "end": _get(seg, "end"),
                    "text": _get(seg, "text").strip(),
                }
                for i, seg in enumerate(raw_segments)
            ]

            return {"text": response.text, "segments": segments}

        except Exception as e:
            self.logger.error(f"Groq transcription failed: {str(e)}")
            raise RuntimeError(f"Groq transcription failed: {str(e)}")


