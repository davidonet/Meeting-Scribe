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
        "tiny": "mlx-community/whisper-tiny",
        "base": "mlx-community/whisper-base",
        "small": "mlx-community/whisper-small",
        "medium": "mlx-community/whisper-medium",
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
