"""
openai_vision.py — OpenAI GPT-4V / GPT-4o Vision backend.

Used as a fallback when ANTHROPIC_API_KEY is not set but OPENAI_API_KEY is.
Requires:  pip install openai
"""

from __future__ import annotations

import logging

from director.tools.vision.interface import VisionInterface, VisionResult

logger = logging.getLogger(__name__)


class OpenAIVisionInterface(VisionInterface):
    """Vision backend backed by OpenAI's vision-capable chat models."""

    DESCRIBE_PROMPT = (
        "You are a technical diagnostics assistant. "
        "Describe this image in detail, focusing on error messages, status "
        "indicators, icons, text on screen, and visible hardware."
    )
    OCR_PROMPT = (
        "Extract all text visible in this image exactly as it appears. "
        "Output only the raw text, preserving line breaks."
    )

    def __init__(self, model: str = "gpt-4o") -> None:
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI  # type: ignore
                self._client = OpenAI()
            except ImportError as exc:
                raise RuntimeError(
                    "openai package is required: pip install openai"
                ) from exc
        return self._client

    def _call(self, image_path: str, prompt: str) -> VisionResult:
        client = self._get_client()
        b64    = self.load_image_b64(image_path)
        media  = self.infer_media_type(image_path)
        try:
            resp = client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url",
                         "image_url": {"url": f"data:{media};base64,{b64}"}},
                    ],
                }],
            )
            text = resp.choices[0].message.content or ""
            return VisionResult(text=text, confidence=1.0, raw={"model": self.model})
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("OpenAIVisionInterface error: %s", exc)
            return VisionResult(error=str(exc))

    def describe(self, image_path: str) -> VisionResult:
        return self._call(image_path, self.DESCRIBE_PROMPT)

    def ocr(self, image_path: str) -> VisionResult:
        return self._call(image_path, self.OCR_PROMPT)
