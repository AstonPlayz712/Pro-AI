"""
gemini_vision.py — Google Gemini multimodal vision backend.

Used when only GOOGLE_API_KEY is set (no Anthropic/OpenAI keys).
Requires:  pip install google-generativeai
"""

from __future__ import annotations

import logging

from director.tools.vision.interface import VisionInterface, VisionResult

logger = logging.getLogger(__name__)


class GeminiVisionInterface(VisionInterface):
    """Vision backend backed by Google's Gemini multimodal models."""

    DESCRIBE_PROMPT = (
        "You are a technical diagnostics assistant. "
        "Describe this image in detail, focusing on error messages, status "
        "indicators, icons, text on screen, and visible hardware."
    )
    OCR_PROMPT = (
        "Extract all text visible in this image exactly as it appears. "
        "Output only the raw text, preserving line breaks."
    )

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro") -> None:
        self.api_key = api_key
        self.model   = model
        self._model_obj = None

    def _get_model(self):
        if self._model_obj is None:
            try:
                import google.generativeai as genai  # type: ignore
                genai.configure(api_key=self.api_key)
                self._model_obj = genai.GenerativeModel(self.model)
            except ImportError as exc:
                raise RuntimeError(
                    "google-generativeai is required: pip install google-generativeai"
                ) from exc
        return self._model_obj

    def _call(self, image_path: str, prompt: str) -> VisionResult:
        try:
            import PIL.Image  # type: ignore
            model = self._get_model()
            img = PIL.Image.open(image_path)
            resp = model.generate_content([prompt, img])
            text = (resp.text or "").strip()
            return VisionResult(text=text, confidence=1.0, raw={"model": self.model})
        except ImportError as exc:
            return VisionResult(error=f"Pillow required: {exc}")
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("GeminiVisionInterface error: %s", exc)
            return VisionResult(error=str(exc))

    def describe(self, image_path: str) -> VisionResult:
        return self._call(image_path, self.DESCRIBE_PROMPT)

    def ocr(self, image_path: str) -> VisionResult:
        return self._call(image_path, self.OCR_PROMPT)
