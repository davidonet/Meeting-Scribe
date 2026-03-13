# utils/anytype.py
# ───────────────────────────────────────────────────────────────────
# Publishes meeting notes to Anytype via its local HTTP API.

import os
import logging
from typing import Optional

try:
    import requests
except ImportError:
    requests = None


ANYTYPE_DEFAULT_URL = "http://localhost:31009/v1"
ANYTYPE_API_VERSION = "2025-11-08"


class AnytypePublisher:
    """
    Creates a page object in Anytype containing the meeting notes.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = ANYTYPE_DEFAULT_URL,
        space_id: Optional[str] = None,
    ):
        """
        Args:
          api_key  – Anytype API key (falls back to ANYTYPE_KEY env var)
          base_url – Anytype local API URL
          space_id – target space (falls back to ANYTYPE_SPACE env var,
                     then auto-detects the first available space)
        """
        if requests is None:
            raise ImportError(
                "The 'requests' package is required for Anytype integration. "
                "Install it with: pip install requests"
            )

        self.api_key = api_key or os.environ.get("ANYTYPE_KEY")
        if not self.api_key:
            raise ValueError(
                "Anytype API key not found. Set ANYTYPE_KEY or pass api_key."
            )

        self.base_url = base_url.rstrip("/")
        self.space_id = space_id or os.environ.get("ANYTYPE_SPACE")
        self.logger = logging.getLogger(__name__)

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Anytype-Version": ANYTYPE_API_VERSION,
        }

    def _resolve_space(self) -> str:
        """Return the target space ID, auto-detecting if needed."""
        if self.space_id:
            return self.space_id

        self.logger.info("No space ID configured — detecting first available space")
        resp = requests.get(f"{self.base_url}/spaces", headers=self._headers())
        resp.raise_for_status()

        data = resp.json()
        spaces = data.get("data", data)
        if not isinstance(spaces, list) or len(spaces) == 0:
            raise RuntimeError("No Anytype spaces found.")

        space_id = spaces[0].get("id") or spaces[0].get("spaceId")
        self.logger.info(f"Using Anytype space: {space_id}")
        return space_id

    def publish(self, title: str, body_md: str) -> str:
        """
        Create a page object in Anytype.

        Args:
          title   – page title (e.g. "Meeting Notes — 2026-03-13")
          body_md – Markdown content for the page body

        Returns:
          The ID of the created Anytype object.
        """
        space_id = self._resolve_space()

        payload = {
            "name": title,
            "icon": {"emoji": "\U0001f4dd", "format": "emoji"},
            "body": body_md,
            "type_key": "page",
        }

        url = f"{self.base_url}/spaces/{space_id}/objects"
        self.logger.info(f"Creating Anytype page: {title}")

        resp = requests.post(url, headers=self._headers(), json=payload)
        resp.raise_for_status()

        result = resp.json()
        object_id = (result.get("object") or result).get("id", "?")
        self.logger.info(
            f"Notes saved to Anytype (space: {space_id}, object: {object_id})"
        )
        return object_id
