"""
dai.py — Director-AI (DAI): the top-level orchestrator.

Responsibilities
----------------
1. Accept a DAIRequest (text + optional images).
2. Run vision/OCR on any attached images to enrich the request context.
3. Route the enriched request to the correct specialist via the Router.
4. Collect the specialist's DAIResponse, attach metadata, and return it.
5. Fall back to a best-effort UNKNOWN response if no specialist matches.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from director.core.router import Router, build_default_router
from director.core.schema import (
    DAIRequest,
    DAIResponse,
    ProblemDomain,
    ConfidenceLevel,
)
from director.tools.vision.interface import VisionInterface, NullVisionInterface
from director.tools.web.interface import WebInterface, NullWebInterface
from src.backend.dai.system_prompt import DAI_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class DirectorAI:
    """
    Top-level orchestrator for the Pro-AI Director system.

    Parameters
    ----------
    router      : Router instance (defaults to the built-in route table).
    vision_tool : VisionInterface implementation for image analysis.
    web_tool    : WebInterface implementation for live web lookups.
    """

    def __init__(
        self,
        router:      Router | None       = None,
        vision_tool: VisionInterface | None = None,
        web_tool:    WebInterface | None    = None,
    ) -> None:
        self.router      = router      or build_default_router()
        self.vision_tool = vision_tool or NullVisionInterface()
        self.web_tool    = web_tool    or NullWebInterface()
        self.system_prompt: str = DAI_SYSTEM_PROMPT
        logger.info("DirectorAI initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle(self, request: DAIRequest) -> DAIResponse:
        """
        Process a DAIRequest end-to-end and return a DAIResponse.

        This is the single entry-point for all callers.
        """
        logger.info("DAI.handle — request_id=%s", request.request_id)
        start = time.perf_counter()

        try:
            # 1. Vision enrichment
            request = self._enrich_with_vision(request)

            # 2. Route to specialist
            specialist = self.router.route(request)

            # 3. Execute specialist or fall back
            if specialist is None:
                response = self._unknown_response(request)
            else:
                specialist.vision_tool = self.vision_tool
                specialist.web_tool    = self.web_tool
                response = specialist.run(request)

            response.timestamp = time.time()

        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("DAI.handle failed: %s", exc)
            response = self._error_response(request, str(exc))

        elapsed = time.perf_counter() - start
        logger.info(
            "DAI.handle complete — request_id=%s domain=%s elapsed=%.3fs",
            request.request_id, response.domain, elapsed,
        )
        return response

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _enrich_with_vision(self, request: DAIRequest) -> DAIRequest:
        """Run vision/OCR on each attached image and append text to context."""
        if not request.image_paths:
            return request

        vision_texts: list[str] = []
        for path in request.image_paths:
            try:
                result = self.vision_tool.describe(path)
                if result.text:
                    vision_texts.append(result.text)
                    logger.debug("Vision OCR — path=%s chars=%d", path, len(result.text))
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Vision failed for %s: %s", path, exc)

        if vision_texts:
            combined = "\n".join(vision_texts)
            request.context["vision_text"] = combined
            # Also inject into raw_text so the router can score it
            request.raw_text = (request.raw_text + "\n" + combined).strip()

        return request

    @staticmethod
    def _unknown_response(request: DAIRequest) -> DAIResponse:
        return DAIResponse(
            request_id=request.request_id,
            domain=ProblemDomain.UNKNOWN,
            confidence=0.0,
            confidence_lvl=ConfidenceLevel.LOW,
            summary="No matching specialist found for the given request.",
            actions=["Provide more details about the problem domain."],
        )

    @staticmethod
    def _error_response(request: DAIRequest, error: str) -> DAIResponse:
        return DAIResponse(
            request_id=request.request_id,
            domain=ProblemDomain.UNKNOWN,
            confidence=0.0,
            confidence_lvl=ConfidenceLevel.LOW,
            summary="An internal error occurred during processing.",
            error=error,
        )


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def create_dai(**overrides: Any) -> DirectorAI:
    """
    Create a fully-configured DirectorAI.

    Loads config from environment (via core.config.get_config), picks the
    best available vision and web backends based on credentials present,
    and constructs the DAI with them.

    Any keyword argument (router, vision_tool, web_tool) overrides the
    auto-selected default.
    """
    try:
        from core.config import create_vision_tool, create_web_tool
        defaults: dict[str, Any] = {
            "vision_tool": create_vision_tool(),
            "web_tool":    create_web_tool(),
        }
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("create_dai: config load failed (%s); using Null tools.", exc)
        defaults = {}

    defaults.update(overrides)
    return DirectorAI(**defaults)
