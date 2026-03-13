# utils/summarize.py
# ───────────────────────────────────────────────────────────────────
# Generates meeting notes from a transcript using Claude (Anthropic API).

import os
import logging
from pathlib import Path
from typing import Optional

try:
    import anthropic
except ImportError:
    anthropic = None


class MeetingSummarizer:
    """
    Calls Claude to produce structured meeting notes from a raw transcript.
    """

    DEFAULT_MODEL = "claude-sonnet-4-6"

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

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        """
        Args:
          api_key – Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
          model   – Claude model identifier
        """
        if anthropic is None:
            raise ImportError(
                "The 'anthropic' package is required for summarization. "
                "Install it with: pip install anthropic"
            )

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY or pass api_key."
            )

        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)

        context_path = Path(__file__).parent / "context.md"
        self._context = context_path.read_text(encoding="utf-8") if context_path.exists() else ""

    def summarize(self, transcript_md: str) -> str:
        """
        Generate meeting notes from a Markdown transcript.

        Args:
          transcript_md – the full transcript text (Markdown)

        Returns:
          Meeting notes as Markdown string.
        """
        self.logger.info(f"Calling Claude ({self.model}) to generate meeting notes")

        system_prompt = (self._context + "\n\n" + self.SYSTEM_PROMPT).strip() if self._context else self.SYSTEM_PROMPT

        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": transcript_md}],
        )

        notes = message.content[0].text
        self.logger.info("Meeting notes generated successfully")
        return notes
