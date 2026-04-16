"""
vision/interface.py — Abstract interface for vision / OCR tools.

Concrete implementations (Claude Vision, Tesseract, GPT-4V, etc.) must
subclass VisionInterface and implement `describe` and `ocr`.

The NullVisionInterface is the default no-op implementation used when no
vision backend is configured — it returns empty results instead of raising.
"""

from __future__ import annotations

import base64
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class VisionResult:
    """Unified result from any vision operation."""
    text:        str              = ""          # Free-text description or OCR output
    labels:      list[str]        = field(default_factory=list)   # Detected object / concept labels
    confidence:  float            = 0.0
    raw:         dict[str, Any]   = field(default_factory=dict)   # Provider-specific payload
    error:       str | None       = None


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class VisionInterface(ABC):
    """
    Abstract base for all vision backends.

    Implement both `describe` (semantic scene description) and `ocr`
    (raw text extraction) in your concrete subclass.  They may call
    the same underlying API — that is fine.
    """

    @abstractmethod
    def describe(self, image_path: str) -> VisionResult:
        """
        Return a semantic description of the image at `image_path`.

        Parameters
        ----------
        image_path : Absolute or relative path to the image file.

        Returns
        -------
        VisionResult with at minimum `text` populated.
        """

    @abstractmethod
    def ocr(self, image_path: str) -> VisionResult:
        """
        Extract raw text from the image (OCR).

        Parameters
        ----------
        image_path : Absolute or relative path to the image file.

        Returns
        -------
        VisionResult with `text` containing the extracted characters.
        """

    # ------------------------------------------------------------------
    # Shared utility helpers available to all subclasses
    # ------------------------------------------------------------------

    @staticmethod
    def load_image_b64(image_path: str) -> str:
        """Read an image file and return its base-64 encoded string."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        with open(path, "rb") as fh:
            return base64.b64encode(fh.read()).decode("utf-8")

    @staticmethod
    def infer_media_type(image_path: str) -> str:
        """Return MIME type based on file extension."""
        ext = Path(image_path).suffix.lower()
        return {
            ".jpg":  "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png":  "image/png",
            ".gif":  "image/gif",
            ".webp": "image/webp",
        }.get(ext, "image/jpeg")


# ---------------------------------------------------------------------------
# Null (no-op) implementation
# ---------------------------------------------------------------------------

class NullVisionInterface(VisionInterface):
    """
    No-op vision backend.

    Used when no real vision provider is configured.
    All calls return an empty VisionResult without raising.
    """

    def describe(self, image_path: str) -> VisionResult:
        logger.debug("NullVisionInterface.describe — skipped: %s", image_path)
        return VisionResult(text="", error="No vision backend configured.")

    def ocr(self, image_path: str) -> VisionResult:
        logger.debug("NullVisionInterface.ocr — skipped: %s", image_path)
        return VisionResult(text="", error="No vision backend configured.")


# ---------------------------------------------------------------------------
# Example: Claude Vision implementation stub
# ---------------------------------------------------------------------------

class ClaudeVisionInterface(VisionInterface):
    """
    Vision backend backed by the Anthropic Claude API (claude-sonnet-4-6).

    Set the ANTHROPIC_API_KEY environment variable before use.

    Example
    -------
    >>> from director.tools.vision.interface import ClaudeVisionInterface
    >>> vision = ClaudeVisionInterface()
    >>> result = vision.describe("/tmp/boot_screen.png")
    >>> print(result.text)
    """

    DESCRIBE_PROMPT = (
        "You are a technical diagnostics assistant. "
        "Describe this image in detail, focusing on any error messages, "
        "status indicators, icons, text on screen, and hardware components visible. "
        "Be precise and exhaustive."
    )
    OCR_PROMPT = (
        "Extract all text visible in this image exactly as it appears. "
        "Output only the raw text, preserving line breaks."
    )

    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        self.model = model
        self._client = None  # lazy-loaded

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic  # type: ignore
                self._client = anthropic.Anthropic()
            except ImportError as exc:
                raise RuntimeError(
                    "anthropic package is required: pip install anthropic"
                ) from exc
        return self._client

    def _call(self, image_path: str, prompt: str) -> VisionResult:
        client = self._get_client()
        b64    = self.load_image_b64(image_path)
        media  = self.infer_media_type(image_path)
        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
                        {"type": "text",  "text": prompt},
                    ],
                }],
            )
            text = message.content[0].text if message.content else ""
            return VisionResult(text=text, confidence=1.0, raw={"model": self.model})
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("ClaudeVisionInterface error: %s", exc)
            return VisionResult(error=str(exc))

    def describe(self, image_path: str) -> VisionResult:
        return self._call(image_path, self.DESCRIBE_PROMPT)

    def ocr(self, image_path: str) -> VisionResult:
        return self._call(image_path, self.OCR_PROMPT)
