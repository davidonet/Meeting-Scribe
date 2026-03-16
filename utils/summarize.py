# utils/summarize.py
# ───────────────────────────────────────────────────────────────────
# Generates meeting notes from a transcript using either:
#   - A local model via mlx-lm (default, no API key needed)
#   - Claude via the Anthropic API (--backend claude)

import logging
from pathlib import Path
from typing import Optional


class MeetingSummarizer:
    """
    Produces structured meeting notes from a raw transcript.

    Supports two backends:
      - "mlx"    : local inference via mlx-lm (Apple Silicon, default)
      - "claude" : Anthropic API (requires ANTHROPIC_API_KEY)
    """

    DEFAULT_MLX_MODEL = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
    DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-6"

    SYSTEM_PROMPT = (
        "You are a professional meeting-notes assistant.\n"
        "Given a raw speaker-labelled transcript, produce concise meeting notes "
        "in Markdown with the following sections:\n"
        "1. **Participants** – list of speakers identified\n"
        "2. **Summary** – 3-5 sentence overview\n"
        "3. **Key Discussion Points** – bullet list\n"
        "4. **Decisions Made** – bullet list (if any)\n"
        "5. **Action Items** – bullet list with owner when identifiable\n\n"
        "Be factual. Do not invent information absent from the transcript. "
        "Write in the same language as the transcript."
    )

    LANGUAGE_INSTRUCTION = "Always write the meeting notes in {language}, regardless of the transcript language."

    def __init__(
        self,
        backend: str = "mlx",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_tokens: int = 4096,
        language: Optional[str] = "French",
    ):
        """
        Args:
          backend    – "mlx" for local inference, "claude" for Anthropic API
          model      – model identifier (defaults per backend if None)
          api_key    – Anthropic API key (only needed for "claude" backend)
          max_tokens – maximum tokens to generate
          language   – force output language (e.g. "French"); None to auto-detect from transcript
        """
        self.backend = backend
        self.max_tokens = max_tokens
        self.language = language
        self.logger = logging.getLogger(__name__)

        # Load context.md (domain knowledge for the system prompt)
        context_path = Path(__file__).parent / "context.md"
        self._context = context_path.read_text(encoding="utf-8") if context_path.exists() else ""

        if backend == "mlx":
            self._init_mlx(model)
        elif backend == "claude":
            self._init_claude(model, api_key)
        else:
            raise ValueError(f"Unknown backend: {backend!r}. Use 'mlx' or 'claude'.")

    # ── Backend initialisation ────────────────────────────────────

    def _init_mlx(self, model: Optional[str]) -> None:
        try:
            from mlx_lm import load, generate
        except ImportError:
            raise ImportError(
                "mlx-lm is required for local summarization. "
                "Install it with: pip install mlx-lm"
            )

        self.model_name = model or self.DEFAULT_MLX_MODEL
        self.logger.info(f"Loading local model: {self.model_name}")
        self._mlx_model, self._mlx_tokenizer = load(self.model_name)
        self._mlx_generate = generate
        self.logger.info("Local model loaded successfully")

    def _init_claude(self, model: Optional[str], api_key: Optional[str]) -> None:
        import os

        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is required for the Claude backend. "
                "Install it with: pip install anthropic"
            )

        self.model_name = model or self.DEFAULT_CLAUDE_MODEL
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY or pass api_key."
            )
        self._claude_client = anthropic.Anthropic(api_key=resolved_key)

    # ── Public API ────────────────────────────────────────────────

    def summarize(self, transcript_md: str) -> str:
        """
        Generate meeting notes from a Markdown transcript.

        Args:
          transcript_md – the full transcript text (Markdown)

        Returns:
          Meeting notes as Markdown string.
        """
        base = (self._context + "\n\n" + self.SYSTEM_PROMPT).strip() if self._context else self.SYSTEM_PROMPT
        if self.language:
            base = base + "\n" + self.LANGUAGE_INSTRUCTION.format(language=self.language)
        system_prompt = base

        if self.backend == "mlx":
            return self._summarize_mlx(system_prompt, transcript_md)
        else:
            return self._summarize_claude(system_prompt, transcript_md)

    # ── Private: MLX backend ──────────────────────────────────────

    def _summarize_mlx(self, system_prompt: str, transcript_md: str) -> str:
        self.logger.info(f"Generating notes with local model ({self.model_name})")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript_md},
        ]

        prompt = self._mlx_tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        notes = self._mlx_generate(
            self._mlx_model,
            self._mlx_tokenizer,
            prompt=prompt,
            max_tokens=self.max_tokens,
            verbose=False,
        )

        self.logger.info("Meeting notes generated successfully (local)")
        return notes

    # ── Private: Claude backend ───────────────────────────────────

    def _summarize_claude(self, system_prompt: str, transcript_md: str) -> str:
        self.logger.info(f"Calling Claude ({self.model_name}) to generate meeting notes")

        message = self._claude_client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": transcript_md}],
        )

        notes = message.content[0].text
        self.logger.info("Meeting notes generated successfully (Claude)")
        return notes
